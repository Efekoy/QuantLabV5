"""Synthetic fixed-library power decomposition with shared neighboring events.

This is *not* market-level A/B/C replay. It answers where fixed-library power is
lost and how a family statistic responds to four planted-edge shapes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from quantlab5.v5.hierarchy import evaluate_shape_effects
from quantlab5.v5.synthetic_streams import SHAPES, structured_panel

EFFECTS = (0, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15)
LEVELS = ("single_hac", "single_bootstrap", "unadjusted_120", "holm_120",
          "stepdown_120", "global", "family", "neighborhood", "naive_event")


def hits(r) -> dict[str, bool]:
    return {
        "single_hac": r.single_hac_p <= 0.05,
        "single_bootstrap": r.single_bootstrap_p <= 0.05,
        "unadjusted_120": r.unadjusted_joint_p <= 0.05,
        "holm_120": r.holm_p <= 0.05,
        "stepdown_120": r.stepdown_p <= 0.05,
        "global": r.global_p <= 0.05,
        "family": r.family_supported,
        "neighborhood": r.neighborhood_supported,
        "naive_event": r.naive_event_p <= 0.05,
    }


def mde_bracket(rates: dict[str, float], target: float) -> str:
    prev = None
    for e in EFFECTS[1:]:
        if rates[str(e)] >= target:
            return f"({prev}R,{e}R]" if prev is not None else f"<= {e}R"
        prev = e
    return f"> {EFFECTS[-1]}R"


def run(frequencies: tuple[int, ...], worlds: int, bootstrap_reps: int,
        output: Path, seed: int = 20260925) -> dict:
    report = {
        "kind": "fixed_library_hierarchical_synthetic_calibration",
        "days": 1034, "families": 30, "specs_per_family": 4,
        "worlds_per_frequency": worlds, "bootstrap_reps": bootstrap_reps,
        "block_sessions": 20, "hac_lags": 20, "effects_R": list(EFFECTS),
        "warning": "No executable market grammar or adaptive A/B/C replay; cannot freeze.",
        "results": {},
    }
    for f in frequencies:
        counts = {shape: {str(e): {level: 0 for level in LEVELS} for e in EFFECTS} for shape in SHAPES}
        for i in range(worlds):
            p = structured_panel(1034, f, seed + 100000 * f + i)
            for shape in SHAPES:
                result = evaluate_shape_effects(p, shape, EFFECTS, reps=bootstrap_reps,
                                                seed=seed + 10000000 * f + i)
                for e, r in zip(EFFECTS, result):
                    for level, yes in hits(r).items():
                        counts[shape][str(e)][level] += int(yes)
            if (i + 1) % 20 == 0:
                print(f"{f}/year: {i+1}/{worlds} worlds", flush=True)
        rates = {shape: {e: {level: v / worlds for level, v in levels.items()}
                         for e, levels in edges.items()} for shape, edges in counts.items()}
        mde = {shape: {level: mde_bracket({e: rates[shape][e][level] for e in rates[shape]}, 0.8)
                       for level in ("stepdown_120", "family", "neighborhood")}
               for shape in SHAPES}
        report["results"][str(f)] = {"rates": rates, "mde80_brackets": mde}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--frequencies", type=int, nargs="+", default=[100, 250, 500])
    p.add_argument("--worlds", type=int, default=120)
    p.add_argument("--bootstrap-reps", type=int, default=99)
    p.add_argument("--output", type=Path, default=Path("reports/V5_HIERARCHICAL_POWER.json"))
    a = p.parse_args()
    run(tuple(a.frequencies), a.worlds, a.bootstrap_reps, a.output)
