"""Fresh synthetic-stream calibration of max versus top-two family evidence.

This is deliberately NOT a market-level adaptive-search calibration. Independent
null panels set the cutoffs, different null panels check size, and fresh planted
panels estimate family detection. No real partition is loaded.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import beta

from quantlab5.v5.holdout import family_statistic
from quantlab5.v5.synthetic_streams import structured_panel

METHODS = ("max", "top2")
SHAPES = ("needle", "plateau", "family", "regime")
EDGES = (0.0, .05, .075, .10, .15)


def _interval(k: int, n: int) -> list[float]:
    return [0.0 if k == 0 else float(beta.ppf(.025, k, n-k+1)),
            1.0 if k == n else float(beta.ppf(.975, k+1, n-k))]


def _stats(x: np.ndarray) -> dict[str, np.ndarray]:
    return {method: family_statistic(x, method) for method in METHODS}


def calibrate(*, days: int, frequency: int, calibration_worlds: int,
              verification_worlds: int, plant_worlds: int, seed: int) -> dict:
    if min(days, frequency, calibration_worlds, verification_worlds, plant_worlds) < 1:
        raise ValueError("all dimensions must be positive")
    maxima = {m: [] for m in METHODS}
    for i in range(calibration_worlds):
        p = structured_panel(days, frequency, seed + i)
        stat = _stats(p.daily)
        for m in METHODS:
            maxima[m].append(float(np.max(stat[m])))
    # At most floor(.05*(B+1)) calibration null exceedances, with a +1
    # empirical p convention. A statistic equal to the cutoff does not pass.
    rank = max(0, min(calibration_worlds - 1,
                      int(np.ceil(.95 * (calibration_worlds + 1))) - 1))
    cutoff = {m: float(np.sort(maxima[m])[rank]) for m in METHODS}
    false = {m: 0 for m in METHODS}
    for i in range(verification_worlds):
        p = structured_panel(days, frequency, seed + 100_000 + i)
        stat = _stats(p.daily)
        for m in METHODS:
            false[m] += bool(np.max(stat[m]) > cutoff[m])
    power = {shape: {str(e): {m: 0 for m in METHODS} for e in EDGES} for shape in SHAPES}
    for shape_idx, shape in enumerate(SHAPES):
        for i in range(plant_worlds):
            p = structured_panel(days, frequency, seed + 200_000 + shape_idx * 10_000 + i)
            for edge in EDGES:
                x, _ = p.planted(shape, edge)
                stat = _stats(x)
                for m in METHODS:
                    power[shape][str(edge)][m] += bool(stat[m][0] > cutoff[m])
    return {
        "status": "SYNTHETIC_STREAM_ONLY_NOT_ADAPTIVE_MARKET_REPLAY",
        "days": days, "frequency": frequency,
        "calibration_worlds": calibration_worlds,
        "verification_worlds": verification_worlds,
        "plant_worlds_per_shape": plant_worlds, "seed": seed,
        "family_count": 30, "rules_per_family": 4,
        "cutoff": cutoff,
        "verification_global_false_positive": {
            m: {"count": false[m], "rate": false[m] / verification_worlds,
                "ci95": _interval(false[m], verification_worlds)} for m in METHODS},
        "target_family_detection": {
            shape: {edge: {m: {"count": counts[m], "rate": counts[m] / plant_worlds,
                              "ci95": _interval(counts[m], plant_worlds)}
                           for m in METHODS} for edge, counts in by_edge.items()}
            for shape, by_edge in power.items()},
    }


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--days", type=int, default=900)
    a.add_argument("--frequency", type=int, default=500)
    a.add_argument("--calibration-worlds", type=int, default=200)
    a.add_argument("--verification-worlds", type=int, default=200)
    a.add_argument("--plant-worlds", type=int, default=100)
    a.add_argument("--seed", type=int, default=54124)
    a.add_argument("--out", type=Path, default=Path("reports/V5_TOP_TWO_FAMILY_PILOT.json"))
    ns = a.parse_args()
    out = calibrate(days=ns.days, frequency=ns.frequency,
                    calibration_worlds=ns.calibration_worlds,
                    verification_worlds=ns.verification_worlds,
                    plant_worlds=ns.plant_worlds, seed=ns.seed)
    ns.out.parent.mkdir(parents=True, exist_ok=True)
    ns.out.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(ns.out)
    print(json.dumps({"cutoff": out["cutoff"],
                      "verification_global_false_positive": out["verification_global_false_positive"]}, indent=2))


if __name__ == "__main__":
    main()
