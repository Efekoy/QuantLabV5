"""Hash-freeze direct-null protocol before any new DISCOVERY structure read."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import subprocess

from quantlab5.direct_null.access import FREEZE, LEDGER, STATE
from quantlab5.isolation import ledger
from quantlab5.project import ROOT, default_project
from quantlab5.search.candidate_id import candidate_id
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v5.candidate_inventory import inventory

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
    "V5_DIRECT_NULL_PROTOCOL.md", "quantlab5/direct_null/access.py",
    "quantlab5/direct_null/methods.py", "quantlab5/isolation/load_view.py",
    "research/run_direct_null_study.py", "research/freeze_direct_null_protocol.py",
    "research/check_v5_1_nuisance.py", "tests/test_direct_null_methods.py",
    "V5_1_NUISANCE_PROTOCOL_FREEZE.json",
    "V5_1_DISCOVERY_NUISANCE_CALIBRATION.json",
    "reports/V5_1_NUISANCE_TAPE.npz",
)


def main():
    if FREEZE.exists() or STATE.exists() or LEDGER.exists():
        raise RuntimeError("direct-null protocol/access already exists")
    protocol = (ROOT / "V5_DIRECT_NULL_PROTOCOL.md").read_text(encoding="utf-8")
    if "**Status: FROZEN DESIGN BEFORE DISCOVERY STRUCTURE ACCESS.**" not in protocol:
        raise RuntimeError("direct-null design not marked frozen")
    project = default_project()
    ok, reason = ledger.verify(project.ledger_path)
    if not ok:
        raise RuntimeError(reason)
    stage = json.loads(project.stage_state_path.read_text(encoding="utf-8"))["stage"]
    if stage != "DISCOVERY":
        raise RuntimeError("direct-null study requires DISCOVERY stage")
    prior = subprocess.run(["git", "diff", "--quiet", "v5.3-calibration-failed", "--",
                            *STRATEGY_FILES], cwd=ROOT).returncode
    if prior != 0:
        raise RuntimeError("strategy files differ from stopped V5.3")
    inv = inventory()
    ids = [candidate_id(x) for x in inv["stage_a"]+inv["stage_b"]+inv["stage_c_universe"]]
    created = ledger.append(LEDGER, "DIRECT_NULL_LEDGER_CREATED", reason="new controlled study")
    body = {
        "kind": "V5_DIRECT_NULL_PROTOCOL_FREEZE", "status": "FROZEN",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "predecessor_tag": "v5.3-calibration-failed",
        "candidate_universe_ids_sha256": sha256_text("\n".join(ids)),
        "files_sha256": {rel: file_sha256(ROOT / rel) for rel in FILES},
        "allowed_partition": "DISCOVERY", "allowed_instruments": ["NQ", "ES"],
        "allowed_session_dates": ["2010-06-08", "2018-12-31"],
        "allowed_columns": ["open", "high", "low", "close", "volume", "symbol"],
        "allowed_read_reason": "DIRECT_NULL_STRUCTURE_ACCESS",
        "method_priority": ["joint_bar_reflection", "joint_session_reflection"],
        "diagnostic_seeds": [9101, 9102, 9103], "diagnostic_worlds": 6,
        "nuisance_thresholds_source": "V5_1_NUISANCE_PROTOCOL_FREEZE.json",
        "new_directional_max": .01,
        "selection": "first method passing every structural, nuisance and zero-edge gate on all seeds",
        "stopping_rule": "if no method passes, stop with V5_DIRECT_NULL_STOP_REPORT.md",
        "main_ledger_anchor_before_access": ledger.head(project.ledger_path),
        "ledger_anchor_before_access": {"seq": created["seq"], "record_hash": created["record_hash"]},
        "real_strategy_search_authorized": False,
        "raw_discovery_export_authorized": False,
    }
    doc = {**body, "body_sha256": sha256_text(canonical_json(body))}
    FREEZE.write_text(json.dumps(doc, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    STATE.write_text(json.dumps({"state": "ARMED", "freeze_sha256": file_sha256(FREEZE)},
                                sort_keys=True, indent=2)+"\n", encoding="utf-8")
    ledger.append(LEDGER, "DIRECT_NULL_PROTOCOL_FROZEN", reason="prior to new DISCOVERY access",
                  freeze_sha256=file_sha256(FREEZE))
    print(file_sha256(FREEZE))


if __name__ == "__main__":
    main()
