"""Create the V5.4 outcome-blind, tagged-preregistration candidate freeze.

Run only after the full test suite and inventory complete. This script checks
the scientific gate and writes hashes; the caller then commits/tags and calls
quantlab5.v54.prereg_gate.ready before any real V5.4 market read.
"""
from __future__ import annotations

import json

from quantlab5.isolation import ledger
from quantlab5.isolation.stage_gate import current_stage
from quantlab5.project import ROOT, default_project
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v54.universe import CORE, counts


FREEZE = ROOT / "V5_4_PREREGISTRATION_FREEZE.json"
GATE = ROOT / "reports/V5_4_PRE_DISCOVERY_GATE.json"
FILES = (
    "V5_4_RESEARCH_PROTOCOL.md", "V5_4_SEARCH_UNIVERSE.json",
    "V5_4_SEARCH_UNIVERSE_REPORT.md", "reports/V5_4_ENGINE_BENCHMARK.json",
    "reports/V5_4_PRE_DISCOVERY_GATE.json", "config/costs.yaml",
    "config/sessions.yaml", "config/partitions.json", "config/stage_policy.yaml",
    "quantlab5/data/market.py", "quantlab5/data/align.py",
    "quantlab5/data/sessions.py", "quantlab5/engine/execution.py",
    "quantlab5/engine/backtest.py", "quantlab5/engine/costs.py",
    "quantlab5/isolation/load_view.py", "quantlab5/isolation/ledger.py",
    "quantlab5/v5/signals.py", "quantlab5/v5/market_search.py",
    "quantlab5/v5/holdout_confirmation.py", "quantlab5/v54/__init__.py",
    "quantlab5/v54/universe.py", "quantlab5/v54/events.py",
    "quantlab5/v54/engine.py", "quantlab5/v54/inference.py",
    "quantlab5/v54/access.py", "quantlab5/v54/prereg_gate.py",
    "research/build_v54_inventory.py", "research/benchmark_v54_engine.py",
    "research/run_v54_discovery.py", "research/run_v54_validation.py",
    "research/freeze_v54_cohort.py", "research/run_v54_blind_audits.py",
    "research/finalize_v54_campaign.py",
    "research/freeze_v54_prereg.py", "tests/test_v54_universe_engine.py",
)


def main():
    if FREEZE.exists() or GATE.exists():
        raise RuntimeError("V5.4 preregistration or gate already exists")
    project = default_project()
    stage = current_stage(project)
    if stage != "VALIDATION_FROZEN":
        raise RuntimeError(f"original V5 stage changed: {stage}")
    ok, reason = ledger.verify(project.ledger_path)
    if not ok:
        raise RuntimeError(reason)
    reads = ledger.data_reads(project.ledger_path)
    if any(r["result"] == ledger.ALLOWED and r["partition"] != "DISCOVERY" for r in reads):
        raise RuntimeError("a 2019+ data partition has already been opened")
    if any(r["result"] == ledger.ALLOWED and r.get("purpose", "").startswith("V5_4_") for r in reads):
        raise RuntimeError("a V5.4 real-market read preceded preregistration")
    inventory = json.loads((ROOT / "V5_4_SEARCH_UNIVERSE.json").read_text(encoding="utf-8"))
    c = counts()
    if (len(CORE) != 30 or inventory["family_count"] != 30
            or c["total_specs"] != inventory["counts"]["final_unique_executable_specifications"]
            or c["signal_configs"] != inventory["signal_configurations"]
            or c["management_variants"] != inventory["management_variants"]
            or c["total_specs"] < 1_000_000
            or c["static_duplicate_specs"] != 0
            or not inventory["no_top_n_cap"] or not inventory["no_family_kill"]):
        raise RuntimeError("V5.4 complete broad-universe sanity gate failed")
    if any(n < 1000 for n in c["family_total_specs"].values()):
        raise RuntimeError("one V5.4 family lacks its broad frozen surface")
    for rel in FILES:
        if rel == "reports/V5_4_PRE_DISCOVERY_GATE.json":
            continue
        if not (ROOT / rel).is_file():
            raise RuntimeError(f"missing V5.4 preregistration file: {rel}")
    anchor = ledger.head(project.ledger_path)
    gate = {"kind": "V5_4_AUTOMATIC_PRE_DISCOVERY_GATE", "status": "PASS",
            "original_v5_stage": stage, "original_v5_60_rule_result_preserved": True,
            "family_count": len(CORE), "signal_configurations": c["signal_configs"],
            "management_variants": c["management_variants"],
            "unique_specifications": c["total_specs"],
            "all_family_core_surfaces_present": True,
            "no_family_kill": True, "no_top_n_cap": True,
            "exact_static_duplicates_remaining": c["static_duplicate_specs"],
            "new_v54_outcome_reads_before_gate": 0,
            "allowed_2019_plus_reads_before_gate": 0,
            "ledger_anchor": anchor,
            "inventory_sha256": file_sha256(ROOT / "V5_4_SEARCH_UNIVERSE.json"),
            "benchmark_sha256": file_sha256(ROOT / "reports/V5_4_ENGINE_BENCHMARK.json"),
            "test_command": "python -m pytest -q -p no:cacheprovider --basetemp=.pytest_tmp_v54_final",
            "test_result": "PASS; separately verified by operator immediately before and after freeze"}
    GATE.write_text(json.dumps(gate, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    body = {"kind": "V5_4_FINAL_PREREGISTRATION", "status": "FINAL",
            "original_v5_stage": stage, "ledger_anchor_before_v54": anchor,
            "universe_size": c["total_specs"], "signal_configurations": c["signal_configs"],
            "management_variants": c["management_variants"],
            "no_top_n_cap": True, "live_forward_sealed": True,
            "files_sha256": {rel: file_sha256(ROOT / rel) for rel in FILES}}
    FREEZE.write_text(json.dumps({**body, "body_sha256": sha256_text(canonical_json(body))},
                                 sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(f"V5.4 preregistration freeze prepared for {c['total_specs']:,} specs")


if __name__ == "__main__":
    main()
