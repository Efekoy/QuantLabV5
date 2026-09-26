"""Final holdout protocol and research preregistration freeze, before strategy read."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import subprocess

from quantlab5.isolation import ledger
from quantlab5.project import ROOT, default_project
from quantlab5.search.candidate_id import candidate_id
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v5.candidate_inventory import inventory

READS_MARKET_DATA = False
HOLDOUT = ROOT / "V5_HOLDOUT_CONFIRMATION_PROTOCOL_FREEZE.json"
FINAL = ROOT / "V5_PREREGISTRATION_FREEZE.json"
TESTS = ROOT / "reports/V5_PREDISCOVERY_TESTS.json"
FILES = (
    "V5_NULL_PROGRAM_CONCLUSION.md", "V5_HOLDOUT_CONFIRMATION_PROTOCOL.md",
    "V5_RESEARCH_PREREGISTRATION.md", "V5_STRATEGY_CATALOG.md",
    "V5_POWER_CALIBRATION_REPORT.md", "V5_NULL_METHOD_REPORT.md",
    "V5_PRIOR_LAB_COVERAGE.md", "config/stage_policy.yaml",
    "config/costs.yaml", "config/execution.yaml", "config/sessions.yaml",
    "config/prop_profiles.yaml", "config/partitions.json",
    "quantlab5/v5/candidate_inventory.py", "quantlab5/v5/signals.py",
    "quantlab5/v5/market_search.py", "quantlab5/v5/holdout_confirmation.py",
    "quantlab5/v5/audit.py", "quantlab5/v5/inference.py",
    "quantlab5/v5/duplicate_accounting.py", "quantlab5/v5/risk_coverage.py",
    "quantlab5/v5/cohort.py", "quantlab5/data/market.py",
    "quantlab5/data/schema.py", "quantlab5/engine/execution.py",
    "quantlab5/engine/costs.py", "quantlab5/isolation/load_view.py",
    "quantlab5/isolation/stage_gate.py", "quantlab5/isolation/prereg_gate.py",
    "research/run_v5_discovery.py", "research/run_v5_validation.py",
    "research/freeze_v5_final_cohort.py",
    "research/run_v5_blind_audits.py", "research/freeze_v5_holdout_confirmation.py",
    "research/finalize_v5_campaign.py",
    "tests/test_v5_holdout_confirmation.py", "tests/test_v5_blind_audit.py",
    "tests/test_v5_prereg_gate.py", "reports/V5_CANDIDATE_INVENTORY.json",
    "reports/V5_PREDISCOVERY_TESTS.json",
)
FAILURE_TAGS = ("v5-calibration-failed", "v5.1-calibration-failed",
                "v5.2-calibration-failed", "v5.3-calibration-failed",
                "v5-direct-null-failed")


def _hash_doc(body):
    return {**body, "body_sha256": sha256_text(canonical_json(body))}


def main():
    if HOLDOUT.exists():
        raise RuntimeError("holdout protocol already frozen")
    if json.loads(FINAL.read_text(encoding="utf-8")).get("status") != "REVIEW_REQUIRED":
        raise RuntimeError("preexisting V5 draft freeze is not the expected review state")
    project = default_project()
    stage = json.loads(project.stage_state_path.read_text(encoding="utf-8"))["stage"]
    if stage != "DISCOVERY":
        raise RuntimeError("final preregistration requires unopened DISCOVERY strategy stage")
    ok, reason = ledger.verify(project.ledger_path)
    if not ok:
        raise RuntimeError(reason)
    forbidden = [x for x in ledger.data_reads(project.ledger_path)
                 if x.get("result") == ledger.ALLOWED
                 and x.get("reason") == "REAL_DISCOVERY_SEARCH_ACCESS"]
    if forbidden:
        raise RuntimeError("real V5 strategy DISCOVERY access already occurred")
    tests = json.loads(TESTS.read_text(encoding="utf-8"))
    if tests.get("status") != "PASS" or tests.get("failed", 1) != 0 or tests.get("passed", 0) < 300:
        raise RuntimeError("complete pre-DISCOVERY executable test suite did not pass")
    inv = inventory()
    ids = [candidate_id(x) for x in inv["stage_a"]+inv["stage_b"]+inv["stage_c_universe"]]
    if inv["counts"]["A"] != 60 or len(ids) != len(set(ids)):
        raise RuntimeError("candidate inventory changed")
    tags = {}
    for tag in FAILURE_TAGS:
        tags[tag] = subprocess.run(["git", "rev-parse", f"{tag}^{{commit}}"], cwd=ROOT,
                                   check=True, capture_output=True, text=True).stdout.strip()
    anchor = ledger.head(project.ledger_path)
    body = {
        "kind": "V5_HOLDOUT_CONFIRMATION_PROTOCOL_FREEZE", "status": "FROZEN",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_universe_ids_sha256": sha256_text("\n".join(ids)),
        "inventory_counts": inv["counts"], "failed_null_archive_tags": tags,
        "files_sha256": {rel: file_sha256(ROOT/rel) for rel in FILES},
        "ledger_anchor_before_discovery": anchor,
        "discovery_period": ["2010-06-08", "2018-12-31"],
        "validation_period": ["2019-01-02", "2022-12-30"],
        "audit_1_period": ["2023-01-03", "2025-12-31"],
        "audit_2_start": "2026-01-02",
        "stage_a_reference": {"type": "common-day centered stationary bootstrap",
                              "reps": 500, "block": 20, "hac_lags": 20, "seed": 515001,
                              "family_expansion_p_max": .10},
        "validation": {"type": "exact-candidate Romano-Wolf stepdown",
                       "alpha_one_sided": .05, "reps": 500, "near_boundary_reps": 2000,
                       "block": 20, "hac_lags": 20, "seed": 515005,
                       "near_boundary_band": .01},
        "discovery_qualifier": {"trades_min": 120, "active_years_min": 6,
                                "mean_daily_net_r_positive": True,
                                "stress_net_r_positive": True,
                                "matched_excess_positive": True},
        "validation_support": {"trades_min": 40, "active_years_min": 2,
                               "adjusted_p_max": .05, "stress_net_positive": True,
                               "matched_excess_positive": True},
        "classifications": ["SUPPORTED", "INCONCLUSIVE / UNDERPOWERED", "REJECTED"],
        "no_cap_advancement": True,
        "portfolio_selection": "none; individual four-budget diagnostics only",
        "audit_reveal": "both complete and cohort/hash verified before either public result",
        "live_forward_open_authorized": False,
    }
    HOLDOUT.write_text(json.dumps(_hash_doc(body), sort_keys=True, indent=2)+"\n",
                       encoding="utf-8")
    final_body = {
        "kind": "V5_FINAL_PREREGISTRATION", "status": "FINAL",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "holdout_protocol_sha256": file_sha256(HOLDOUT),
        "files_sha256": {**body["files_sha256"],
                         "V5_HOLDOUT_CONFIRMATION_PROTOCOL_FREEZE.json": file_sha256(HOLDOUT)},
        "candidate_universe_ids_sha256": body["candidate_universe_ids_sha256"],
        "ledger_anchor_before_discovery": anchor,
        "real_discovery_strategy_outcomes_before_freeze": 0,
        "null_market_calibration_required": False,
        "validation_primary_confirmation": True,
        "no_cap_advancement": True,
        "portfolio_selection": "none; individual four-budget diagnostics only",
        "live_forward_open_authorized": False,
    }
    FINAL.write_text(json.dumps(_hash_doc(final_body), sort_keys=True, indent=2)+"\n",
                     encoding="utf-8")
    print(file_sha256(HOLDOUT), file_sha256(FINAL))


if __name__ == "__main__":
    main()
