"""One-shot V5.1 nuisance access after its separate protocol freeze."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import json
import os
from pathlib import Path
import sys

from quantlab5.project import ROOT
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text

FREEZE = ROOT / "V5_1_NUISANCE_PROTOCOL_FREEZE.json"
STATE = ROOT / "ledgers/V5_1_CALIBRATION_ACCESS_STATE.json"
LEDGER = ROOT / "ledgers/V5_1_DATA_ACCESS_LEDGER.jsonl"
WORKER = ROOT / "research/calibrate_v5_1_nuisance.py"
_active = ContextVar("v5_1_nuisance_access", default=False)


def freeze_ready() -> tuple[bool, str]:
    try:
        doc = json.loads(FREEZE.read_text(encoding="utf-8"))
        if doc.get("kind") != "V5_1_NUISANCE_PROTOCOL_FREEZE" or doc.get("status") != "FROZEN":
            return False, "V5.1 nuisance protocol is not frozen"
        body = {k: v for k, v in doc.items() if k != "body_sha256"}
        if sha256_text(canonical_json(body)) != doc.get("body_sha256"):
            return False, "V5.1 freeze body hash mismatch"
        for rel, expected in doc["files_sha256"].items():
            p = Path(rel)
            if p.is_absolute() or ".." in p.parts or file_sha256(ROOT / p) != expected:
                return False, f"V5.1 pinned file mismatch: {rel}"
        from quantlab5.search.candidate_id import candidate_id
        from quantlab5.v5.candidate_inventory import inventory
        inv = inventory()
        stage_a = [candidate_id(x) for x in inv["stage_a"]]
        universe = [candidate_id(x) for x in (inv["stage_a"] + inv["stage_b"]
                                               + inv["stage_c_universe"])]
        if (doc.get("stage_a_ids_sha256") != sha256_text("\n".join(stage_a))
                or doc.get("candidate_universe_ids_sha256") != sha256_text("\n".join(universe))):
            return False, "V5.1 candidate IDs differ from the frozen grammar"
        from quantlab5.isolation import ledger
        ok, reason = ledger.verify(LEDGER, anchor=doc["ledger_anchor_before_access"])
        if not ok:
            return False, reason
        if not any(r.get("event") == "V5_1_NUISANCE_PROTOCOL_FROZEN"
                   and r.get("freeze_sha256") == file_sha256(FREEZE)
                   for r in ledger.read(LEDGER)):
            return False, "V5.1 freeze is not ledgered"
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return False, f"V5.1 freeze invalid: {exc}"
    return True, "V5.1 nuisance protocol verifies"


def active() -> bool:
    return bool(_active.get())


def _state(value: str, freeze_hash: str) -> None:
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"state": value, "freeze_sha256": freeze_hash},
                              sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, STATE)


@contextmanager
def scope():
    ok, reason = freeze_ready()
    if not ok:
        raise RuntimeError(reason)
    if Path(sys.argv[0]).resolve() != WORKER.resolve():
        raise RuntimeError("V5.1 nuisance access requires the pinned worker")
    freeze_hash = file_sha256(FREEZE)
    if json.loads(STATE.read_text(encoding="utf-8")) != {"state": "ARMED", "freeze_sha256": freeze_hash}:
        raise RuntimeError("V5.1 nuisance access is not ARMED")
    _state("ACTIVE", freeze_hash)
    token = _active.set(True)
    try:
        yield
    finally:
        _active.reset(token)
        # Fail closed on exception; no automatic retry.


def close() -> None:
    if not active():
        raise RuntimeError("V5.1 nuisance scope is not active")
    freeze_hash = file_sha256(FREEZE)
    if json.loads(STATE.read_text(encoding="utf-8")) != {"state": "ACTIVE", "freeze_sha256": freeze_hash}:
        raise RuntimeError("V5.1 nuisance state changed during worker run")
    _state("COMPLETE", freeze_hash)
