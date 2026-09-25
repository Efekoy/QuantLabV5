"""Shared fixtures. NOTHING here touches real market data, the real vault, the real
ledger or the real stage state.

(Ported from QuantLabV4 with V5 partition names.)

`synth_project` builds a throw-away V5 project: synthetic raw NQ/ES files in the exact
source schema (Databento metadata columns, roll_session, ...), partitioned by the REAL
bootstrap partitioner into a temp project (DISCOVERY) and a temp vault (sealed
partitions), then advanced BOOTSTRAP -> DISCOVERY by the real stage gate.

Compressed synthetic calendar (session dates):
  DISCOVERY            2020-08-03 .. 2020-10-30
  VALIDATION           2020-11-02 .. 2020-11-30
  HISTORICAL_AUDIT_1   2020-12-01 .. 2020-12-31
  HISTORICAL_AUDIT_2   2021-01-01 .. last complete session (file ends mid-session)
"""
from __future__ import annotations

import os
import shutil
import stat
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from quantlab5.project import Project  # noqa: E402

DEFS = {
    "DISCOVERY": {"first_session": "2020-08-03", "last_session": "2020-10-30", "location": "project"},
    "VALIDATION": {"first_session": "2020-11-02", "last_session": "2020-11-30", "location": "vault"},
    "HISTORICAL_AUDIT_1": {"first_session": "2020-12-01", "last_session": "2020-12-31", "location": "vault"},
    "HISTORICAL_AUDIT_2": {"first_session": "2021-01-01", "last_session": "LATEST_COMPLETE_SESSION_AT_BOOTSTRAP",
                          "location": "vault"},
    "LIVE_FORWARD": {"first_session": "AFTER_FINAL_COHORT_FREEZE", "last_session": "OPEN", "location": "vault"},
}
RAW_SCHEMA = pa.schema([("ts_event", pa.timestamp("ns", tz="UTC")), ("rtype", pa.int16()),
                        ("publisher_id", pa.int16()), ("instrument_id", pa.int64()), ("open", pa.float64()),
                        ("high", pa.float64()), ("low", pa.float64()), ("close", pa.float64()),
                        ("volume", pa.int64()), ("symbol", pa.string()), ("roll_session", pa.string()),
                        ("roll_boundary", pa.bool_()), ("duplicate_timestamp", pa.bool_()),
                        ("source_duplicate_count", pa.int32())])


def _rm_ro(func, path, _exc):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def rmtree(p: Path):
    if p.exists():
        shutil.rmtree(p, onexc=lambda f, p_, e: _rm_ro(f, p_, e))


def canonical_raw_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Add the source file's metadata columns to a synthetic (ts, ohlc, volume, symbol) frame."""
    from quantlab5.data.sessions import session_dates
    ts = pd.DatetimeIndex(df["ts_event"]).tz_convert("UTC").as_unit("ns").asi8
    sd = session_dates(ts).astype(str)
    sym = df["symbol"].astype(str).to_numpy()
    rb = np.r_[False, sym[1:] != sym[:-1]]
    return pd.DataFrame({
        "ts_event": pd.to_datetime(ts, utc=True), "rtype": np.full(len(df), 33, np.int16),
        "publisher_id": np.full(len(df), 1, np.int16), "instrument_id": np.full(len(df), 12345, np.int64),
        "open": df["open"].astype("float64"), "high": df["high"].astype("float64"),
        "low": df["low"].astype("float64"), "close": df["close"].astype("float64"),
        "volume": df["volume"].astype("int64"), "symbol": sym, "roll_session": sd, "roll_boundary": rb,
        "duplicate_timestamp": np.zeros(len(df), bool), "source_duplicate_count": np.ones(len(df), np.int32)})


def write_raw(path: Path, df: pd.DataFrame, row_group_size: int = 20000) -> None:
    tbl = pa.Table.from_pandas(canonical_raw_frame(df), schema=RAW_SCHEMA, preserve_index=False)
    pq.write_table(tbl, path, row_group_size=row_group_size)


_RAW_CACHE: dict = {}


