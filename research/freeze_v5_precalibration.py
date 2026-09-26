"""Create the immutable precalibration science hash pin before nuisance access."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from quantlab5.isolation import ledger
from quantlab5.isolation.calibration_gate import FREEZE, STATE
from quantlab5.project import ROOT, default_project
from quantlab5.search.candidate_id import candidate_id
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v5.candidate_inventory import inventory

READS_MARKET_DATA = False
PINNED_FILES = (
    "quantlab5/search/candidate_id.py", "quantlab5/data/market.py",
    "quantlab5/data/schema.py", "quantlab5/data/sessions.py",
    "quantlab5/features/ops.py", "quantlab5/engine/execution.py",
    "quantlab5/engine/costs.py",
    "quantlab5/v5/candidate_inventory.py", "quantlab5/v5/signals.py",
    "quantlab5/v5/market_search.py", "quantlab5/v5/duplicate_accounting.py",
    "quantlab5/v5/validation.py", "quantlab5/v5/inference.py",
    "quantlab5/v5/risk_coverage.py", "quantlab5/v5/calibrated_null.py",
    "quantlab5/v5/market_plant.py", "quantlab5/isolation/load_view.py",
    "quantlab5/isolation/calibration_gate.py",
    "research/calibrate_v5_discovery_nuisance.py",
    "research/freeze_v5_precalibration.py",
    "research/check_v5_nuisance_fit.py", "research/run_v5_executable_calibration.py",
    "V5_PRECALIBRATION_SCIENCE_PROTOCOL.md", "V5_RESEARCH_PREREGISTRATION.md",
    "V5_STRATEGY_CATALOG.md", "V5_NULL_METHOD_REPORT.md",
    "V5_POWER_CALIBRATION_REPORT.md", "V5_PRIOR_LAB_COVERAGE.md",
    "reports/V5_CANDIDATE_INVENTORY.json", "config/partitions.json",
    "config/paths.yaml", "config/sessions.yaml", "config/search.yaml",
    "config/costs.yaml", "config/stage_policy.yaml", "config/execution.yaml",
    "config/nulls.yaml", "config/prop_profiles.yaml",
)


def main() -> None:
    project = default_project()
    path = ROOT / FREEZE
    state_path = ROOT / STATE
    if path.exists() or state_path.exists():
        raise RuntimeError("precalibration freeze/access state already exists")
    if (ROOT / "V5_DISCOVERY_NUISANCE_CALIBRATION.json").exists():
        raise RuntimeError("nuisance calibration already exists before freeze")
    stage = json.loads(project.stage_state_path.read_text(encoding="utf-8"))["stage"]
    if stage != "DISCOVERY":
        raise RuntimeError("precalibration requires DISCOVERY stage")
    ok, reason = ledger.verify(project.ledger_path)
    if not ok:
        raise RuntimeError(reason)
    sealed = {"VALIDATION", "HISTORICAL_AUDIT_1", "HISTORICAL_AUDIT_2", "LIVE_FORWARD"}
    if any(r.get("result") == "ALLOWED" and r.get("partition") in sealed
           for r in ledger.data_reads(project.ledger_path)):
        raise RuntimeError("sealed market read already exists in access ledger")
    protocol = (ROOT / "V5_PRECALIBRATION_SCIENCE_PROTOCOL.md").read_text(encoding="utf-8")
    if "**Status: FROZEN SCIENCE DESIGN." not in protocol:
        raise RuntimeError("science protocol document is not marked frozen")
    space = inventory()
    stage_a = [candidate_id(s) for s in space["stage_a"]]
    all_ids = [candidate_id(s) for s in space["stage_a"] + space["stage_b"]
               + space["stage_c_universe"]]
    body = {
        "kind": "V5_PRECALIBRATION_SCIENCE_FREEZE", "status": "FROZEN",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "stage_a_count": len(stage_a), "candidate_universe_count": len(all_ids),
        "stage_a_ids_sha256": sha256_text("\n".join(stage_a)),
        "candidate_universe_ids_sha256": sha256_text("\n".join(all_ids)),
        "files_sha256": {rel: file_sha256(ROOT / rel) for rel in PINNED_FILES},
        "worker_permissions": {"partition": "DISCOVERY", "instruments": ["NQ", "ES"],
            "start": "2010-06-08", "end": "2018-12-31",
            "columns": ["open", "high", "low", "close", "volume", "symbol"],
            "reason": "CALIBRATION_NUISANCE_ACCESS"},
        "power_gate": {"all_null_worlds": 200, "null_reference_worlds": 500,
            "false_survivor_upper95_max": .10, "plateau_0p10_500_lower95_min": .70,
            "plateau_0p15_500_lower95_min": .90},
        "ledger_anchor_before_access": ledger.head(project.ledger_path),
        "preexisting_discovery_read_sequences": [r["seq"] for r in ledger.data_reads(project.ledger_path)
            if r.get("result") == "ALLOWED" and r.get("partition") == "DISCOVERY"],
        "preexisting_discovery_read_disclosure": "bootstrap structural counts and one-day isolation probe predate this freeze; no V5 strategy outcome was calculated",
        "discovery_search_authorized": False,
        "later_partitions_opened": False,
    }
    doc = {**body, "body_sha256": sha256_text(canonical_json(body))}
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    freeze_hash = file_sha256(path)
    ledger.append(project.ledger_path, "PRECALIBRATION_SCIENCE_FROZEN",
                  reason="scientific design frozen before nuisance access",
                  science_freeze_sha256=freeze_hash,
                  stage_a_ids_sha256=body["stage_a_ids_sha256"],
                  candidate_universe_ids_sha256=body["candidate_universe_ids_sha256"])
    state_path.write_text(json.dumps({"kind": "V5_CALIBRATION_ACCESS_STATE",
                                      "state": "ARMED", "science_freeze_sha256": freeze_hash},
                                     sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(freeze_hash)


if __name__ == "__main__":
    main()
