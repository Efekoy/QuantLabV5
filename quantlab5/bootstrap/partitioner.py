"""PRIVILEGED one-time physical split of the raw NQ/ES files into V5 partitions.

(Ported from QuantLabV4 quantlab4/bootstrap/partitioner.py -- itself adapted from QuantLabV3
tools/partition_data.py. V5 changes: partition names only; the splitting logic is unchanged.)

This is the ONLY code in QuantLabV5 allowed to open the original full-history
source files. It streams each file row group by row group and inspects ONLY
timestamps (plus the source `roll_session` label, to cross-check the session rule).
Rows are copied unchanged -- every column, original order, original dtypes --
into exactly one partition file each. It computes and prints NOTHING about prices
or volumes: no returns, ranges, volatility, volume statistics, summaries or charts.
Source files are opened read-only and never modified.

Partitions are CME sessions (18:00 -> 17:00 New York, labelled by END date):

  DISCOVERY           2010-06-08 .. 2018-12-31   -> <project>/data/discovery/
  VALIDATION          2019-01-02 .. 2022-12-30   -> <vault>/VALIDATION/
  HISTORICAL_AUDIT_1  2023-01-03 .. 2025-12-31   -> <vault>/HISTORICAL_AUDIT_1/
  HISTORICAL_AUDIT_2  2026-01-02 .. latest COMPLETE session in the source file
                                                  -> <vault>/HISTORICAL_AUDIT_2/

A trailing incomplete session is excluded from every partition (counted only).
LIVE_FORWARD receives no historical rows.
"""
from __future__ import annotations

import os
import stat
from datetime import date
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from quantlab5.data.schema import TS, check_arrow_schema
from quantlab5.data.sessions import is_complete_final_session, session_fields
from quantlab5.util.hashing import file_sha256

HISTORICAL = ("DISCOVERY", "VALIDATION", "HISTORICAL_AUDIT_1", "HISTORICAL_AUDIT_2")
OPEN_ENDED = "HISTORICAL_AUDIT_2"          # ends at the latest complete session in the source file


class PartitionError(Exception):
    pass


def _d(s: str) -> date:
    return date.fromisoformat(s)


def _day_num(d: date) -> int:
    return (d - date(1970, 1, 1)).days


def _day_str(n: int) -> str:
    return str(np.datetime64(int(n), "D"))


def scan_timestamps(raw: Path, last_bar_clock: str) -> dict:
    """First pass: timestamp column only. Sortedness, uniqueness, session span, completeness."""
    pf = pq.ParquetFile(raw)
    prev = None
    n = 0
    first = last = None
    days: set[int] = set()
    for rg in range(pf.metadata.num_row_groups):
        ts = pf.read_row_group(rg, columns=[TS]).column(TS).cast(pa.int64()).to_numpy()
        if len(ts) == 0:
            continue
        if (np.diff(ts) <= 0).any() or (prev is not None and ts[0] <= prev):
            raise PartitionError(f"{raw.name}: timestamps not strictly increasing")
        if first is None:
            first = int(ts[0])
        prev = last = int(ts[-1])
        n += len(ts)
        days.update(np.unique(session_fields(ts)[2]).tolist())
    _t, _l, sd_first, _ = session_fields(np.array([first]))
    _t, _l, sd_last, _ = session_fields(np.array([last]))
    complete = is_complete_final_session(last, last_bar_clock)
    # the last complete session is the final session if complete, else the last EARLIER trading session
    last_complete = int(sd_last[0]) if complete else max(d for d in days if d < int(sd_last[0]))
    return {"rows": n, "first_ts_ns": first, "last_ts_ns": last, "first_session": _day_str(sd_first[0]),
            "last_session_in_file": _day_str(sd_last[0]), "final_session_complete": bool(complete),
            "last_complete_session_day": last_complete}


def _bounds(definitions: dict, last_complete_day: int) -> dict[str, tuple[int, int]]:
    out = {}
    for name in HISTORICAL:
        d = definitions[name]
        lo = _day_num(_d(d["first_session"]))
        hi = last_complete_day if name == OPEN_ENDED else _day_num(_d(d["last_session"]))
        out[name] = (lo, min(hi, last_complete_day))
    return out


def out_path(project, instrument: str, name: str) -> Path:
    base = project.discovery_dir if name == "DISCOVERY" else project.vault / name
    return base / f"{instrument}_{name}.parquet"


