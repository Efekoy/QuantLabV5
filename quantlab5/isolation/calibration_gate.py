"""One-shot, worker-only DISCOVERY nuisance access before final preregistration.

This is a protocol guard, not an OS security boundary. The main research loader
continues to require v5-prereg. A calibration run must be launched from the
hash-pinned worker and must start from an ARMED one-shot state.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import json
import os
from pathlib import Path
import sys

from quantlab5.project import ROOT
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text

FREEZE = "V5_PRECALIBRATION_SCIENCE_FREEZE.json"
STATE = "ledgers/CALIBRATION_ACCESS_STATE.json"
WORKER = "research/calibrate_v5_discovery_nuisance.py"
_active = ContextVar("v5_calibration_access", default=False)


def science_freeze_ready(root: Path = ROOT) -> tuple[bool, str]:
    path = root / FREEZE
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False, "precalibration science freeze is missing or invalid"
    if doc.get("kind") != "V5_PRECALIBRATION_SCIENCE_FREEZE" or doc.get("status") != "FROZEN":
        return False, "precalibration science freeze is not FROZEN"
    body = {k: v for k, v in doc.items() if k != "body_sha256"}
    if sha256_text(canonical_json(body)) != doc.get("body_sha256"):
        return False, "precalibration science freeze body hash mismatch"
    files = doc.get("files_sha256")
    required = {WORKER, "quantlab5/isolation/calibration_gate.py",
                "quantlab5/isolation/load_view.py", "quantlab5/v5/signals.py",
                "quantlab5/v5/candidate_inventory.py", "quantlab5/v5/market_search.py",
                "quantlab5/engine/execution.py", "quantlab5/engine/costs.py",
                "quantlab5/data/market.py", "quantlab5/data/sessions.py",
                "quantlab5/v5/calibrated_null.py", "quantlab5/v5/market_plant.py",
                "quantlab5/v5/validation.py", "quantlab5/v5/inference.py",
                "quantlab5/v5/risk_coverage.py", "research/run_v5_executable_calibration.py",
                "research/check_v5_nuisance_fit.py",
                "V5_PRECALIBRATION_SCIENCE_PROTOCOL.md",
                "V5_RESEARCH_PREREGISTRATION.md", "V5_STRATEGY_CATALOG.md",
                "V5_NULL_METHOD_REPORT.md", "V5_POWER_CALIBRATION_REPORT.md",
                "reports/V5_CANDIDATE_INVENTORY.json",
                "config/costs.yaml", "config/stage_policy.yaml"}
    if not isinstance(files, dict) or not required <= files.keys():
        return False, "precalibration science freeze lacks required code and rules"
    for rel, expected in files.items():
        relative = Path(rel)
        if relative.is_absolute() or ".." in relative.parts or not isinstance(expected, str):
            return False, "precalibration science freeze contains an unsafe path"
        source = root / relative
        if not source.is_file() or file_sha256(source) != expected:
            return False, f"precalibration pinned file mismatch: {rel}"
    from quantlab5.search.candidate_id import candidate_id
    from quantlab5.v5.candidate_inventory import inventory
    universe = inventory()
    stage_a_ids = [candidate_id(s) for s in universe["stage_a"]]
    all_ids = [candidate_id(s) for s in (universe["stage_a"] + universe["stage_b"]
                                        + universe["stage_c_universe"])]
    if (doc.get("stage_a_ids_sha256") != sha256_text("\n".join(stage_a_ids))
            or doc.get("candidate_universe_ids_sha256") != sha256_text("\n".join(all_ids))):
        return False, "precalibration candidate IDs are not pinned to executable grammar"
    from quantlab5.isolation import ledger
    anchor = doc.get("ledger_anchor_before_access")
    if not isinstance(anchor, dict):
        return False, "precalibration ledger anchor is missing"
    ledger_path = root / "ledgers/DATA_ACCESS_LEDGER.jsonl"
    ok, reason = ledger.verify(ledger_path, anchor=anchor)
    if not ok:
        return False, f"precalibration ledger invalid: {reason}"
    freeze_hash = file_sha256(path)
    if not any(r.get("event") == "PRECALIBRATION_SCIENCE_FROZEN"
               and r.get("science_freeze_sha256") == freeze_hash
               and r.get("seq", -1) > anchor["seq"] for r in ledger.read(ledger_path)):
        return False, "precalibration freeze is not anchored in the access ledger"
    return True, "precalibration science freeze verifies"


def calibration_access_active() -> bool:
    return bool(_active.get())


def _write_state(path: Path, state: str, freeze_hash: str) -> None:
    payload = {"kind": "V5_CALIBRATION_ACCESS_STATE", "state": state,
               "science_freeze_sha256": freeze_hash}
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


@contextmanager
def calibration_scope(root: Path = ROOT):
    """Enable exactly one hash-pinned worker run; a crash remains fail-closed."""
    if root.resolve() != ROOT.resolve():
        raise RuntimeError("calibration scope is only for the actual V5 project")
    ok, reason = science_freeze_ready(root)
    if not ok:
        raise RuntimeError(reason)
    if Path(sys.argv[0]).resolve() != (root / WORKER).resolve():
        raise RuntimeError("calibration access requires the pinned worker entry point")
    state_path = root / STATE
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise RuntimeError("calibration access state is missing or invalid") from None
    freeze_hash = file_sha256(root / FREEZE)
    if state != {"kind": "V5_CALIBRATION_ACCESS_STATE", "state": "ARMED",
                  "science_freeze_sha256": freeze_hash}:
        raise RuntimeError("calibration access is not ARMED for this freeze")
    _write_state(state_path, "ACTIVE", freeze_hash)
    token = _active.set(True)
    try:
        yield
    finally:
        _active.reset(token)
        # A failed worker stays ACTIVE and requires a separate incident audit.


def close_calibration_scope(root: Path = ROOT) -> None:
    if not calibration_access_active():
        raise RuntimeError("no active calibration scope")
    path = root / STATE
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("state") != "ACTIVE" or state.get("science_freeze_sha256") != file_sha256(root / FREEZE):
        raise RuntimeError("calibration access state changed during worker run")
    _write_state(path, "COMPLETE", state["science_freeze_sha256"])
