"""THE single data-access entry point for research code.

(Ported unchanged in behaviour from QuantLabV4 quantlab4/isolation/load_view.py; V5 changes: the
V5 logical partition names and LIVE_FORWARD. V4 history: adapted from quantlab3/data/loader.py. Kept: registry-only partitions, SHA-256
verification before use, refusal of the original full-history files, ledger record
written BEFORE bars are returned, no on-disk extract cache. Changed for V4: requests
are LOGICAL (instrument, partition, start, end, columns); every argument is
validated and path-like input is refused; every refusal is ledgered too; volume and
all canonical columns are returned; the stage/registry/freeze state is fully
re-verified on every call.)

    md = load_view("NQ", "DISCOVERY", start="2012-01-01", end="2012-12-31",
                   columns=["open", "high", "low", "close", "volume", "symbol"])
    bars = md.bars()

Research code must never open parquet/CSV files itself (a test scans the source tree).
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as pads

from quantlab5.data.schema import ALL_COLUMNS, TS, Bars, bars_from_frame
from quantlab5.data.sessions import session_start_utc_ns
from quantlab5.data.validation import DataIntegrityError, quick_check
from quantlab5.isolation import ledger
from quantlab5.isolation.stage_gate import StageViolation, authorize, current_stage
from quantlab5.project import Project, default_project
from quantlab5.util.hashing import file_sha256

_NAME = re.compile(r"^[A-Z][A-Z0-9_]{0,39}$")
_COL = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LOGICAL_PARTITIONS = ("DISCOVERY", "VALIDATION", "HISTORICAL_AUDIT_1", "HISTORICAL_AUDIT_2", "LIVE_FORWARD")


class AccessRefused(StageViolation):
    """load_view refused the request (the refusal is in the ledger)."""


@dataclass
class MarketData:
    frame: pd.DataFrame
    instrument: str
    partition: str
    start: str
    end: str
    columns: list[str]
    stage: str
    data_sha256: str
    partition_sha256: str
    ledger_seq: int
    meta: dict = field(default_factory=dict)

    def bars(self) -> Bars:
        return bars_from_frame(self.frame, self.instrument, source=f"real:{self.partition}")


def _refuse(project: Project, req: dict, reason: str, stage: str | None = None):
    ledger.append(project.ledger_path, "DATA_READ", ledger.REFUSED, reason, stage=stage, **req)
    raise AccessRefused(f"REFUSED {req.get('instrument')}/{req.get('partition')}: {reason}")


def _as_str(x) -> str:
    return x if isinstance(x, str) else repr(x)


def _parse_date(x, what: str) -> date | None:
    if x is None:
        return None
    if isinstance(x, date):
        return x
    if isinstance(x, str) and _DATE.match(x):
        return date.fromisoformat(x)
    raise ValueError(f"{what} must be YYYY-MM-DD, got {x!r}")


def _within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def load_view(instrument, partition, start=None, end=None, columns=None, *, project: Project | None = None,
              purpose: str = "") -> MarketData:
    project = project or default_project()
    cols_req = None if columns is None else list(columns) if isinstance(columns, (list, tuple)) else [columns]
    req = {"instrument": _as_str(instrument)[:80], "partition": _as_str(partition)[:120],
           "columns": None if cols_req is None else [_as_str(c)[:60] for c in cols_req],
           "requested_start": None if start is None else _as_str(start)[:40],
           "requested_end": None if end is None else _as_str(end)[:40], "purpose": str(purpose)[:200]}

    # 1. argument validation -- anything path-like or malformed is refused outright
    if not isinstance(instrument, str) or not _NAME.match(instrument):
        _refuse(project, req, "instrument is not a plain symbol (paths and expressions are refused)")
    if not isinstance(partition, str) or partition not in LOGICAL_PARTITIONS:
        _refuse(project, req, f"partition must be one of {LOGICAL_PARTITIONS} (raw/full-history paths are refused)")
    if cols_req is not None:
        bad = [c for c in cols_req if not isinstance(c, str) or not _COL.match(c) or c not in ALL_COLUMNS]
        if bad:
            _refuse(project, req, f"unknown or invalid columns {bad}")
    try:
        d0, d1 = _parse_date(start, "start"), _parse_date(end, "end")
    except ValueError as e:
        _refuse(project, req, str(e))

    # 2. stage authorisation (re-verifies stage state, ledger chain, registry pin and freezes)
    try:
        from quantlab5.project import ROOT as V5_ROOT
        is_v54 = (project.root.resolve() == V5_ROOT.resolve()
                  and str(purpose).startswith("V5_4_"))
        if is_v54:
            stage = current_stage(project)
            from quantlab5.v54.access import authorize as authorize_v54
            ok, why = authorize_v54(project, purpose, partition, instrument,
                                    start, end, cols_req, stage)
        else:
            stage, ok, why = authorize(project, partition)
    except StageViolation as e:
        _refuse(project, req, f"stage state invalid: {e}")
    if not ok:
        _refuse(project, req, why, stage)

    # Actual V5 research is held behind the final immutable preregistration.
    # The stage machine alone permits DISCOVERY immediately after bootstrap,
    # which is useful for structural checks but too permissive for strategy
    # research before the executable synthetic calibration is complete.
    from quantlab5.project import ROOT as V5_ROOT
    if project.root.resolve() == V5_ROOT.resolve():
        from quantlab5.direct_null.access import active as direct_null_active
        from quantlab5.v5_1.access import active as v5_1_calibration_active
        from quantlab5.isolation.calibration_gate import calibration_access_active
        calibration = calibration_access_active()
        if direct_null_active():
            expected_columns = ["open", "high", "low", "close", "volume", "symbol"]
            if (stage != "DISCOVERY" or partition != "DISCOVERY"
                    or instrument not in ("NQ", "ES")
                    or str(start) != "2010-06-08" or str(end) != "2018-12-31"
                    or cols_req != expected_columns
                    or purpose != "DIRECT_NULL_STRUCTURE_ACCESS"):
                _refuse(project, req, "direct-null worker may read only full DISCOVERY NQ/ES OHLCV", stage)
            why = "DIRECT_NULL_STRUCTURE_ACCESS"
        elif v5_1_calibration_active():
            expected_columns = ["open", "high", "low", "close", "volume", "symbol"]
            if (stage != "DISCOVERY" or partition != "DISCOVERY"
                    or instrument not in ("NQ", "ES")
                    or str(start) != "2010-06-08" or str(end) != "2018-12-31"
                    or cols_req != expected_columns
                    or purpose != "V5_1_CALIBRATION_NUISANCE_ACCESS"):
                _refuse(project, req, "V5.1 worker may read only full DISCOVERY NQ/ES OHLCV", stage)
            why = "V5_1_CALIBRATION_NUISANCE_ACCESS"
        elif calibration:
            expected_columns = ["open", "high", "low", "close", "volume", "symbol"]
            if (stage != "DISCOVERY" or partition != "DISCOVERY"
                    or instrument not in ("NQ", "ES")
                    or str(start) != "2010-06-08" or str(end) != "2018-12-31"
                    or cols_req != expected_columns
                    or purpose != "CALIBRATION_NUISANCE_ACCESS"):
                _refuse(project, req, "calibration worker may read only full DISCOVERY NQ/ES OHLCV", stage)
            why = "CALIBRATION_NUISANCE_ACCESS"
        elif is_v54:
            # authorize_v54 verified the separate tagged phase and exact scope.
            pass
        else:
            from quantlab5.isolation.prereg_gate import prereg_ready
            ready, reason = prereg_ready(project.root)
            if not ready:
                _refuse(project, req, reason, stage)
            why = "REAL_DISCOVERY_SEARCH_ACCESS" if partition == "DISCOVERY" else why

    if partition == "LIVE_FORWARD":
        return _load_forward(project, req, stage, why, instrument, d0, d1, cols_req)

    # 3. registry record and physical location
    reg = project.partitions()["registry"]
    recs = [r for r in reg["partitions"] if r["instrument"] == instrument and r["partition"] == partition]
    if len(recs) != 1:
        _refuse(project, req, f"{instrument}/{partition} is not exactly one registered partition", stage)
    rec = recs[0]
    path = Path(rec["path"])
    rp = path.resolve()
    base = (project.discovery_dir if partition == "DISCOVERY" else project.vault / partition).resolve()
    if path.is_symlink() or not _within(rp, base) or rp.parent != base:
        _refuse(project, req, f"registered path escapes its partition directory ({base})", stage)
    if rp.name != f"{instrument}_{partition}.parquet":
        _refuse(project, req, "registered file name is not a V5 partition file", stage)
    raw = {p.resolve() for p in project.raw_sources().values()}
    raw_hashes = {s["sha256"] for s in reg.get("sources", {}).values()}
    if rp in raw or rec["sha256"] in raw_hashes:
        _refuse(project, req, "that is an original full-history source file; research never reads it", stage)
    if any(_within(rp, Path(d).resolve()) for d in project.paths.get("prior_lab_data") or ()):
        _refuse(project, req, "that file belongs to an earlier lab's data store; V5 never reads it", stage)

    # 4. requested range must lie inside the partition
    p0 = date.fromisoformat(rec["first_session"])
    p1 = date.fromisoformat(rec["last_session"])
    d0 = d0 or p0
    d1 = d1 or p1
    if d0 > d1:
        _refuse(project, req, "start is after end", stage)
    if d0 < p0 or d1 > p1:
        _refuse(project, req, f"requested sessions {d0}..{d1} fall outside {partition} ({p0}..{p1})", stage)

    # 5. partition hash
    if not rp.is_file():
        _refuse(project, req, "partition file is missing", stage)
    try:
        actual = file_sha256(rp)
    except PermissionError:
        _refuse(project, req, "operating system denied access to the partition file", stage)
    if actual != rec["sha256"]:
        _refuse(project, req, "partition SHA-256 does not match the registry -- partition altered or corrupted", stage)

    # 6. read exactly the requested sessions and columns
    lo, hi = session_start_utc_ns(d0), session_start_utc_ns(d1 + timedelta(days=1))
    want = list(ALL_COLUMNS) if cols_req is None else [TS] + [c for c in cols_req if c != TS]
    dset = pads.dataset(str(rp), format="parquet")
    present = set(dset.schema.names)
    missing = [c for c in want if c not in present]
    if missing:
        _refuse(project, req, f"columns not present in the partition: {missing}", stage)
    ttype = dset.schema.field(TS).type
    flt = ((pads.field(TS) >= pa.scalar(lo, pa.timestamp("ns", "UTC")).cast(ttype))
           & (pads.field(TS) < pa.scalar(hi, pa.timestamp("ns", "UTC")).cast(ttype)))
    # dtypes come from the Arrow schema only: embedded pandas metadata differs between source files
    df = dset.to_table(columns=want, filter=flt).to_pandas(ignore_metadata=True)
    ts = pd.DatetimeIndex(df[TS]).tz_convert("UTC").as_unit("ns").asi8
    if len(ts) and (ts.min() < lo or ts.max() >= hi):
        _refuse(project, req, "post-read check: rows escaped the requested window", stage)
    if all(k in df for k in ("open", "high", "low", "close")):
        try:
            quick_check(instrument, ts, *(df[k].to_numpy("float64") for k in ("open", "high", "low", "close")),
                        df["volume"].to_numpy("float64") if "volume" in df else None)
        except DataIntegrityError as e:
            _refuse(project, req, f"integrity check failed: {e}", stage)
    hsh = hashlib.sha256(ts.tobytes())
    for k in want[1:]:
        hsh.update(pd.util.hash_pandas_object(df[k], index=False).to_numpy().tobytes())
    data_sha = hsh.hexdigest()

    # 7. ledger BEFORE returning
    rec_l = ledger.append(project.ledger_path, "DATA_READ", ledger.ALLOWED, why, stage=stage,
                          **{**req, "requested_start": str(d0), "requested_end": str(d1)},
                          rows=int(len(df)), partition_sha256=rec["sha256"], data_sha256=data_sha)
    return MarketData(frame=df, instrument=instrument, partition=partition, start=str(d0), end=str(d1),
                      columns=want, stage=stage, data_sha256=data_sha, partition_sha256=rec["sha256"],
                      ledger_seq=int(rec_l["seq"]))


def _load_forward(project, req, stage, why, instrument, d0, d1, cols_req) -> MarketData:
    from quantlab5.isolation.forward import accepted_records
    try:
        recs = accepted_records(project, instrument)
    except StageViolation as e:
        _refuse(project, req, str(e), stage)
    if not recs:
        _refuse(project, req, "no forward data has been accepted for this instrument", stage)
    want = list(ALL_COLUMNS) if cols_req is None else [TS] + [c for c in cols_req if c != TS]
    frames = []
    for r in recs:
        p = (project.forward_accepted / r["file"]).resolve()
        if p.parent != project.forward_accepted.resolve() or file_sha256(p) != r["sha256"]:
            _refuse(project, req, f"accepted forward file {r['file']} is altered or misplaced", stage)
        frames.append(pads.dataset(str(p), format="parquet").to_table(columns=want).to_pandas(ignore_metadata=True))
    df = pd.concat(frames, ignore_index=True)
    ts = pd.DatetimeIndex(df[TS]).tz_convert("UTC").as_unit("ns").asi8
    lo = session_start_utc_ns(d0) if d0 else np.iinfo(np.int64).min
    hi = session_start_utc_ns(d1 + timedelta(days=1)) if d1 else np.iinfo(np.int64).max
    df = df.loc[(ts >= lo) & (ts < hi)].reset_index(drop=True)
    hsh = hashlib.sha256()
    for k in want:
        hsh.update(pd.util.hash_pandas_object(df[k], index=False).to_numpy().tobytes())
    rec_l = ledger.append(project.ledger_path, "DATA_READ", ledger.ALLOWED, why, stage=stage, **req,
                          rows=int(len(df)), data_sha256=hsh.hexdigest(),
                          forward_files=[r["file"] for r in recs])
    return MarketData(df, instrument, "LIVE_FORWARD", str(d0), str(d1), want, stage, hsh.hexdigest(),
                      "forward-manifest", int(rec_l["seq"]))


def load_bars(instrument: str, partition: str, start=None, end=None, *, project: Project | None = None,
              purpose: str = "") -> Bars:
    md = load_view(instrument, partition, start, end,
                   columns=["open", "high", "low", "close", "volume", "symbol"], project=project, purpose=purpose)
    return md.bars()
