"""One-time V5.1 null-engine protocol freeze, before any new DISCOVERY read."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import subprocess

from quantlab5.isolation import ledger
from quantlab5.project import ROOT, default_project
from quantlab5.search.candidate_id import candidate_id
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v5.candidate_inventory import inventory
from quantlab5.v5_1.access import FREEZE, LEDGER, STATE

READS_MARKET_DATA = False
STRATEGY_FILES = (
    "quantlab5/v5/candidate_inventory.py", "quantlab5/v5/signals.py",
    "quantlab5/v5/market_search.py", "quantlab5/v5/validation.py",
    "quantlab5/v5/inference.py", "quantlab5/v5/market_plant.py",
    "quantlab5/v5/duplicate_accounting.py", "quantlab5/v5/risk_coverage.py",
    "quantlab5/engine/execution.py", "quantlab5/engine/costs.py",
    "config/costs.yaml", "config/stage_policy.yaml", "config/execution.yaml",
)
FILES = STRATEGY_FILES + (
    "quantlab5/v5_1/access.py", "quantlab5/v5_1/paired_null.py",
    "quantlab5/isolation/load_view.py", "quantlab5/isolation/stage_gate.py",
    "quantlab5/isolation/ledger.py", "quantlab5/project.py",
    "quantlab5/data/schema.py", "quantlab5/data/sessions.py",
    "research/calibrate_v5_1_nuisance.py", "research/check_v5_1_nuisance.py",
    "research/run_v5_1_executable_calibration.py",
    "research/freeze_v5_1_nuisance.py",
    "V5_1_NUISANCE_PROTOCOL.md", "V5_1_NULL_GENERATOR_DIAGNOSIS.md",
    "reports/V5_CANDIDATE_INVENTORY.json", "config/partitions.json",
    "config/paths.yaml", "config/search.yaml", "config/nulls.yaml",
    "config/prop_profiles.yaml", "config/sessions.yaml",
)


def main() -> None:
    if FREEZE.exists() or STATE.exists() or LEDGER.exists():
        raise RuntimeError("V5.1 freeze or access state already exists")
    if (ROOT / "V5_1_DISCOVERY_NUISANCE_CALIBRATION.json").exists():
        raise RuntimeError("V5.1 calibration artifact exists before freeze")
    project = default_project()
    if json.loads(project.stage_state_path.read_text(encoding="utf-8"))["stage"] != "DISCOVERY":
        raise RuntimeError("V5.1 null engineering requires the DISCOVERY stage")
    ok, reason = ledger.verify(project.ledger_path)
    if not ok:
        raise RuntimeError(reason)
    sealed = {"VALIDATION", "HISTORICAL_AUDIT_1", "HISTORICAL_AUDIT_2", "LIVE_FORWARD"}
    if any(r.get("result") == "ALLOWED" and r.get("partition") in sealed
           for r in ledger.data_reads(project.ledger_path)):
        raise RuntimeError("a later partition has already been opened")
    tag = subprocess.run(["git", "rev-parse", "v5-calibration-failed^{commit}"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    unchanged = subprocess.run(["git", "diff", "--quiet", "v5-calibration-failed", "--",
                                *STRATEGY_FILES], cwd=ROOT)
    if unchanged.returncode != 0:
        raise RuntimeError("V5.1 strategy grammar or gates differ from stopped V5")
    protocol = (ROOT / "V5_1_NUISANCE_PROTOCOL.md").read_text(encoding="utf-8")
    if "**Status: FROZEN ENGINEERING PROTOCOL." not in protocol:
        raise RuntimeError("V5.1 protocol document is not marked frozen")
    inv = inventory()
    stage_a = [candidate_id(x) for x in inv["stage_a"]]
    universe = [candidate_id(x) for x in (inv["stage_a"] + inv["stage_b"]
                                           + inv["stage_c_universe"])]
    ledger.append(LEDGER, "V5_1_LEDGER_CREATED", reason="new successor nuisance ledger",
                  v5_archive_commit=tag)
    anchor = ledger.head(LEDGER)
    body = {
        "kind": "V5_1_NUISANCE_PROTOCOL_FREEZE", "status": "FROZEN",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "v5_failed_archive_commit": tag,
        "v5_science_freeze_sha256": file_sha256(ROOT / "V5_PRECALIBRATION_SCIENCE_FREEZE.json"),
        "strategy_files_unchanged_from_v5_tag": True,
        "stage_a_ids_sha256": sha256_text("\n".join(stage_a)),
        "candidate_universe_ids_sha256": sha256_text("\n".join(universe)),
        "files_sha256": {rel: file_sha256(ROOT / rel) for rel in FILES},
        "worker_permissions": {"partition": "DISCOVERY", "instruments": ["NQ", "ES"],
            "start": "2010-06-08", "end": "2018-12-31",
            "columns": ["open", "high", "low", "close", "volume", "symbol"],
            "reason": "V5_1_CALIBRATION_NUISANCE_ACCESS"},
        "candidate_modes_in_priority_order": ["paired_sign", "paired_day_resample",
                                               "state_conditioned_sign"],
        "fidelity_seeds": [9101, 9102, 9103],
        "thresholds": {"clock_quantile_relative_max": .25,
                       "median_price_relative_error_max": .20,
                       "clock_zero_fraction_error_max": .02,
                       "lag_dependence_error_max": .10,
                       "cross_market_nuisance_error_max": .10,
                       "same_minute_sign_agreement_error_max": .05,
                       "zero_edge_directional_diagnostic_max": .01},
        "power_gate": {"all_null_worlds": 200, "adaptive_null_reference_worlds": 500,
                       "false_survivor_upper95_max": .10,
                       "plateau_0p10_500_lower95_min": .70,
                       "plateau_0p15_500_lower95_min": .90},
        "ledger_anchor_before_access": anchor,
        "real_strategy_search_authorized": False,
        "later_partitions_opened": False,
    }
    doc = {**body, "body_sha256": sha256_text(canonical_json(body))}
    FREEZE.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    freeze_hash = file_sha256(FREEZE)
    ledger.append(LEDGER, "V5_1_NUISANCE_PROTOCOL_FROZEN",
                  reason="null architectures, diagnostics and gates frozen before new access",
                  freeze_sha256=freeze_hash)
    STATE.write_text(json.dumps({"state": "ARMED", "freeze_sha256": freeze_hash},
                                sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(freeze_hash)


if __name__ == "__main__":
    main()
