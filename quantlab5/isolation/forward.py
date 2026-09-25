"""LIVE_FORWARD: the forward inbox and the accepted-forward vault.

No historical data is ever assigned to LIVE_FORWARD. The mechanism is:

  1. New market data (a parquet file in the canonical schema) is dropped into
     <vault>/LIVE_FORWARD/inbox/ by whoever collects it.
  2. `ingest_forward` (privileged; run by the administrator / collection job) accepts
     it ONLY if a FINAL_COHORT_FREEZE has been pinned by the stage gate, and ONLY if
     EVERY row belongs to a session that STARTED at or after the freeze timestamp.
     A file with a single earlier row is rejected whole. Accepted files never overlap.
  3. Accepted files are copied to <vault>/LIVE_FORWARD/accepted/, set read-only, and
     recorded in a hash-chained FORWARD_MANIFEST.jsonl plus the main data-access ledger.
  4. Research reads LIVE_FORWARD only through load_view, and only in stage LIVE_FORWARD.

Until a final cohort is frozen, ingestion refuses everything: the inbox can receive
files, nothing can be accepted.
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from quantlab5.data.schema import TS, check_arrow_schema
from quantlab5.data.sessions import session_fields, session_start_utc_ns
from quantlab5.data.validation import DataIntegrityError, quick_check
from quantlab5.isolation import ledger
from quantlab5.isolation.manifests import make_read_only
from quantlab5.isolation.stage_gate import StageViolation, verified_state
from quantlab5.util.hashing import file_sha256


class ForwardRejected(StageViolation):
    """A forward file was not accepted."""


def manifest_path(project) -> Path:
    return project.vault / "LIVE_FORWARD" / "FORWARD_MANIFEST.jsonl"


def ensure_layout(project) -> None:
    for p in (project.forward_inbox, project.forward_accepted):
        p.mkdir(parents=True, exist_ok=True)


def freeze_timestamp_ns(project) -> int | None:
    st = verified_state(project)
    ts = st.get("final_cohort_freeze_utc")
    if not st["freezes"].get("final_cohort") or not ts:
        return None
    return int(pd.Timestamp(datetime.fromisoformat(ts)).tz_convert("UTC").value)


def _reject(project, instrument, src: Path, reason: str):
    ledger.append(project.ledger_path, "FORWARD_INGEST", ledger.REFUSED, reason, instrument=instrument,
                  source_file=src.name)
    raise ForwardRejected(reason)


def accepted_records(project, instrument: str | None = None) -> list[dict]:
    mp = manifest_path(project)
    ok, msg = ledger.verify(mp)
    if not ok:
        raise StageViolation(f"FORWARD_MANIFEST failed verification: {msg}")
    recs = [r for r in ledger.read(mp) if r.get("event") == "FORWARD_ACCEPTED"]
    return [r for r in recs if instrument is None or r["instrument"] == instrument]


def ingest_forward(project, instrument: str, src: Path) -> dict:
    src = Path(src)
    freeze_ns = freeze_timestamp_ns(project)
    if freeze_ns is None:
        _reject(project, instrument, src, "no FINAL_COHORT_FREEZE has been pinned; LIVE_FORWARD is not open "
                                          "for ingestion")
    pf = pq.ParquetFile(src)
    problems = check_arrow_schema(pf.schema_arrow)
    if problems:
        _reject(project, instrument, src, f"schema problems: {problems}")
    df = pf.read().to_pandas()
    ts = pd.DatetimeIndex(df[TS]).tz_convert("UTC").as_unit("ns").asi8
    if len(ts) == 0:
        _reject(project, instrument, src, "empty file")
    try:
        quick_check(instrument, ts, *(df[k].to_numpy("float64") for k in ("open", "high", "low", "close")),
                    df["volume"].to_numpy("float64"))
    except DataIntegrityError as e:
        _reject(project, instrument, src, f"integrity: {e}")
    _t, _l, sday, _sm = session_fields(ts)
    first_session = sday.min().astype("int64").astype("datetime64[D]").astype(object)
    starts = np.array([session_start_utc_ns(d) for d in
                       np.unique(sday).astype("int64").astype("datetime64[D]").astype(object)])
    if (starts < freeze_ns).any():
        _reject(project, instrument, src, f"contains sessions that started before the final cohort freeze "
                                          f"(first session {first_session})")
    prior = accepted_records(project, instrument)
    if prior and ts.min() <= max(int(r["last_ts_ns"]) for r in prior):
        _reject(project, instrument, src, "overlaps previously accepted forward data")
    ensure_layout(project)
    dst = project.forward_accepted / f"{instrument}_LIVE_FORWARD_{len(prior):05d}.parquet"
    if dst.exists():
        _reject(project, instrument, src, f"{dst.name} already exists")
    shutil.copyfile(src, dst)
    make_read_only(dst)
    info = {"instrument": instrument, "file": dst.name, "sha256": file_sha256(dst), "rows": int(len(ts)),
            "first_ts_ns": int(ts.min()), "last_ts_ns": int(ts.max()),
            "first_session": str(first_session),
            "last_session": str(sday.max().astype("int64").astype("datetime64[D]"))}
    ledger.append(manifest_path(project), "FORWARD_ACCEPTED", ledger.INFO, "accepted", **info)
    ledger.append(project.ledger_path, "FORWARD_INGEST", ledger.ALLOWED, "accepted", **info)
    return info
