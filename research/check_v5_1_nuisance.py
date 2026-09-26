"""Frozen V5.1 nuisance-fidelity and general zero-direction diagnostics."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from quantlab5.data.sessions import session_fields
from quantlab5.project import ROOT
from quantlab5.v5_1.paired_null import MODES, PairedNuisanceNull

READS_MARKET_DATA = False
ARTIFACT = ROOT / "V5_1_DISCOVERY_NUISANCE_CALIBRATION.json"
TAPE = ROOT / "reports/V5_1_NUISANCE_TAPE.npz"
OUT = ROOT / "reports/V5_1_NUISANCE_MODEL_FIT.json"
SEEDS = (9101, 9102, 9103)


def _corr(x, y) -> float:
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def _lag(x, day, seg, k: int) -> float:
    good = (day[k:] == day[:-k]) & (seg[k:] == seg[:-k])
    return _corr(x[k:][good], x[:-k][good])


def _clock_error(real, generated, order, bounds, *, tick: float) -> tuple[float, float]:
    worst = 0.0
    zero_error = 0.0
    sorted_real, sorted_generated = real[order], generated[order]
    for clock in range(1440):
        a, z = bounds[clock], bounds[clock+1]
        r = sorted_real[a:z]
        g = sorted_generated[a:z]
        if len(r) < 100:
            continue
        for q in (.5, .9):
            target, actual = np.quantile(r, q), np.quantile(g, q)
            worst = max(worst, max(abs(actual-target)-tick, 0)
                        / max(abs(target), tick if tick > 0 else 1.0))
        zero_error = max(zero_error, abs(np.mean(r == 0)-np.mean(g == 0)))
    return float(worst), float(zero_error)


def _rolling30(x):
    x = np.asarray(x, float)
    cumulative = np.r_[0.0, np.cumsum(x)]
    a = (cumulative[30:]-cumulative[:-30])/30
    return np.r_[np.full(29, np.nan), a]


def diagnose(generator: PairedNuisanceNull, seed: int) -> dict:
    tape = generator.tape
    bars = generator.generate_seed(seed)
    measured = {}
    local = {}
    for inst, prefix in (("NQ", "nq"), ("ES", "es")):
        b = bars[inst]
        ts = tape[f"{prefix}_ts"]
        seg = tape[f"{prefix}_segment"]
        exact = bool(np.array_equal(b.ts, ts) and np.array_equal(b.seg, seg-seg[0]))
        _, _, day, sm = session_fields(ts)
        order = np.argsort(sm, kind="stable")
        bounds = np.searchsorted(sm[order], np.arange(1441))
        rb = tape[f"{prefix}_body_ticks"].astype(float)*.25
        rg = tape[f"{prefix}_gap_ticks"].astype(float)*.25
        rr = rb + (tape[f"{prefix}_up_wick_ticks"]
                   + tape[f"{prefix}_down_wick_ticks"]).astype(float)*.25
        rv = tape[f"{prefix}_volume"].astype(float)
        relation = tape[f"{prefix}_gap_body_relation"]
        rcc = np.where(relation == 1, rg+rb, np.abs(rg-rb))
        gb = np.abs(np.asarray(b.c)-np.asarray(b.o))
        gg = np.abs(np.asarray(b.o)-np.r_[b.o[0], b.c[:-1]])
        gr = np.asarray(b.h)-np.asarray(b.l)
        gv = np.asarray(b.v)
        gcc = np.abs(np.asarray(b.c)-np.r_[b.o[0], b.c[:-1]])
        quantile = {}
        zero = {}
        for name, r, g, tick in (("body", rb, gb, .25), ("range", rr, gr, .25),
                                 ("volume", rv, gv, 0), ("gap", rg, gg, .25),
                                 ("close_close", rcc, gcc, .25)):
            quantile[name], zero[name] = _clock_error(r, g, order, bounds, tick=tick)
        lag_errors = {}
        for name, r, g in (("body", rb, gb), ("volume", rv, gv)):
            for lag in (1, 5, 30):
                lag_errors[f"{name}_{lag}"] = abs(_lag(np.log1p(r), day, seg, lag)
                                                   - _lag(np.log1p(g), day, seg, lag))
        body_sign = np.sign(np.asarray(b.c)-np.asarray(b.o))
        nonzero = body_sign != 0
        directional = {f"sign_autocorr_{lag}": abs(_lag(body_sign, day, seg, lag))
                       for lag in (1, 2, 5, 30)}
        directional["sign_bias"] = float(abs(np.mean(body_sign[nonzero])))
        for name, state in (("prior_body", rb), ("prior_volume", rv)):
            cutoff = np.median(state)
            for label, mask in (("low", state[:-1] <= cutoff),
                                ("high", state[:-1] > cutoff)):
                valid = mask & (day[:-1] == day[1:]) & (seg[:-1] == seg[1:])
                directional[f"next_sign_given_{name}_{label}"] = float(abs(np.mean(body_sign[1:][valid])))
        measured[inst] = {"calendar_roll_exact": exact, "quantile_error": quantile,
                          "zero_fraction_error": zero, "lag_error": lag_errors,
                          "directional": directional,
                          "median_price_relative_error": float(abs(np.median(b.c)
                              - generator.artifact["median_price"][inst])
                              / generator.artifact["median_price"][inst])}
        local[inst] = {"ts": ts, "sm": sm, "body_real": rb, "body_gen": gb,
                       "range_real": rr, "range_gen": gr,
                       "volume_real": rv, "volume_gen": gv,
                       "cc_real": rcc, "cc_gen": gcc, "sign": body_sign}
    n, e = local["NQ"], local["ES"]
    pos = np.searchsorted(e["ts"], n["ts"])
    valid = pos < len(e["ts"])
    valid[valid] &= e["ts"][pos[valid]] == n["ts"][valid]
    ni = np.flatnonzero(valid)
    ei = pos[ni]
    joint = {}
    for name in ("body", "range", "volume", "cc"):
        nr, ng = n[f"{name}_real"], n[f"{name}_gen"]
        er, eg = e[f"{name}_real"], e[f"{name}_gen"]
        transform = np.log1p
        joint[name] = abs(_corr(transform(nr[ni]), transform(er[ei]))
                          - _corr(transform(ng[ni]), transform(eg[ei])))
        if name in ("body", "range", "volume"):
            for label, mask in (("rth", (n["sm"][ni] >= 930) & (n["sm"][ni] <= 1320)),
                                ("non_rth", (n["sm"][ni] < 930) | (n["sm"][ni] > 1320))):
                joint[f"{name}_{label}"] = abs(
                    _corr(transform(nr[ni[mask]]), transform(er[ei[mask]]))
                    - _corr(transform(ng[ni[mask]]), transform(eg[ei[mask]])))
    nr, ng = _rolling30(n["body_real"]), _rolling30(n["body_gen"])
    er, eg = _rolling30(e["body_real"]), _rolling30(e["body_gen"])
    rolling_ok = (ni >= 29) & (ei >= 29)
    joint["volatility_state_30"] = abs(_corr(nr[ni[rolling_ok]], er[ei[rolling_ok]])
                                       - _corr(ng[ni[rolling_ok]], eg[ei[rolling_ok]]))
    nonzero = (n["sign"][ni] != 0) & (e["sign"][ei] != 0)
    same = np.mean(n["sign"][ni[nonzero]] == e["sign"][ei[nonzero]])
    sign_error = abs(same-generator.artifact["joint_sign"]["same_sign_fraction"])
    directional_cross = abs(_corr(n["sign"][ni[:-1]], e["sign"][ei[1:]]))
    passed_nuisance = (all(x["calendar_roll_exact"]
                           and max(x["quantile_error"].values()) <= .25
                           and max(x["zero_fraction_error"].values()) <= .02
                           and max(x["lag_error"].values()) <= .10
                           and x["median_price_relative_error"] <= .20
                           for x in measured.values())
                       and max(joint.values()) <= .10 and sign_error <= .05)
    edge_max = max(directional_cross, *(max(x["directional"].values())
                                          for x in measured.values()))
    return {"seed": seed, "mode": generator.mode, "instruments": measured,
            "joint_nuisance_error": joint, "joint_sign_agreement_error": float(sign_error),
            "cross_lag_directional_error": float(directional_cross),
            "max_zero_edge_diagnostic": float(edge_max),
            "nuisance_pass": bool(passed_nuisance),
            "zero_edge_pass": bool(edge_max <= .01),
            "pass": bool(passed_nuisance and edge_max <= .01)}


def main() -> None:
    from quantlab5.v5_1.access import STATE, freeze_ready
    from quantlab5.util.hashing import file_sha256
    ok, reason = freeze_ready()
    if not ok:
        raise RuntimeError(reason)
    state = json.loads(STATE.read_text(encoding="utf-8"))
    if state["state"] != "COMPLETE":
        raise RuntimeError("V5.1 calibration worker has not closed")
    result = {}
    for mode in MODES:
        generator = PairedNuisanceNull(ARTIFACT, TAPE, mode)
        rows = []
        for seed in SEEDS:
            try:
                rows.append(diagnose(generator, seed))
            except (ValueError, FloatingPointError, OverflowError) as exc:
                rows.append({"mode": mode, "seed": seed, "pass": False,
                             "generation_error": str(exc)})
        result[mode] = rows
    passing = [mode for mode in MODES if all(x["pass"] for x in result[mode])]
    selected = passing[0] if passing else None
    report = {"kind": "V5_1_FROZEN_NUISANCE_FIDELITY",
              "protocol_freeze_sha256": file_sha256(ROOT / "V5_1_NUISANCE_PROTOCOL_FREEZE.json"),
              "artifact_sha256": file_sha256(ARTIFACT),
              "mode_priority": list(MODES), "modes": result,
              "selected_mode": selected,
              "status": "PASS" if selected else "FAIL_NUISANCE_FIDELITY"}
    OUT.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if selected is None:
        raise SystemExit("V5.1 frozen nuisance fidelity failed; stop before power calibration")


if __name__ == "__main__":
    main()
