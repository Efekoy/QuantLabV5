"""Mechanical V5.2 range diagnosis from permitted unsigned tape and null worlds.

This does not inspect any real strategy outcome and does not change a gate.
"""
from __future__ import annotations

import json
import numpy as np

from quantlab5.project import ROOT
from quantlab5.v5_2.positive_null import PositivePairedNull

READS_MARKET_DATA = False
OUT = ROOT / "reports/V5_3_RANGE_DIAGNOSIS.json"


def vector(real: np.ndarray, generated: np.ndarray, sm: np.ndarray) -> list[dict]:
    order = np.argsort(sm, kind="stable")
    sorted_sm, r, g = sm[order], real[order], generated[order]
    bounds = np.searchsorted(sorted_sm, np.arange(1441))
    rows = []
    for clock in range(1440):
        a, z = bounds[clock], bounds[clock+1]
        if z-a < 100:
            continue
        for q in (.5, .9):
            target, actual = float(np.quantile(r[a:z], q)), float(np.quantile(g[a:z], q))
            error = max(abs(actual-target)-.25, 0)/max(target, .25)
            rows.append({"session_minute": clock, "quantile": q, "count": int(z-a),
                         "target_points": target, "generated_points": actual,
                         "signed_relative_difference": (actual-target)/max(target, .25),
                         "frozen_error_after_one_tick": float(error)})
    return rows


def main() -> None:
    if OUT.exists():
        raise RuntimeError("range diagnosis already exists")
    gen = PositivePairedNull(ROOT / "V5_1_DISCOVERY_NUISANCE_CALIBRATION.json",
                             ROOT / "reports/V5_1_NUISANCE_TAPE.npz")
    result = {"kind": "V5_3_V5_2_RANGE_MECHANICS_DIAGNOSIS",
              "source": "archived V5.2 positive-price generator and V5.1 unsigned tape",
              "seeds": {}}
    for seed in (9101, 9102, 9103):
        bars = gen.generate_seed(seed)
        per_inst = {}
        for inst, prefix in (("NQ", "nq"), ("ES", "es")):
            b = bars[inst]
            tape = gen.tape
            target = (tape[f"{prefix}_body_ticks"].astype(float)
                      + tape[f"{prefix}_up_wick_ticks"].astype(float)
                      + tape[f"{prefix}_down_wick_ticks"].astype(float))*.25
            observed = np.asarray(b.h)-np.asarray(b.l)
            rows = vector(target, observed, np.asarray(b.sm))
            per_inst[inst] = {"complete_clock_quantile_vector": rows,
                              "max_frozen_error": max(x["frozen_error_after_one_tick"] for x in rows),
                              "cells_over_0p25": sum(x["frozen_error_after_one_tick"] > .25 for x in rows),
                              "median_signed_relative_difference": float(np.median(
                                  [x["signed_relative_difference"] for x in rows]))}
        result["seeds"][str(seed)] = per_inst
    OUT.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
