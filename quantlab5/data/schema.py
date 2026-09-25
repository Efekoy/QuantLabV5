"""Canonical market-data schema and the in-memory `Bars` container.

VOLUME IS FIRST-CLASS. It is part of the required schema, it is carried through
every transformation (partitioning, loading, resampling, null generation), and a
bar set without a valid volume column is rejected.

Two representations:
  * a pandas DataFrame with the canonical column names (what load_view returns);
  * `Bars`: read-only numpy arrays for the engine / features / nulls. Real data and
    null/synthetic data are both turned into `Bars` by the same constructor, which is
    what lets them enter the same evaluation pipeline.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, replace

import numpy as np
import pandas as pd

from quantlab5.data.sessions import session_fields
from quantlab5.data.validation import quick_check

TS = "ts_event"

# name -> (Arrow type name, required). Matches the Databento-derived source files exactly.
CANONICAL_SCHEMA: dict[str, tuple[str, bool]] = {
    "ts_event": ("timestamp[ns, tz=UTC]", True),
    "open": ("double", True),
    "high": ("double", True),
    "low": ("double", True),
    "close": ("double", True),
    "volume": ("int64", True),
    "symbol": ("string", True),
    "instrument_id": ("int64", False),
    "rtype": ("int16", False),
    "publisher_id": ("int16", False),
    "roll_session": ("string", False),
    "roll_boundary": ("bool", False),
    "duplicate_timestamp": ("bool", False),
    "source_duplicate_count": ("int32", False),
}
REQUIRED_COLUMNS = tuple(k for k, (_t, req) in CANONICAL_SCHEMA.items() if req)
ALL_COLUMNS = tuple(CANONICAL_SCHEMA)
PRICE_COLUMNS = ("open", "high", "low", "close")


class SchemaError(Exception):
    """Market data does not match the canonical schema."""


def check_arrow_schema(schema) -> list[str]:
    """Compare a pyarrow schema to the canonical schema. Returns a list of problems."""
    problems = []
    names = set(schema.names)
    for col, (typ, req) in CANONICAL_SCHEMA.items():
        if col not in names:
            if req:
                problems.append(f"missing required column {col}")
            continue
        actual = str(schema.field(col).type)
        ok = actual == typ or (typ == "string" and actual in ("string", "large_string"))
        if not ok:
            problems.append(f"column {col}: type {actual}, expected {typ}")
    return problems


@dataclass
class Bars:
    """Read-only 1-minute bars for one instrument (real, synthetic or null)."""
    instrument: str
    ts: np.ndarray        # int64 UTC ns, bar START
    tmin: np.ndarray      # int64 UTC minutes since epoch
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    v: np.ndarray         # float64 volume (NaN = missing; never silently zero-filled)
    seg: np.ndarray       # int32 contract segment id (increments at each roll)
    sday: np.ndarray      # int32 session END date, days since epoch
    sm: np.ndarray        # int16 session minute (0 = 18:00 New York)
    source: str = "unknown"   # "real:<partition>" | "synthetic" | "null:<generator>"
    meta: dict = field(default_factory=dict)

    @property
    def n(self) -> int:
        return len(self.c)

    def content_hash(self) -> str:
        h = hashlib.sha256()
        for a in (self.ts, self.o, self.h, self.l, self.c, self.v, self.seg):
            h.update(np.ascontiguousarray(a).tobytes())
        return h.hexdigest()

    def with_prices(self, o=None, h=None, l=None, c=None, v=None, source: str | None = None) -> "Bars":
        """A new Bars with replaced price/volume arrays (timestamps/sessions/segments kept)."""
        new = replace(self, o=_ro(np.array(self.o if o is None else o, dtype=np.float64)),
                      h=_ro(np.array(self.h if h is None else h, dtype=np.float64)),
                      l=_ro(np.array(self.l if l is None else l, dtype=np.float64)),
                      c=_ro(np.array(self.c if c is None else c, dtype=np.float64)),
                      v=_ro(np.array(self.v if v is None else v, dtype=np.float64)),
                      source=source or self.source, meta=dict(self.meta))
        quick_check(new.instrument, new.ts, new.o, new.h, new.l, new.c, new.v)
        return new

    def slice(self, a: int, b: int) -> "Bars":
        return replace(self, ts=self.ts[a:b], tmin=self.tmin[a:b], o=self.o[a:b], h=self.h[a:b],
                       l=self.l[a:b], c=self.c[a:b], v=self.v[a:b], seg=self.seg[a:b],
                       sday=self.sday[a:b], sm=self.sm[a:b], meta=dict(self.meta))


def _ro(a: np.ndarray) -> np.ndarray:
    """Read-only view. Callers pass arrays Bars owns (copied on construction)."""
    a = np.asarray(a).view()
    a.setflags(write=False)
    return a


def segments_from_symbols(symbol) -> np.ndarray:
    con = np.asarray(symbol).astype(str)
    ch = np.zeros(len(con), dtype=bool)
    if len(con):
        ch[1:] = con[1:] != con[:-1]
    return np.cumsum(ch).astype(np.int32)


def bars_from_arrays(instrument: str, ts_ns, o, h, l, c, v=None, symbol=None, source: str = "synthetic",
                     check: bool = True) -> Bars:
    """The ONE constructor for Bars (used for real, synthetic and null data alike)."""
    ts = np.array(ts_ns, dtype="int64", copy=True)
    o, h, l, c = (np.array(x, dtype="float64", copy=True) for x in (o, h, l, c))
    vv = np.full(len(ts), np.nan) if v is None else np.array(v, dtype="float64", copy=True)
    if len(vv) != len(ts):
        raise SchemaError("volume length does not match timestamps")
    if check:
        quick_check(instrument, ts, o, h, l, c, vv)
    seg = segments_from_symbols(symbol) if symbol is not None else np.zeros(len(ts), np.int32)
    tmin, _loc, sday, sm = session_fields(ts)
    return Bars(instrument, _ro(ts), _ro(tmin), _ro(o), _ro(h), _ro(l), _ro(c), _ro(vv), _ro(seg),
                _ro(sday), _ro(sm), source=source)


def bars_from_frame(df: pd.DataFrame, instrument: str, source: str) -> Bars:
    missing = [k for k in REQUIRED_COLUMNS if k not in df.columns]
    if missing:
        raise SchemaError(f"cannot build Bars: missing {missing}")
    ts = pd.DatetimeIndex(df[TS]).tz_convert("UTC").as_unit("ns").asi8
    return bars_from_arrays(instrument, ts, df["open"], df["high"], df["low"], df["close"],
                            df["volume"].astype("float64"), df["symbol"], source=source)
