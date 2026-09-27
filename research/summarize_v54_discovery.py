"""Descriptive overlap diagnostics for every uncapped V5.4 qualifier.

This is a post-search report. It does not alter the frozen five-part screen,
candidate IDs, or subsequent exact-candidate validation set.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json

import numpy as np

from quantlab5.project import ROOT


SOURCE = ROOT / "reports/v54/qualifier_details.jsonl"
OUT = ROOT / "reports/V5_4_DISCOVERY_OVERLAP.jsonl"
SUMMARY = ROOT / "reports/V5_4_DISCOVERY_OVERLAP_SUMMARY.json"
REPORT = ROOT / "V5_4_DISCOVERY_REPORT.md"


def main():
    if OUT.exists() or SUMMARY.exists():
        raise RuntimeError("V5.4 overlap output already exists")
    first = json.loads((ROOT / "reports/v54/first_pass_complete.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines()]
    if len(rows) != first["qualifier_count"] or len({r["candidate_id"] for r in rows}) != len(rows):
        raise RuntimeError("qualifier details incomplete or duplicated")
    entry_groups = defaultdict(list)
    path_groups = Counter()
    realized_groups = Counter()
    for i, row in enumerate(rows):
        entries = tuple(row["trade_entry_indices"])
        exits = tuple(row["trade_exit_indices"])
        entry_groups[entries].append(i)
        path_groups[(entries, exits)] += 1
        realized_groups[(entries, exits, tuple(row["trade_net_r"]))] += 1
    max_corr = [None] * len(rows)
    for entries, indices in entry_groups.items():
        if len(indices) < 2 or len(entries) < 2:
            continue
        pnl = np.asarray([rows[i]["trade_net_r"] for i in indices], float)
        centered = pnl - pnl.mean(axis=1, keepdims=True)
        norm = np.sqrt(np.sum(centered * centered, axis=1))
        valid = norm > 0
        if np.count_nonzero(valid) < 2:
            continue
        z = np.zeros_like(centered)
        z[valid] = centered[valid] / norm[valid, None]
        corr = z @ z.T
        np.fill_diagonal(corr, -np.inf)
        for k, i in enumerate(indices):
            same = valid & valid[k]
            same[k] = False
            if np.any(same):
                max_corr[i] = float(np.max(corr[k, same]))
    with OUT.open("w", encoding="utf-8") as f:
        for i, row in enumerate(rows):
            entries = tuple(row["trade_entry_indices"])
            exits = tuple(row["trade_exit_indices"])
            record = {"candidate_id": row["candidate_id"],
                      "same_entry_peer_count": len(entry_groups[entries]) - 1,
                      "same_entry_exit_peer_count": path_groups[(entries, exits)] - 1,
                      "same_realized_trade_record_peer_count":
                          realized_groups[(entries, exits, tuple(row["trade_net_r"]))] - 1,
                      "max_same_entry_trade_pnl_correlation": max_corr[i]}
            f.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
    summary = {
        "kind": "V5_4_DISCOVERY_QUALIFIER_OVERLAP_DESCRIPTION",
        "qualifier_count": len(rows),
        "same_entry_duplicate_pairs": sum(len(v) * (len(v) - 1) // 2
                                          for v in entry_groups.values()),
        "same_entry_exit_duplicate_pairs": sum(n * (n - 1) // 2
                                               for n in path_groups.values()),
        "same_realized_trade_record_duplicate_pairs": sum(n * (n - 1) // 2
                                                         for n in realized_groups.values()),
        "trade_pnl_correlation_scope": "only pairs with identical entry indices; descriptive, no candidate deletion",
        "qualifiers_with_finite_same_entry_trade_pnl_correlation":
            sum(x is not None for x in max_corr),
    }
    SUMMARY.write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    dist = first["outcome_distributions"]
    with REPORT.open("a", encoding="utf-8") as f:
        f.write("\n## Full-universe outcome counts\n\n")
        f.write(f"Baseline profitable after costs: {first['summary_counts']['positive_net_r']:,}; "
                f"stress positive: {first['summary_counts']['positive_stress_net_r']:,}. "
                "These are descriptive search counts, not evidence of a tradable edge.\n\n")
        for axis in ("family", "management_template", "session", "direction"):
            f.write(f"### {axis.replace('_', ' ').title()}\n\n")
            f.write("| Value | Evaluated | Baseline profitable | Stress positive | PF > 1 |\n")
            f.write("| --- | ---: | ---: | ---: | ---: |\n")
            for value, x in dist[axis].items():
                f.write(f"| {value} | {x['evaluated']:,} | {x['profitable_after_cost']:,} | "
                        f"{x['stress_positive']:,} | {x['profit_factor_gt_1']:,} |\n")
            f.write("\n")
        f.write(f"Among all qualifiers, identical entry-index pairs: "
                f"{summary['same_entry_duplicate_pairs']:,}; identical entry/exit pairs: "
                f"{summary['same_entry_exit_duplicate_pairs']:,}; identical realized "
                f"trade-record pairs: {summary['same_realized_trade_record_duplicate_pairs']:,}. "
                "Per-candidate same-entry trade P&L correlations are in the overlap JSONL. "
                "These annotations do not delete or rank candidates.\n")
    print(f"V5.4 overlap described for all {len(rows):,} qualifiers")


if __name__ == "__main__":
    main()
