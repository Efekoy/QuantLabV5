"""Paired synthetic-only test of discovery gates versus holdout confirmation.

No real V5 partition is read. This experiment replays an adaptive *stream-level*
discovery screen, not the unfinished A/B/C market signal engine.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from quantlab5.v5.hierarchy import cluster_support
from quantlab5.v5.holdout import (discovery_screen, family_statistic,
                                 validate)
from quantlab5.v5.inference import hac_t
from quantlab5.v5.synthetic_streams import SHAPES, structured_panel

EFFECTS = (0.0, .05, .075, .10, .15)
METHODS = ("current", "holm", "stepdown", "bh", "by", "family_first")
FAMILY_STATS = ("daily_mean", "max", "top2", "median")


def reference(frequency: int, worlds: int, seed: int) -> dict:
    exact_val, fam_val, global_disc, family_disc = [], [], [], []
    family_refs = {k: [] for k in FAMILY_STATS}
    for i in range(worlds):
        d = structured_panel(2160, frequency, seed + 100000 * frequency + i)
        v = structured_panel(1008, frequency, seed + 9000000 + 100000 * frequency + i)
        te = hac_t(d.daily)
        tf = family_statistic(d.daily)
        global_disc.append(max(float(te.max()), float(tf.max())))
        family_disc.append(float(tf.max()))
        exact_val.append(hac_t(v.daily))
        fam_val.append(family_statistic(v.daily))
        for k in FAMILY_STATS:
            family_refs[k].append(family_statistic(v.daily, k))
    return {"exact_val": np.asarray(exact_val), "family_val": np.asarray(fam_val),
            "global_critical": float(np.quantile(global_disc, .95)),
            "family_critical": float(np.quantile(family_disc, .95)),
            "family_refs": {k: np.asarray(z) for k, z in family_refs.items()}}


def current_gate(nom, discovery: np.ndarray, ref: dict) -> tuple[int, ...]:
    if not nom.families:
        return ()
    te = hac_t(discovery)
    tf = family_statistic(discovery)
    if max(te.max(), tf.max()) <= ref["global_critical"]:
        return ()
    return tuple(j for j in nom.families if tf[j] > ref["family_critical"]
                 and cluster_support(discovery[:, 4*j:4*j+4]))


def run(frequencies: tuple[int, ...], worlds: int, refs: int,
        output: Path, seed: int = 20261003) -> dict:
    report = {"kind": "synthetic_stream_adaptive_holdout_architecture",
              "discovery_days": 2160, "validation_days": 1008,
              "worlds_per_frequency": worlds, "null_reference_worlds": refs,
              "effects_R": EFFECTS, "families": 30, "rules_per_family": 4,
              "discovery_screen": {"stress_increment_R": .02, "min_events": 120,
                                   "min_positive_neighbors": 3, "positive_halves": 2,
                                   "cross_family_corr_duplicate": .85},
              "warning": "Stream-level adaptive nomination, not executable A/B/C market replay; no real partition read.",
              "results": {}}
    for f in frequencies:
        null = reference(f, refs, seed + 111000000)
        stat_critical = {k: float(np.quantile(null["family_refs"][k].max(axis=1), .95))
                         for k in FAMILY_STATS}
        cells = {s: {str(e): {m: {"found": 0, "true_survivor": 0,
                                    "false_survivors": 0, "any_false": 0, "total_survivors": 0,
                                    "fdp_sum": 0.0} for m in METHODS}
                              | {"nominated_total": 0, "nominated_target": 0,
                                 "target_representative_true": 0, "target_stable": 0}
                          for e in EFFECTS} for s in SHAPES}
        # Family statistics evaluated on independent validation panels, with
        # a max-over-30 null cutoff for each prespecified statistic.
        family_stat_hits = {s: {str(e): {k: 0 for k in FAMILY_STATS} for e in EFFECTS} for s in SHAPES}
        for i in range(worlds):
            disc = structured_panel(2160, f, seed + 100000 * f + i)
            val = structured_panel(1008, f, seed + 9000000 + 100000 * f + i)
            for shape in SHAPES:
                for effect in EFFECTS:
                    key = str(effect)
                    dx, _ = disc.planted(shape, effect)
                    vx, _ = val.planted(shape, effect)
                    nom = discovery_screen(dx, disc.counts)
                    cell = cells[shape][key]
                    cell["nominated_total"] += len(nom.families)
                    cell["nominated_target"] += int(0 in nom.families)
                    cell["target_stable"] += int(0 in nom.qualified)
                    target_is_real = bool(effect > 0 and 0 in nom.families and
                                          SHAPES[shape][nom.representative[nom.families.index(0)]] > 0)
                    cell["target_representative_true"] += int(target_is_real)
                    confirmed = validate(nom, vx, null["exact_val"], null["family_val"])
                    eligible = set(current_gate(nom, dx, null))
                    confirmed["current"] = tuple(j for j in confirmed["holm"] if j in eligible)
                    for method in METHODS:
                        selected = confirmed[method]
                        true = int(0 in selected and target_is_real)
                        false = len(selected) - true
                        m = cell[method]
                        m["found"] += int(0 in nom.families)
                        m["true_survivor"] += true
                        m["false_survivors"] += false
                        m["any_false"] += int(false > 0)
                        m["total_survivors"] += len(selected)
                        m["fdp_sum"] += false / len(selected) if selected else 0.0
                    for method in FAMILY_STATS:
                        obs = family_statistic(vx, method)[0]
                        family_stat_hits[shape][key][method] += int(obs > stat_critical[method])
            if (i + 1) % 20 == 0:
                print(f"{f}/year: {i+1}/{worlds} paired worlds", flush=True)
        rates = {}
        for shape, effects in cells.items():
            rates[shape] = {}
            for e, raw in effects.items():
                rates[shape][e] = {
                    "mean_frozen_hypotheses": raw["nominated_total"] / worlds,
                    "target_nomination_rate": raw["nominated_target"] / worlds,
                    "target_stable_rate": raw["target_stable"] / worlds,
                    "target_representative_true_rate": raw["target_representative_true"] / worlds,
                    "methods": {m: {"target_survival": v["true_survivor"] / worlds,
                                    "mean_false_survivors": v["false_survivors"] / worlds,
                                    "any_false_rate": v["any_false"] / worlds,
                                    "mean_total_survivors": v["total_survivors"] / worlds,
                                    "fdr": v["fdp_sum"] / worlds}
                                for m, v in raw.items() if m in METHODS},
                    "family_stat_global_power": {k: n / worlds for k, n in family_stat_hits[shape][e].items()},
                }
        report["results"][str(f)] = {"rates": rates,
                                     "null_reference_critical": {k: null[k] for k in
                                                                  ("global_critical", "family_critical")}}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--frequencies", type=int, nargs="+", default=[100, 250, 500])
    p.add_argument("--worlds", type=int, default=120)
    p.add_argument("--refs", type=int, default=199)
    p.add_argument("--seed", type=int, default=20261003)
    p.add_argument("--output", type=Path, default=Path("reports/V5_HOLDOUT_ARCHITECTURES.json"))
    a = p.parse_args()
    run(tuple(a.frequencies), a.worlds, a.refs, a.output, seed=a.seed)
