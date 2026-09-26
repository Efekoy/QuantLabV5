"""Generate the complete, compact V5.4 grammar inventory without market data."""
from __future__ import annotations

from collections import Counter
import json

from quantlab5.project import ROOT
from quantlab5.util.hashing import file_sha256
from quantlab5.v54.universe import (CORE, DIRECTIONS, ENTRIES, SESSIONS,
                                     counts, filters_for, managements)
from research.run_v54_discovery import DTYPE


OUT = ROOT / "V5_4_SEARCH_UNIVERSE.json"
REPORT = ROOT / "V5_4_SEARCH_UNIVERSE_REPORT.md"


def _family_descriptions():
    rows = {}
    for line in (ROOT/"V5_STRATEGY_CATALOG.md").read_text(encoding="utf-8").splitlines():
        parts = line.split("|")
        if len(parts) >= 4 and parts[1].strip() in CORE:
            rows[parts[1].strip()] = parts[2].strip()
    if set(rows) != set(CORE):
        raise RuntimeError("original V5 catalog does not identify all 30 family mechanisms")
    return rows


def _axis_counts(management):
    def label(x):
        return "none" if x is None or x is False else str(x)
    out = {}
    for key in ("stop", "target_r", "breakeven_r", "partial_r",
                "partial_fraction", "trail_r", "hold", "mechanism_exit"):
        out[key] = dict(sorted(Counter(label(getattr(m, key)) for m in management).items()))
    return out


