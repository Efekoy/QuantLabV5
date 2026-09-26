"""Paired structure-preserving zero-direction worlds from unsigned nuisance tape.

The tape contains no absolute historical return sign. Every generated bar gets
a fresh symmetric sign, with only same-minute NQ/ES coupling. No future value
is consulted in sign generation. V5 strategy definitions are not imported.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from quantlab5.data.schema import bars_from_arrays
from quantlab5.data.sessions import day_to_date, session_fields
from quantlab5.util.hashing import file_sha256

MODES = ("paired_sign", "paired_day_resample", "state_conditioned_sign")
FIELDS = ("gap_ticks", "body_ticks", "up_wick_ticks", "down_wick_ticks",
          "volume", "gap_body_relation")


class PairedNuisanceNull:
    def __init__(self, artifact_path: Path, tape_path: Path, mode: str):
        if mode not in MODES:
            raise ValueError("unfrozen V5.1 null mode")
        self.mode = mode
        self.artifact = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
        if self.artifact.get("kind") != "V5_1_DISCOVERY_NUISANCE_CALIBRATION":
            raise ValueError("invalid V5.1 nuisance artifact")
        if file_sha256(tape_path) != self.artifact["tape_sha256"]:
            raise ValueError("V5.1 nuisance tape hash mismatch")
        with np.load(tape_path, allow_pickle=False) as f:
            self.tape = {k: f[k].copy() for k in f.files}

    def generate(self, source: dict, seed: int):
        if set(source) != {"NQ", "ES"}:
            raise ValueError("V5.1 null requires NQ and ES")
        return self.generate_seed(seed)

    @staticmethod
    def _donor_days(tape: dict, rng: np.random.Generator) -> dict[int, int]:
        days = np.unique(np.r_[session_fields(tape["nq_ts"])[2],
                               session_fields(tape["es_ts"])[2]])
        months: dict[tuple[int, int], list[int]] = {}
        for day in days:
            d = day_to_date(int(day))
            months.setdefault((d.year, d.month), []).append(int(day))
        return {day: donor for pool in months.values()
                for day, donor in zip(pool, rng.permutation(pool))}

    def _source_index(self, prefix: str, donors: dict[int, int] | None) -> np.ndarray:
        ts = self.tape[f"{prefix}_ts"]
        if donors is None:
            return np.arange(len(ts))
        _, _, day, sm = session_fields(ts)
        key = day.astype(np.int64)*1440 + sm.astype(np.int64)
        unique_days, inverse = np.unique(day, return_inverse=True)
        donor = np.array([donors[int(d)] for d in unique_days], np.int64)[inverse]
        requested = donor*1440 + sm
        ix = np.searchsorted(key, requested)
        ok = ix < len(key)
        ok[ok] &= key[ix[ok]] == requested[ok]
        return np.where(ok, ix, np.arange(len(ts)))

    def generate_seed(self, seed: int):
        rng = np.random.default_rng(int(seed))
        donors = self._donor_days(self.tape, rng) if self.mode == "paired_day_resample" else None
        a = {}
        for inst, prefix in (("NQ", "nq"), ("ES", "es")):
            ts = self.tape[f"{prefix}_ts"]
            seg = self.tape[f"{prefix}_segment"]
            ix = self._source_index(prefix, donors)
            a[inst] = {"ts": ts, "seg": seg,
                       **{name: self.tape[f"{prefix}_{name}"][ix] for name in FIELDS}}
        # Independent timewise direction; only same-minute cross-market signs
        # are coupled. No real sign vector is stored or read here.
        signs = {inst: np.where(rng.random(len(a[inst]["ts"])) < .5, -1, 1).astype(np.int8)
                 for inst in ("NQ", "ES")}
        nq, es = a["NQ"], a["ES"]
        pos = np.searchsorted(nq["ts"], es["ts"])
        matched = pos < len(nq["ts"])
        matched[matched] &= nq["ts"][pos[matched]] == es["ts"][matched]
        ei = np.flatnonzero(matched)
        ni = pos[ei]
        if self.mode == "state_conditioned_sign":
            joint = self.artifact["joint_sign"]
            magnitude = np.log1p(nq["body_ticks"][ni].astype(float)
                                 + es["body_ticks"][ei].astype(float))
            bucket = np.searchsorted(joint["joint_magnitude_quartile_cuts"], magnitude,
                                     side="right")
            probability = np.asarray(joint["same_sign_by_joint_magnitude_quartile"])[bucket]
        else:
            probability = self.artifact["joint_sign"]["same_sign_fraction"]
        signs["ES"][ei] = signs["NQ"][ni] * np.where(rng.random(len(ei)) < probability, 1, -1)
        out = {}
        for inst in ("NQ", "ES"):
            x = a[inst]
            n = len(x["ts"])
            body_sign = signs[inst]
            relation = x["gap_body_relation"].astype(np.int8)
            independent_gap_sign = np.where(rng.random(n) < .5, -1, 1)
            gap_sign = np.where(relation != 0, relation*body_sign, independent_gap_sign)
            gap = gap_sign*x["gap_ticks"].astype(float)*.25
            body = body_sign*x["body_ticks"].astype(float)*.25
            change = gap + body
            cumulative = np.cumsum(change)
            median_price = float(self.artifact["median_price"][inst])
            base = np.rint((median_price-np.median(cumulative))/.25)*.25
            close = base + cumulative
            open_ = close-body
            if np.min(open_) <= 0:
                raise ValueError("V5.1 zero-edge price path crossed zero")
            flip = rng.random(n) < .5
            up = np.where(flip, x["down_wick_ticks"], x["up_wick_ticks"]).astype(float)*.25
            down = np.where(flip, x["up_wick_ticks"], x["down_wick_ticks"]).astype(float)*.25
            high = np.maximum(open_, close) + up
            low = np.minimum(open_, close) - down
            if np.min(low) <= 0:
                raise ValueError("V5.1 zero-edge low crossed zero")
            symbols = np.char.add(inst+"S", x["seg"].astype(str))
            out[inst] = bars_from_arrays(inst, x["ts"], open_, high, low, close,
                                         x["volume"], symbols,
                                         source=f"v5.1:null:{self.mode}:{seed}")
        return out
