"""Zero-direction market worlds from pinned DISCOVERY nuisance summaries.

Only the calendar/segment template and unconditional magnitudes enter this
generator. Direction is redrawn independently across minutes, with a symmetric
joint NQ/ES sign law. This generator never loads actual price or return paths.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from numba import njit

from quantlab5.data.schema import Bars, bars_from_arrays
from quantlab5.data.sessions import session_fields
from quantlab5.util.hashing import file_sha256


@njit(cache=True)
def _ar_state(noise, day, segment, rho):
    out = np.empty(len(noise))
    gain = np.sqrt(max(0.0, 1.0-rho*rho))
    prior = 0.0
    for i in range(len(noise)):
        if i == 0 or day[i] != day[i-1] or segment[i] != segment[i-1]:
            prior = noise[i]
        else:
            prior = rho*prior + gain*noise[i]
        out[i] = prior
    return out


def _lognormal_profile(profile: dict, sm: np.ndarray, z: np.ndarray,
                       rng: np.random.Generator, tick: float, *, integer: bool = False) -> np.ndarray:
    med = np.asarray(profile["median"], float)[sm]
    p90 = np.asarray(profile["p90"], float)[sm]
    zero = np.asarray(profile["zero_fraction"], float)[sm]
    floor = 1.0 if integer else tick
    sigma = np.log(np.maximum(p90, floor) / np.maximum(med, floor)) / 1.2815515655446004
    values = np.exp(np.log(np.maximum(med, floor)) + sigma*z)
    values[rng.random(len(values)) < zero] = 0
    if integer:
        return np.rint(values).astype(np.int64)
    return np.rint(values/tick)*tick


def _gap_magnitudes(quantiles: list[float], count: int, rng: np.random.Generator,
                    tick: float) -> np.ndarray:
    q = np.interp(rng.random(count), [0, .5, .9, .99, 1], quantiles)
    return np.rint(q/tick)*tick


class CalibratedZeroEdgeWorlds:
    name = "v5_discovery_nuisance_symmetric_zero_edge"

    def __init__(self, artifact_path: Path, template_path: Path):
        doc = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
        if doc.get("kind") != "V5_DISCOVERY_NUISANCE_CALIBRATION" or doc.get("status") != "COMPLETE":
            raise ValueError("nuisance calibration artifact is not complete")
        if file_sha256(template_path) != doc.get("calendar_template_sha256"):
            raise ValueError("calendar template hash mismatch")
        with np.load(template_path, allow_pickle=False) as f:
            self.template = {k: f[k].copy() for k in ("nq_ts", "nq_segment", "es_ts", "es_segment")}
        self.doc = doc

    def generate(self, source: dict[str, Bars], seed: int) -> dict[str, Bars]:
        """NullGenerator-compatible call; source bars are intentionally unused."""
        if set(source) != {"NQ", "ES"}:
            raise ValueError("expected NQ/ES source mapping")
        return self.generate_seed(seed)

    def generate_seed(self, seed: int) -> dict[str, Bars]:
        rng = np.random.default_rng(int(seed))
        arrays = {}
        signs = {}
        abs_noise = {}
        # Independent zero-body draws and tick rounding attenuate observed
        # magnitude correlation relative to latent Gaussian correlation.
        rho_abs = float(np.clip(1.45*self.doc["joint"]["abs_body_log_correlation"],
                                -0.995, 0.995))
        p_same = float(self.doc["joint"]["same_sign_fraction"])
        if not 0 <= p_same <= 1:
            raise ValueError("invalid joint sign calibration")
        for inst, prefix in (("NQ", "nq"), ("ES", "es")):
            ts = self.template[f"{prefix}_ts"]
            seg = self.template[f"{prefix}_segment"]
            if len(ts) != len(seg) or not len(ts) or np.any(ts[1:] <= ts[:-1]):
                raise ValueError("invalid calibrated calendar template")
            _, _, day, sm = session_fields(ts)
            sm = np.asarray(sm, int)
            summary = self.doc[inst]
            rho_body = float(np.clip(summary["abs_body_log_lag_correlation"]["1"], 0, .95))
            rho_volume = float(np.clip(summary["volume_log_lag_correlation"]["1"], 0, .95))
            base_noise = rng.standard_normal(len(ts))
            abs_noise[inst] = _ar_state(base_noise, day, seg, rho_body)
            volume_noise = _ar_state(rng.standard_normal(len(ts)), day, seg, rho_volume)
            tick = .25
            body = _lognormal_profile(summary["body_abs_points_by_clock"], sm,
                                      abs_noise[inst], rng, tick)
            range_target = _lognormal_profile(summary["range_points_by_clock"], sm,
                                               abs_noise[inst], rng, tick)
            volume = _lognormal_profile(summary["volume_by_clock"], sm,
                                        volume_noise, rng, tick, integer=True)
            signs[inst] = np.where(rng.random(len(ts)) < .5, -1.0, 1.0)
            arrays[inst] = {"ts": ts, "seg": seg, "day": day, "body": body,
                            "range_target": range_target, "volume": volume, "median_price": summary["median_price"],
                            "gap_quantiles": summary["absolute_gap_points_quantiles"]}
        # Couple ES magnitudes and signs at exactly matched minutes, preserving
        # contemporaneous nuisance dependence without retaining real directions.
        nq, es = arrays["NQ"], arrays["ES"]
        pos = np.searchsorted(nq["ts"], es["ts"])
        matched = pos < len(nq["ts"])
        matched[matched] &= nq["ts"][pos[matched]] == es["ts"][matched]
        es_ix = np.flatnonzero(matched)
        if len(es_ix):
            n_ix = pos[es_ix]
            coupled = rho_abs*abs_noise["NQ"][n_ix] + np.sqrt(1-rho_abs*rho_abs)*abs_noise["ES"][es_ix]
            _, _, _, es_sm = session_fields(es["ts"])
            es["body"][es_ix] = _lognormal_profile(
                self.doc["ES"]["body_abs_points_by_clock"], np.asarray(es_sm, int)[es_ix],
                coupled, rng, .25)
            agree = rng.random(len(es_ix)) < p_same
            signs["ES"][es_ix] = signs["NQ"][n_ix] * np.where(agree, 1.0, -1.0)
        out = {}
        for inst in ("NQ", "ES"):
            a = arrays[inst]
            n = len(a["ts"])
            boundary = np.r_[True, (a["day"][1:] != a["day"][:-1])
                             | (a["seg"][1:] != a["seg"][:-1])]
            gap = np.zeros(n)
            gap[boundary] = _gap_magnitudes(a["gap_quantiles"], int(boundary.sum()), rng, .25)
            gap *= np.where(rng.random(n) < .5, -1.0, 1.0)
            changes = signs[inst]*a["body"] + gap
            base_price = np.rint(a["median_price"]/.25)*.25
            close = base_price + np.cumsum(changes)
            open_ = close - signs[inst]*a["body"]
            extra_ticks = np.maximum(np.rint((a["range_target"]-a["body"])/.25).astype(int), 0)
            up_ticks = rng.binomial(extra_ticks, .5)
            high = np.maximum(open_, close) + up_ticks*.25
            low = np.minimum(open_, close) - (extra_ticks-up_ticks)*.25
            if np.min(low) <= 0:
                raise ValueError("zero-edge path crossed nonpositive prices")
            symbols = np.char.add(inst + "S", a["seg"].astype(str))
            out[inst] = bars_from_arrays(inst, a["ts"], open_, high, low, close,
                                         a["volume"], symbols,
                                         source=f"null:{self.name}:{seed}")
        return out
