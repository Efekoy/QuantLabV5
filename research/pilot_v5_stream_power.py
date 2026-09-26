"""Pilot conditional power through V5 fixed-family bootstrap, synthetic only.

Not a final calibration: adaptive feature generation and full market replay are
absent. Results cannot authorize real discovery or a preregistration freeze.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from quantlab5.v5.inference import fixed_family_inference
from quantlab5.v5.synthetic_streams import dependent_panel, plant

EFFECTS = (0, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15)


def run(replications: int, bootstrap_reps: int, frequencies: tuple[int, ...],
        days: int, candidates: int, seed: int) -> dict:
    out = {"kind": "conditional_stream_pilot", "days": days, "candidates": candidates,
           "replications": replications, "bootstrap_reps": bootstrap_reps,
           "frequencies": list(frequencies), "effects_R": list(EFFECTS),
           "warning": "Not full-market or adaptive A/B/C power; cannot authorize discovery.",
           "results": {}}
    for f in frequencies:
        detections = {str(e): 0 for e in EFFECTS}
        family_detections = {str(e): 0 for e in EFFECTS}
        for i in range(replications):
            panel, counts = dependent_panel(days, f, candidates, seed + f * 100000 + i)
            for e in EFFECTS:
                x = plant(panel, counts, e)
                res = fixed_family_inference(x, reps=bootstrap_reps, seed=seed + f * 10000000 + i)
                detections[str(e)] += int(res.adjusted_p[0] <= 0.05)
                family_detections[str(e)] += int(res.global_p <= 0.05)
        out["results"][str(f)] = {
            "exact_spec_detection": {e: detections[e] / replications for e in detections},
            "any_family_detection": {e: family_detections[e] / replications for e in family_detections},
        }
        print(f"finished {f} trades/year", flush=True)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--replications", type=int, default=100)
    p.add_argument("--bootstrap-reps", type=int, default=99)
    p.add_argument("--frequencies", type=int, nargs="+", default=[100, 500])
    p.add_argument("--days", type=int, default=1034)
    p.add_argument("--candidates", type=int, default=120)
    p.add_argument("--seed", type=int, default=20260925)
    p.add_argument("--output", type=Path, default=Path("reports/V5_STREAM_POWER_PILOT.json"))
    args = p.parse_args()
    result = run(args.replications, args.bootstrap_reps, tuple(args.frequencies),
                 args.days, args.candidates, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(args.output)
