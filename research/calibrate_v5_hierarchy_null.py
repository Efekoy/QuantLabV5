"""Independent zero-edge check of the fixed-library hierarchy only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scipy.stats import beta

from quantlab5.v5.hierarchy import evaluate_hierarchy
from quantlab5.v5.synthetic_streams import structured_panel


def upper95(k: int, n: int) -> float:
    return float(beta.ppf(0.95, k + 1, n - k)) if k < n else 1.0


def run(frequencies: tuple[int, ...], worlds: int, output: Path) -> dict:
    fields = ("single_hac", "single_bootstrap", "holm", "stepdown", "global", "family", "neighborhood", "naive_event")
    report = {"kind": "independent_zero_edge_fixed_library_check", "worlds_per_frequency": worlds,
              "bootstrap_reps": 99, "days": 1034, "seed_base": 20261001, "results": {}}
    for f in frequencies:
        hits = dict.fromkeys(fields, 0)
        for i in range(worlds):
            panel = structured_panel(1034, f, 20261001 + 100000 * f + i)
            r = evaluate_hierarchy(panel.daily, target_events=panel.target_event_r,
                                   reps=99, seed=303001 + 100000 * f + i)
            flags = (r.single_hac_p <= .05, r.single_bootstrap_p <= .05,
                     r.holm_p <= .05, r.stepdown_p <= .05, r.global_p <= .05,
                     r.family_supported, r.neighborhood_supported, r.naive_event_p <= .05)
            for name, flag in zip(fields, flags):
                hits[name] += int(flag)
            if (i + 1) % 50 == 0:
                print(f"null {f}/year: {i+1}/{worlds}", flush=True)
        report["results"][str(f)] = {name: {"hits": k, "rate": k / worlds,
                                             "upper95": upper95(k, worlds)}
                                      for name, k in hits.items()}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--frequencies", type=int, nargs="+", default=[100, 250, 500])
    p.add_argument("--worlds", type=int, default=300)
    p.add_argument("--output", type=Path, default=Path("reports/V5_HIERARCHICAL_NULL.json"))
    a = p.parse_args()
    run(tuple(a.frequencies), a.worlds, a.output)
