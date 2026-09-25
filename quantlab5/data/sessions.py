"""Session arithmetic in America/New_York.

(Copied from quantlab3/data/sessions.py; unchanged except the V4 additions at the
end: session_dates, session_end_utc_ns, is_complete_final_session.)

Internal time representation (all int arrays, one value per bar):

    tmin   UTC minutes since the Unix epoch of the bar START
    local  New York wall-clock minutes since the epoch (DST applied)
    sday   session day: days since epoch of the date the CME session ENDS on
    sm     session minute: minutes since 18:00 NY that opened the session
           (18:00 -> 0, 09:30 -> 930, 16:00 -> 1320, 17:00 -> 1380)

Expressing clock times as session minutes makes Globex windows that cross
midnight contiguous, and removes every DST special case from strategy code:
DST lives only in the timezone conversion below.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

NY = "America/New_York"
SESSION_START_CLOCK = 18 * 60          # 18:00 New York
_SHIFT = 24 * 60 - SESSION_START_CLOCK  # 360 minutes: 18:00 -> next day's 00:00
EPOCH = date(1970, 1, 1)


def hhmm(s: str) -> int:
    """'09:30' -> 570 minutes after midnight."""
    h, m = str(s).split(":")
    h, m = int(h), int(m)
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError(f"bad clock time {s!r}")
    return h * 60 + m


def clock_to_sm(s: str) -> int:
    """Clock time in New York -> session minute (0 = 18:00)."""
    return (hhmm(s) + _SHIFT) % 1440


def sm_to_clock(sm: int) -> str:
    m = (int(sm) - _SHIFT) % 1440
    return f"{m // 60:02d}:{m % 60:02d}"


def local_minutes(ts_ns_utc: np.ndarray) -> np.ndarray:
    """UTC ns timestamps -> New York wall-clock minutes since epoch (DST aware)."""
    idx = pd.DatetimeIndex(pd.to_datetime(np.asarray(ts_ns_utc, dtype="int64"), utc=True))
    local = idx.tz_convert(NY).tz_localize(None)
    return (local.as_unit("ns").asi8 // 60_000_000_000).astype(np.int64)


def session_fields(ts_ns_utc: np.ndarray):
    """Return (tmin, local, sday, sm) for bar START timestamps."""
    ts = np.asarray(ts_ns_utc, dtype="int64")
    tmin = ts // 60_000_000_000
    local = local_minutes(ts)
    shifted = local + _SHIFT
    sday = (shifted // 1440).astype(np.int32)
    sm = (shifted % 1440).astype(np.int16)
    return tmin.astype(np.int64), local, sday, sm


def date_to_day(d: date) -> int:
    return (d - EPOCH).days


def day_to_date(day: int) -> date:
    return EPOCH + timedelta(days=int(day))


def session_start_utc_ns(session_date: date) -> int:
    """UTC ns of 18:00 New York on the evening BEFORE `session_date` (session open)."""
    prev = session_date - timedelta(days=1)
    t = pd.Timestamp(year=prev.year, month=prev.month, day=prev.day, hour=18).tz_localize(NY)
    return int(t.tz_convert("UTC").value)


def period_bounds_utc_ns(first_session: date, last_session: date) -> tuple[int, int]:
    """[start, end) UTC ns covering every bar of sessions first..last inclusive."""
    return session_start_utc_ns(first_session), session_start_utc_ns(last_session + timedelta(days=1))


def years_of_sday(sday: np.ndarray) -> np.ndarray:
    d = np.asarray(sday, dtype="int64").astype("datetime64[D]")
    return d.astype("datetime64[Y]").astype(np.int64) + 1970


def months_of_sday(sday: np.ndarray) -> np.ndarray:
    """YYYYMM integer for each session day."""
    d = np.asarray(sday, dtype="int64").astype("datetime64[D]")
    m = d.astype("datetime64[M]").astype(np.int64)
    return (m // 12 + 1970) * 100 + (m % 12) + 1


class Window:
    """A trading window from config/sessions.yaml in session minutes."""

    def __init__(self, name: str, entry_start: int, entry_end: int, flat_at: int):
        self.name = name
        self.entry_start = entry_start
        self.entry_end = entry_end
        self.flat_at = flat_at

    def describe(self) -> str:
        return (f"entries from {sm_to_clock(self.entry_start)} to {sm_to_clock(self.entry_end)} "
                f"New York, always flat by {sm_to_clock(self.flat_at)}")


def load_windows(sessions_cfg: dict) -> dict[str, Window]:
    out = {}
    for name, w in (sessions_cfg.get("windows") or {}).items():
        es, ee, fa = clock_to_sm(w["entry_start"]), clock_to_sm(w["entry_end"]), clock_to_sm(w["flat_at"])
        if fa == 0:
            fa = 1440
        if not (es < ee <= fa):
            raise ValueError(f"window {name}: need entry_start < entry_end <= flat_at within one session")
        out[name] = Window(name, es, ee, fa)
    return out


def rth_bounds(sessions_cfg: dict) -> tuple[int, int]:
    r = sessions_cfg.get("rth") or {"start": "09:30", "end": "16:00"}
    return clock_to_sm(r["start"]), clock_to_sm(r["end"])


# ----------------------------------------------------------------------------- V4 additions

def session_dates(ts_ns_utc: np.ndarray) -> np.ndarray:
    """Session (END) date of every bar START timestamp, as numpy datetime64[D]."""
    _t, _l, sday, _sm = session_fields(ts_ns_utc)
    return sday.astype("int64").astype("datetime64[D]")


def session_end_utc_ns(session_date: date) -> int:
    """UTC ns of 17:00 New York on `session_date` (the CME daily close)."""
    t = pd.Timestamp(year=session_date.year, month=session_date.month, day=session_date.day,
                     hour=17).tz_localize(NY)
    return int(t.tz_convert("UTC").value)


def is_complete_final_session(last_bar_ts_ns: int, last_bar_clock: str = "16:59") -> bool:
    """A file's final session is complete only if it reaches the bar starting at `last_bar_clock` NY."""
    _t, _l, _sd, sm = session_fields(np.array([last_bar_ts_ns], dtype="int64"))
    return int(sm[0]) >= clock_to_sm(last_bar_clock)