def synthetic_raw(inst: str) -> pd.DataFrame:
    from quantlab5.synthetic.markets import synthetic_bars
    if inst not in _RAW_CACHE:
        seed, base = (11, 11000.0) if inst == "NQ" else (22, 3300.0)
        df = synthetic_bars(date(2020, 8, 3), date(2021, 1, 29), seed=seed, base=base, symbol=inst)
        # append a PARTIAL trailing session (2021-02-01: only the first two hours) -> must be excluded
        tail = synthetic_bars(date(2021, 2, 1), date(2021, 2, 1), seed=seed + 1, base=float(df["close"].iloc[-1]),
                              symbol=inst).iloc[:120]
        tail["symbol"] = df["symbol"].iloc[-1]
        _RAW_CACHE[inst] = pd.concat([df, tail], ignore_index=True)
    return _RAW_CACHE[inst]


def make_project(tmp: Path) -> Project:
    """A complete synthetic V5 project at stage DISCOVERY (real partitioner + real stage gate)."""
    import json
    import yaml
    from quantlab5.bootstrap.partitioner import partition_instrument
    from quantlab5.isolation.forward import ensure_layout
    from quantlab5.isolation.stage_gate import advance, init_state
    root, vault, rawdir = tmp / "proj", tmp / "vault", tmp / "raw"
    for d in ("config", "ledgers", "freezes", "provenance", "data/discovery"):
        (root / d).mkdir(parents=True, exist_ok=True)
    rawdir.mkdir(parents=True, exist_ok=True)
    for f in ("costs.yaml", "sessions.yaml", "stage_policy.yaml", "search.yaml", "nulls.yaml",
              "prop_profiles.yaml", "execution.yaml"):
        shutil.copy(PROJECT / "config" / f, root / "config" / f)
    raws = {}
    for inst in ("NQ", "ES"):
        raws[inst] = rawdir / f"{inst.lower()}_full.parquet"
        write_raw(raws[inst], synthetic_raw(inst))
    (root / "config" / "paths.yaml").write_text(yaml.safe_dump(
        {"vault": str(vault), "discovery_dir": "data/discovery", "raw_sources": {k: str(v) for k, v in raws.items()}}))
    parts = {"version": "test", "definitions": DEFS, "registry": None}
    (root / "config" / "partitions.json").write_text(json.dumps(parts))
    project = Project(root=root, vault=vault)
    for name in ("VALIDATION", "HISTORICAL_AUDIT_1", "HISTORICAL_AUDIT_2"):
        (vault / name).mkdir(parents=True, exist_ok=True)
    init_state(project)
    sources, records = {}, []
    for inst, raw in sorted(raws.items()):
        src, recs = partition_instrument(project, inst, raw, DEFS, "16:59", log=lambda *a: None)
        sources[inst] = src
        records += recs
    parts["registry"] = {"vault": str(vault), "sources": sources, "partitions": records}
    (root / "config" / "partitions.json").write_text(json.dumps(parts))
    ensure_layout(project)
    advance(project, "DISCOVERY")
    return project


@pytest.fixture(scope="session")
def shared_project(tmp_path_factory) -> Project:
    """Read-only use only (tests that do not change stage or files)."""
    return make_project(tmp_path_factory.mktemp("v5shared"))


@pytest.fixture()
def fresh_project(tmp_path) -> Project:
    """A brand-new synthetic project per test (for tests that tamper or change stage)."""
    return make_project(tmp_path)


@pytest.fixture()
def costs_cfg():
    import yaml
    return yaml.safe_load((PROJECT / "config" / "costs.yaml").read_text())


@pytest.fixture()
def sessions_cfg():
    import yaml
    return yaml.safe_load((PROJECT / "config" / "sessions.yaml").read_text())


def make_bars(closes, start="2020-10-05 09:30", tz="America/New_York", spread=0.5, opens=None,
              highs=None, lows=None):
    """Deterministic hand-made 1-minute bars (all inside one RTH session by default). (From V3 conftest.)"""
    n = len(closes)
    ts = pd.date_range(pd.Timestamp(start, tz=tz), periods=n, freq="min").tz_convert("UTC")
    c = np.asarray(closes, dtype=float)
    o = np.asarray(opens, dtype=float) if opens is not None else np.r_[c[0], c[:-1]]
    h = np.asarray(highs, dtype=float) if highs is not None else np.maximum(o, c) + spread
    l = np.asarray(lows, dtype=float) if lows is not None else np.minimum(o, c) - spread
    return ts.as_unit("ns").asi8, o, h, l, c