def partition_instrument(project, instrument: str, raw: Path, definitions: dict, last_bar_clock: str,
                         log=print) -> tuple[dict, list[dict]]:
    raw = Path(raw)
    raw_sha = file_sha256(raw)
    pf = pq.ParquetFile(raw)
    schema = pf.schema_arrow
    problems = check_arrow_schema(schema)
    if problems:
        raise PartitionError(f"{raw}: schema problems {problems}")
    scan = scan_timestamps(raw, last_bar_clock)
    bounds = _bounds(definitions, scan["last_complete_session_day"])

    writers, paths, stats = {}, {}, {}
    for name in HISTORICAL:
        dst = out_path(project, instrument, name)
        if dst.exists():
            raise PartitionError(f"refusing to overwrite {dst}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        paths[name] = dst
        writers[name] = pq.ParquetWriter(dst, schema, compression="zstd")
        stats[name] = {"rows": 0, "first_ts_ns": None, "last_ts_ns": None, "first_day": None, "last_day": None,
                       "sessions": set(), "roll_session_mismatch": 0}
    excluded = {"before_discovery": 0, "incomplete_final_session": 0, "unassigned": 0}
    try:
        for rg in range(pf.metadata.num_row_groups):
            tbl = pf.read_row_group(rg)
            ts = tbl.column(TS).cast(pa.int64()).to_numpy()
            _t, _l, sday, _sm = session_fields(ts)
            sday = sday.astype(np.int64)
            label_src = tbl.column("roll_session").to_numpy(zero_copy_only=False).astype(str) \
                if "roll_session" in tbl.schema.names else None
            assigned = np.zeros(len(ts), dtype=bool)
            for name, (lo, hi) in bounds.items():
                m = (sday >= lo) & (sday <= hi)
                if not m.any():
                    continue
                assigned |= m
                part = tbl.filter(pa.array(m))
                writers[name].write_table(part)
                s = stats[name]
                pts = ts[m]
                s["rows"] += int(m.sum())
                s["first_ts_ns"] = int(pts[0]) if s["first_ts_ns"] is None else s["first_ts_ns"]
                s["last_ts_ns"] = int(pts[-1])
                s["first_day"] = int(sday[m][0]) if s["first_day"] is None else s["first_day"]
                s["last_day"] = int(sday[m][-1])
                s["sessions"].update(np.unique(sday[m]).tolist())
                if label_src is not None:
                    comp = sday[m].astype("datetime64[D]").astype(str)
                    s["roll_session_mismatch"] += int((comp != label_src[m]).sum())
            first_disc = bounds["DISCOVERY"][0]
            excluded["before_discovery"] += int(((sday < first_disc) & ~assigned).sum())
            excluded["incomplete_final_session"] += int(((sday > scan["last_complete_session_day"])
                                                         & ~assigned).sum())
            excluded["unassigned"] += int((~assigned).sum())
    finally:
        for w in writers.values():
            w.close()
    placed = sum(s["rows"] for s in stats.values())
    if placed + excluded["unassigned"] != scan["rows"]:
        raise PartitionError(f"{instrument}: row accounting failed")
    if excluded["unassigned"] != excluded["before_discovery"] + excluded["incomplete_final_session"]:
        raise PartitionError(f"{instrument}: rows fell into a gap between partitions")

    records = []
    for name in HISTORICAL:
        dst, s = paths[name], stats[name]
        os.chmod(dst, stat.S_IREAD)
        d = definitions[name]
        lo, hi = bounds[name]
        rec = {
            "instrument": instrument, "partition": name,
            "location": "project" if name == "DISCOVERY" else "vault", "path": str(dst),
            "first_session": d["first_session"], "last_session": _day_str(hi),
            "first_data_session": _day_str(s["first_day"]) if s["first_day"] is not None else None,
            "last_data_session": _day_str(s["last_day"]) if s["last_day"] is not None else None,
            "first_timestamp_utc": str(np.datetime64(s["first_ts_ns"], "ns")) + "Z" if s["rows"] else None,
            "last_timestamp_utc": str(np.datetime64(s["last_ts_ns"], "ns")) + "Z" if s["rows"] else None,
            "rows": s["rows"], "sessions": len(s["sessions"]),
            "roll_session_label_mismatches": s["roll_session_mismatch"],
            "bytes": dst.stat().st_size, "sha256": file_sha256(dst),
        }
        records.append(rec)
        log(f"  {instrument} {name:25s} rows={rec['rows']:>9,}  sessions={rec['sessions']:>5}  "
            f"{rec['first_data_session']} .. {rec['last_data_session']}  sha256={rec['sha256'][:16]}")
    source = {"instrument": instrument, "path": str(raw.resolve()), "bytes": raw.stat().st_size,
              "sha256": raw_sha, "rows": scan["rows"],
              "schema": {f.name: str(f.type) for f in schema},
              "first_timestamp_utc": str(np.datetime64(scan["first_ts_ns"], "ns")) + "Z",
              "last_timestamp_utc": str(np.datetime64(scan["last_ts_ns"], "ns")) + "Z",
              "first_session": scan["first_session"], "last_session_in_file": scan["last_session_in_file"],
              "final_session_complete": scan["final_session_complete"],
              "last_complete_session": _day_str(scan["last_complete_session_day"]),
              "excluded_rows": excluded, "rows_placed": placed}
    if file_sha256(raw) != raw_sha:
        raise PartitionError(f"{raw} changed while it was being partitioned")
    return source, records
