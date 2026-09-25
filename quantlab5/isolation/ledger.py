"""Append-only, hash-chained data-access ledger.

(Adapted from quantlab3/data/ledger.py. V4 changes: the required V4 record fields,
a sequence number, `previous_record_hash` / `record_hash` naming, an exclusive
lock around each append so parallel workers cannot interleave or fork the chain,
integrity check of the current head before every append, and head anchors that
freezes pin so that truncation after a freeze is also detectable.)

Every market-data read attempt through quantlab5.isolation.load_view appends one
record -- ALLOWED or REFUSED -- and ALLOWED data is only returned after its record
has been durably written. If the ledger cannot be written, the read fails.

record_hash = SHA-256(canonical_json(record without record_hash)), and each record
carries the previous record's hash, so editing, deleting, reordering or inserting
any line breaks `verify`.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from quantlab5.util.hashing import canonical_json, sha256_text

GENESIS = "0" * 64
ALLOWED, REFUSED, INFO = "ALLOWED", "REFUSED", "INFO"
_LOCK_TIMEOUT_S = 60.0
_STALE_LOCK_S = 300.0


class LedgerError(Exception):
    """The ledger is missing, unwritable, locked, or its hash chain is broken."""


def _record_hash(rec: dict) -> str:
    return sha256_text(canonical_json({k: v for k, v in rec.items() if k != "record_hash"}))


class _Lock:
    def __init__(self, path: Path):
        self.lock = Path(str(path) + ".lock")
        self.fd = None

    def __enter__(self):
        t0 = time.monotonic()
        while True:
            try:
                self.fd = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.fd, str(os.getpid()).encode())
                return self
            except (FileExistsError, PermissionError):
                # Windows raises PermissionError while another writer's lock file is pending deletion
                try:
                    if time.time() - self.lock.stat().st_mtime > _STALE_LOCK_S:
                        self.lock.unlink()      # a crashed writer; the chain check below still guards content
                        continue
                except (FileNotFoundError, PermissionError):
                    pass
                if time.monotonic() - t0 > _LOCK_TIMEOUT_S:
                    raise LedgerError(f"ledger lock {self.lock} held for over {_LOCK_TIMEOUT_S}s")
                time.sleep(0.01)

    def __exit__(self, *exc):
        if self.fd is not None:
            os.close(self.fd)
        try:
            self.lock.unlink()
        except FileNotFoundError:
            pass


def _tail_record(path: Path) -> dict | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        pos = f.tell()
        buf = b""
        while pos > 0:
            step = min(8192, pos)
            pos -= step
            f.seek(pos)
            buf = f.read(step) + buf
            lines = buf.strip().splitlines()
            if len(lines) > 1 or pos == 0:
                return json.loads(lines[-1])
    return None


def append(path: Path, event: str, result: str = INFO, reason: str = "", **fields) -> dict:
    """Append one record under an exclusive lock. Raises LedgerError if it cannot be durably written."""
    path = Path(path)
    if not path.parent.exists():
        raise LedgerError(f"ledger directory {path.parent} does not exist")
    if result not in (ALLOWED, REFUSED, INFO):
        raise LedgerError(f"invalid result {result!r}")
    with _Lock(path):
        last = _tail_record(path)
        if last is not None and _record_hash(last) != last.get("record_hash"):
            raise LedgerError("the ledger's last record fails its own hash: the ledger was edited")
        rec = {
            "seq": 0 if last is None else int(last["seq"]) + 1,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "result": result,
            "reason": reason,
            **fields,
            "command": " ".join(sys.argv)[:500],
            "pid": os.getpid(),
            "user": os.environ.get("USERNAME") or os.environ.get("USER"),
            "host": socket.gethostname(),
            "previous_record_hash": GENESIS if last is None else last["record_hash"],
        }
        rec["record_hash"] = _record_hash(rec)
        try:
            with open(path, "a", encoding="utf-8", newline="\n") as f:
                f.write(canonical_json(rec) + "\n")
                f.flush()
                os.fsync(f.fileno())
        except OSError as e:
            raise LedgerError(f"cannot write data-access ledger {path}: {e}") from e
    return rec


def read(path: Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def verify(path: Path, anchor: dict | None = None) -> tuple[bool, str]:
    """Verify the whole chain; optionally that it still contains `anchor` = {"seq", "record_hash"}."""
    prev = GENESIS
    try:
        recs = read(path)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return False, f"ledger is not valid JSONL: {e}"
    for i, rec in enumerate(recs):
        if rec.get("seq") != i:
            return False, f"line {i + 1}: sequence number {rec.get('seq')} != {i} (deleted/inserted record)"
        if rec.get("previous_record_hash") != prev:
            return False, f"line {i + 1}: previous_record_hash does not match the previous record"
        if _record_hash(rec) != rec.get("record_hash"):
            return False, f"line {i + 1}: record hash mismatch (record edited)"
        prev = rec["record_hash"]
    if anchor is not None and int(anchor["seq"]) >= 0:
        s = int(anchor["seq"])
        if s >= len(recs):
            return False, f"ledger truncated: anchor seq {s} but only {len(recs)} records"
        if recs[s]["record_hash"] != anchor["record_hash"]:
            return False, f"record {s} differs from the anchored hash"
    return True, f"ok ({len(recs)} records)"


def head(path: Path) -> dict:
    """Anchor for freezes: the sequence number and hash of the current last record."""
    last = _tail_record(Path(path))
    if last is None:
        return {"seq": -1, "record_hash": GENESIS}
    return {"seq": int(last["seq"]), "record_hash": last["record_hash"]}


def data_reads(path: Path) -> list[dict]:
    """Research-API read attempts (allowed and refused)."""
    return [r for r in read(path) if r.get("event") == "DATA_READ"]
