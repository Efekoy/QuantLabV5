"""Frozen, one-shot direct-null structure access gate."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import json
import os
from pathlib import Path
import sys

from quantlab5.project import ROOT
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text

FREEZE = ROOT / "V5_DIRECT_NULL_PROTOCOL_FREEZE.json"
STATE = ROOT / "ledgers/V5_DIRECT_NULL_ACCESS_STATE.json"
LEDGER = ROOT / "ledgers/V5_DIRECT_NULL_ACCESS_LEDGER.jsonl"
WORKER = ROOT / "research/run_direct_null_study.py"
_active = ContextVar("v5_direct_null_access", default=False)


def freeze_ready() -> tuple[bool, str]:
    try:
        doc = json.loads(FREEZE.read_text(encoding="utf-8"))
        if doc.get("kind") != "V5_DIRECT_NULL_PROTOCOL_FREEZE" or doc.get("status") != "FROZEN":
            return False, "direct-null protocol is not frozen"
        body = {k: v for k, v in doc.items() if k != "body_sha256"}
        if sha256_text(canonical_json(body)) != doc.get("body_sha256"):
            return False, "direct-null freeze body hash mismatch"
        for rel, expected in doc["files_sha256"].items():
            p = Path(rel)
            if p.is_absolute() or ".." in p.parts or file_sha256(ROOT / p) != expected:
                return False, f"direct-null pinned file mismatch: {rel}"
        from quantlab5.isolation import ledger
        ok, reason = ledger.verify(LEDGER, doc["ledger_anchor_before_access"])
        if not ok:
            return False, reason
        from quantlab5.project import default_project
        ok, reason = ledger.verify(default_project().ledger_path,
                                   doc["main_ledger_anchor_before_access"])
        if not ok:
            return False, reason
        if not any(r.get("event") == "DIRECT_NULL_PROTOCOL_FROZEN"
                   and r.get("freeze_sha256") == file_sha256(FREEZE)
                   for r in ledger.read(LEDGER)):
            return False, "direct-null freeze is not ledgered"
        from quantlab5.search.candidate_id import candidate_id
        from quantlab5.v5.candidate_inventory import inventory
        inv = inventory()
        ids = [candidate_id(x) for x in inv["stage_a"]+inv["stage_b"]+inv["stage_c_universe"]]
        if sha256_text("\n".join(ids)) != doc["candidate_universe_ids_sha256"]:
            return False, "candidate grammar changed"
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return False, f"direct-null freeze invalid: {exc}"
    return True, "direct-null protocol verifies"


def active() -> bool:
    return bool(_active.get())


def _state(value: str, freeze_hash: str) -> None:
    temp = STATE.with_suffix(".tmp")
    temp.write_text(json.dumps({"state": value, "freeze_sha256": freeze_hash},
                               sort_keys=True, indent=2)+"\n", encoding="utf-8")
    os.replace(temp, STATE)


@contextmanager
def scope():
    ok, reason = freeze_ready()
    if not ok:
        raise RuntimeError(reason)
    if Path(sys.argv[0]).resolve() != WORKER.resolve():
        raise RuntimeError("direct-null access requires pinned worker")
    h = file_sha256(FREEZE)
    if json.loads(STATE.read_text(encoding="utf-8")) != {"state": "ARMED", "freeze_sha256": h}:
        raise RuntimeError("direct-null worker is not armed")
    _state("ACTIVE", h)
    token = _active.set(True)
    try:
        yield
    finally:
        _active.reset(token)


def close() -> None:
    if not active():
        raise RuntimeError("direct-null scope is not active")
    h = file_sha256(FREEZE)
    if json.loads(STATE.read_text(encoding="utf-8")) != {"state": "ACTIVE", "freeze_sha256": h}:
        raise RuntimeError("direct-null state changed")
    _state("COMPLETE", h)