def build():
    c = counts()
    management = managements()
    descriptions = _family_descriptions()
    families = {}
    for family in CORE:
        looks, thresholds = CORE[family]
        families[family] = {
            "original_executable_definition": descriptions[family],
            "core_axes": {"lookback": list(looks), "threshold": list(thresholds)},
            "core_signal_variants": c["family_core_variants"][family],
            "directions": list(DIRECTIONS), "sessions": list(SESSIONS),
            "filter_variants": [list(x) for x in filters_for(family)],
            "entry_variants": list(ENTRIES),
            "signal_configurations": c["family_signal_configs"][family],
            "management_compatible_configurations": c["family_total_specs"][family],
        }
    # The broad draft had four windows; 'globex' is exactly identical to rth
    # because the original family gate only emits executable 09:35–15:15 signals.
    all_four = c["pre_dedup_rth_plus_globex_specs"]
    naive_mgmt = 6 * 7 * 3 * 3 * 3 * 4 * 2
    signal = c["signal_configs"]
    mgmt_count = len(management)
    benchmark_path = ROOT / "reports/V5_4_ENGINE_BENCHMARK.json"
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8")) if benchmark_path.exists() else None
    doc = {
        "kind": "V5_4_POST_ORIGINAL_V5_BROAD_DISCOVERY_UNIVERSE",
        "status": "PRE_OUTCOME_INVENTORY",
        "original_v5_result": "60 Stage A evaluated; 0 qualified; later partitions unopened",
        "original_catalog_sha256": file_sha256(ROOT/"V5_STRATEGY_CATALOG.md"),
        "family_count": 30,
        "families": families,
        "signal_configurations": c["signal_configs"],
        "management_variants": c["management_variants"],
        "management_templates": [m.as_dict() for m in management],
        "management_by_template_per_signal": c["by_template_per_signal"],
        "specifications_by_template": c["by_template_total"],
        "management_axis_counts_per_signal": _axis_counts(management),
        "dimensions": {"directions": list(DIRECTIONS), "sessions": list(SESSIONS),
                       "entries": list(ENTRIES),
                       "filter_count_per_family": {"zero": 1, "one": 3, "two": 1}},
        "specifications_by_direction": {x: c["total_specs"]//len(DIRECTIONS) for x in DIRECTIONS},
        "specifications_by_session": {x: c["total_specs"]//len(SESSIONS) for x in SESSIONS},
        "specifications_by_filter_count": {
            "zero": signal//5*mgmt_count,
            "one": signal//5*3*mgmt_count,
            "two": signal//5*mgmt_count},
        "specifications_by_management_axis": {
            axis: {value: n*signal for value, n in values.items()}
            for axis, values in _axis_counts(management).items()},
        "storage_and_runtime": {
            "first_pass_row_bytes": DTYPE.itemsize,
            "first_pass_npy_estimated_bytes": c["total_specs"]*DTYPE.itemsize+128,
            "qualifier_index_worst_case_bytes": c["total_specs"]*8+128,
            "qualifier_detail_and_validation_size": "outcome-dependent; no candidate cap",
            "peak_ram_pre_run_estimate_gb": "4–12 GB, unverified until a full-market run",
            "synthetic_kernel_benchmark": benchmark,
            "full_run_note": "Kernel timing excludes real-world feature/event generation, qualifier reruns, hashing, data loading and disk IO; it is a lower bound, not a wall-clock forecast."},
        "counts": {
            "raw_four_session_valid_specifications": all_four,
            "naive_management_cartesian_per_signal": naive_mgmt,
            "invalid_management_tuples_excluded_per_signal": naive_mgmt-len(management),
            "invalid_management_tuples_excluded_over_final_signal_set":
                (naive_mgmt-len(management))*c["signal_configs"],
            "semantic_static_duplicates_removed": c["semantic_static_duplicates_removed"],
            "duplicate_reason": "globex and rth are equivalent under original V5 RTH-only SignalContext.base_ok",
            "remaining_static_duplicates": c["static_duplicate_specs"],
            "final_unique_executable_specifications": c["total_specs"],
        },
        "candidate_id": "Q54 + first 24 SHA-256 hex characters of canonical spec in namespace quantlab5.v54.broad_discovery",
        "inventory_representation": "finite axis lists, disjoint template list, and canonical Cartesian iterator; no materialized 14-million-row JSON",
        "no_family_kill": True,
        "no_top_n_cap": True,
        "outcome_reads": 0,
    }
    return doc


def main():
    if OUT.exists() or REPORT.exists():
        raise RuntimeError("V5.4 universe inventory already exists")
    doc = build()
    c = counts()
    all_four = doc["counts"]["raw_four_session_valid_specifications"]
    naive_mgmt = doc["counts"]["naive_management_cartesian_per_signal"]
    management = managements()
    benchmark = doc["storage_and_runtime"]["synthetic_kernel_benchmark"]
    OUT.write_text(json.dumps(doc, sort_keys=True, indent=2, allow_nan=False)+"\n",
                   encoding="utf-8")
    lines = ["# V5.4 broad discovery universe", "",
             "Post-original-V5 design inventory, generated before any V5.4 real strategy outcome.", "",
             f"Original V5 campaign: {doc['original_v5_result']}.",
             f"30 families; {doc['signal_configurations']:,} signal configurations; "
             f"{doc['management_variants']} management variants; "
             f"{doc['counts']['final_unique_executable_specifications']:,} unique executable specifications.",
             f"Removed {doc['counts']['semantic_static_duplicates_removed']:,} exact RTH/Globex "
             "semantic duplicates before the final count.", "",
             "| Family | Core | Signal configurations | Combined specifications |",
             "| --- | ---: | ---: | ---: |"]
    for f, row in doc["families"].items():
        lines.append(f"| {f} | {row['core_signal_variants']} | "
                     f"{row['signal_configurations']:,} | "
                     f"{row['management_compatible_configurations']:,} |")
    lines += ["", "Every family evaluates its full prespecified core surface. "
              "Family performance cannot stop expansion because there is no family kill gate.",
              "", "## Combinatorial accounting", "",
              f"Four-session raw valid combinations: {all_four:,}; exact RTH/Globex "
              f"duplicates removed: {c['semantic_static_duplicates_removed']:,}; "
              f"remaining static duplicates: {c['static_duplicate_specs']:,}.",
              f"Naive management Cartesian tuples per signal: {naive_mgmt:,}; "
              f"invalid/inconsistent tuples excluded per signal: {naive_mgmt-len(management):,}; "
              f"valid disjoint templates per signal: {len(management)}.",
              "", "## Counts by template and axes", "",
              "| Management template | Per signal | Complete universe |",
              "| --- | ---: | ---: |"]
    for template, n in c["by_template_per_signal"].items():
        lines.append(f"| {template} | {n:,} | {c['by_template_total'][template]:,} |")
    lines += ["", "| Signal axis | Value | Complete universe |",
              "| --- | --- | ---: |"]
    for axis, values in (("direction", doc["specifications_by_direction"]),
                         ("session", doc["specifications_by_session"]),
                         ("filter count", doc["specifications_by_filter_count"])):
        for value, n in values.items():
            lines.append(f"| {axis} | {value} | {n:,} |")
    lines += ["", "| Management axis | Value | Complete universe |",
              "| --- | --- | ---: |"]
    for axis, values in doc["specifications_by_management_axis"].items():
        for value, n in values.items():
            lines.append(f"| {axis} | {value} | {n:,} |")
    bench = benchmark["measurements"][-1] if benchmark else None
    lines += ["", "## Compute and storage planning", "",
              f"First-pass storage: {doc['storage_and_runtime']['first_pass_npy_estimated_bytes']/1e9:.2f} GB "
              f"({DTYPE.itemsize} bytes/specification). Worst-case qualifier index: "
              f"{doc['storage_and_runtime']['qualifier_index_worst_case_bytes']/1e9:.2f} GB. "
              "Detail, validation, and audit files depend on the uncapped qualifying cohort.",
              "Pre-run peak process RAM estimate: 4–12 GB, unverified until a full-market run."]
    if bench:
        lines += [f"Actual sparse-kernel benchmark: {bench['specifications_per_second']:,.0f} "
                  f"specifications/second at {bench['specifications']:,} synthetic evaluations; "
                  f"10 million kernel calls ~{benchmark['estimated_10m_seconds_at_1m_rate']:.0f} s; "
                  f"full universe kernel calls ~{benchmark['estimated_full_universe_seconds_at_1m_rate']:.0f} s.",
                  "These times are lower bounds only. Real feature/event generation, real entry "
                  "density, qualifier reruns, hashing, and storage may extend the full run to many hours."]
    lines += ["", "Full axes and all management templates are in `V5_4_SEARCH_UNIVERSE.json`."]
    REPORT.write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(f"V5.4 inventory: {doc['counts']['final_unique_executable_specifications']:,} specs")


if __name__ == "__main__":
    main()
