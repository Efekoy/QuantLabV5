"""New York session logic across DST transitions. (Ported from QuantLabV3 tests; V4 additions at the end.)"""
from datetime import date

import pandas as pd

from quantlab5.data.sessions import clock_to_sm, day_to_date, session_fields, session_start_utc_ns


def _one(ts: str):
    t = pd.Timestamp(ts, tz="America/New_York").tz_convert("UTC").value
    tmin, local, sday, sm = session_fields([t])
    return int(sday[0]), int(sm[0]), t


def test_rth_open_is_930_in_winter_and_summer():
    for ts in ("2021-03-12 09:30", "2021-03-15 09:30", "2021-11-05 09:30", "2021-11-08 09:30"):
        _sd, sm, _ = _one(ts)
        assert sm == clock_to_sm("09:30") == 930
    # but the UTC times differ by an hour
    assert _one("2021-03-15 09:30")[2] - _one("2021-03-12 09:30")[2] == (3 * 24 - 1) * 3600 * 10**9


def test_sunday_evening_belongs_to_monday_session():
    sd, sm, _ = _one("2021-03-14 18:00")          # the day DST starts
    assert day_to_date(sd) == date(2021, 3, 15) and sm == 0
    sd, sm, _ = _one("2021-11-07 18:00")          # the day DST ends
    assert day_to_date(sd) == date(2021, 11, 8) and sm == 0
    sd, _, _ = _one("2021-11-08 16:59")
    assert day_to_date(sd) == date(2021, 11, 8)


def test_session_boundary_utc():
    # session of Mon 2021-03-15 opens Sun 18:00 EDT = 22:00 UTC; winter session opens 23:00 UTC
    assert pd.Timestamp(session_start_utc_ns(date(2021, 3, 15)), tz="UTC") == pd.Timestamp("2021-03-14 22:00", tz="UTC")
    assert pd.Timestamp(session_start_utc_ns(date(2021, 3, 12)), tz="UTC") == pd.Timestamp("2021-03-11 23:00", tz="UTC")


def test_clock_conversions():
    assert clock_to_sm("18:00") == 0
    assert clock_to_sm("16:00") == 1320
    assert clock_to_sm("02:00") == 480


# ----------------------------------------------------------------------------- V4 additions
import numpy as np  # noqa: E402

from quantlab5.data.sessions import is_complete_final_session, session_dates  # noqa: E402
from quantlab5.synthetic.markets import session_boundary_market, session_timestamps  # noqa: E402


def test_synthetic_globex_sessions_start_at_1800_on_dst_sundays():
    # regression for the inherited V3 synthetic bug ("midnight + 18h" = 17:00 on 2020-11-01)
    for d in (date(2020, 11, 2), date(2021, 3, 15)):
        ts = session_timestamps([d])
        first = pd.Timestamp(ts[0], tz="UTC").tz_convert("America/New_York")
        assert (first.hour, first.minute) == (18, 0)
        assert set(session_dates(ts).astype(str)) == {str(d)}
        assert len(ts) == 23 * 60


def test_dst_sessions_have_constant_session_minutes_but_shifted_utc():
    b = session_boundary_market()
    days = np.unique(b.sday)
    assert len(days) == 4
    for d in days:
        m = b.sday == d
        assert b.sm[m][0] == 0 and b.sm[m][-1] == 1379          # 18:00 .. 16:59 every day
    # the RTH open (session minute 930) is 14:30 UTC in winter and 13:30 UTC in summer
    utc_hours = sorted({pd.Timestamp(int(t), tz="UTC").hour for t in b.ts[b.sm == 930]})
    assert utc_hours == [13, 14]


def test_final_session_completeness_rule():
    full = session_timestamps([date(2021, 3, 16)])
    assert is_complete_final_session(int(full[-1]))
    assert not is_complete_final_session(int(full[-2]))
