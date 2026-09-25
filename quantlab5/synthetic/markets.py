"""Synthetic OHLCV markets with KNOWN properties -- software-correctness fixtures only.

(synthetic_bars is adapted from quantlab3/data/synthetic.py; V4 adds integer volume
with an intraday profile. The known-property fixtures below are new in V4.)

Nothing here is statistical research: each fixture exists so a test can assert an
exact, known outcome of the engine, features, resampling, nulls or isolation code.
No real market data is read.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from quantlab5.data.schema import Bars, bars_from_arrays
from quantlab5.data.sessions import NY

TICK = 0.25


# ------------------------------------------------------------------ timestamps

def session_timestamps(session_dates, rth_only: bool = False, minutes: int | None = None) -> np.ndarray:
    """UTC ns bar-start timestamps. Globex: 18:00 prev day -> 16:59; RTH: 09:30 -> 15:59."""
    out = []
    for d in session_dates:
        d = pd.Timestamp(d)
        if rth_only:
            first = pd.Timestamp(d.year, d.month, d.day, 9, 30).tz_localize(NY)
            n = minutes or 390
            out.append(pd.date_range(first, periods=n, freq="min").tz_convert("UTC").as_unit("ns").asi8)
        else:
            p = d - timedelta(days=1)
            # wall-clock construction: "midnight + 18h" is 17:00 on a DST-ending Sunday (V3 synthetic bug)
            first = pd.Timestamp(p.year, p.month, p.day, 18, 0).tz_localize(NY)
            last = pd.Timestamp(d.year, d.month, d.day, 16, 59).tz_localize(NY)
            rng = pd.date_range(first.tz_convert("UTC"), last.tz_convert("UTC"), freq="min")
            if minutes:
                rng = rng[:minutes]
            out.append(rng.as_unit("ns").asi8)
    return np.concatenate(out) if out else np.zeros(0, np.int64)


def weekdays(start: date, end: date) -> list[date]:
    return [d.date() for d in pd.date_range(start, end, freq="D") if d.weekday() < 5]


def _ohlc_from_close(close: np.ndarray, rng, wick: float = 0.5, tick: float = TICK):
    close = np.round(np.asarray(close) / tick) * tick
    open_ = np.r_[close[0], close[:-1]]
    hi = np.maximum(open_, close) + np.round(np.abs(rng.standard_normal(len(close))) * wick / tick) * tick
    lo = np.minimum(open_, close) - np.round(np.abs(rng.standard_normal(len(close))) * wick / tick) * tick
    return open_, hi, lo, close


def _volume(ts: np.ndarray, rng, base: int = 200) -> np.ndarray:
    local = pd.DatetimeIndex(pd.to_datetime(ts, utc=True)).tz_convert(NY)
    mod = local.hour * 60 + local.minute
    prof = np.where((mod >= 570) & (mod < 960), 4.0, 1.0)
    return rng.poisson(base * prof).astype(np.int64)


# ------------------------------------------------------------------ V3-derived random walk

def synthetic_bars(start: date, end: date, seed: int = 7, base: float = 5000.0, tick: float = TICK,
                   symbol: str = "SYN", rth_only: bool = False, roll_gap: float = 15.0) -> pd.DataFrame:
    """Driftless random walk, Globex sessions Mon-Fri, quarterly 'rolls' with a price gap, integer volume.

    Returns a DataFrame in the canonical schema (ts_event, open, high, low, close, volume, symbol)."""
    rng = np.random.default_rng(seed)
    ts = session_timestamps(weekdays(start, end), rth_only=rth_only)
    n = len(ts)
    local = pd.DatetimeIndex(pd.to_datetime(ts, utc=True)).tz_convert(NY)
    mod = (local.hour * 60 + local.minute).to_numpy()
    vol = np.where((mod >= 570) & (mod < 960), 1.0, 0.35) * 1.2
    steps = rng.standard_normal(n) * vol
    from quantlab5.data.sessions import session_fields
    _t, _l, sday, _sm = session_fields(ts)
    sdate = pd.to_datetime(sday.astype("int64"), unit="D")
    qkey = (sdate.year * 4 + (sdate.month - 1) // 3).to_numpy()
    seg_change = np.r_[False, qkey[1:] != qkey[:-1]]
    close = base + np.cumsum(steps + seg_change * roll_gap)
    o, h, l, c = _ohlc_from_close(close, rng, 0.6, tick)
    contract = np.array([f"{symbol}Q{k}" for k in qkey])
    return pd.DataFrame({"ts_event": pd.to_datetime(ts, utc=True), "open": o, "high": h, "low": l, "close": c,
                         "volume": _volume(ts, rng), "symbol": contract})


# ------------------------------------------------------------------ known-property fixtures

def _bars(inst, ts, o, h, l, c, v, symbol=None, source="synthetic") -> Bars:
    return bars_from_arrays(inst, ts, o, h, l, c, v, symbol if symbol is not None else np.full(len(ts), "SYNA"),
                            source=source)


def rising_market(n: int = 390, step: float = 1.0, start_px: float = 1000.0, session: str = "2020-10-05") -> Bars:
    """Every bar closes exactly `step` above the previous close; open = previous close."""
    ts = session_timestamps([session], rth_only=True, minutes=n)
    c = start_px + step * np.arange(1, n + 1)
    o = c - step
    return _bars("SYN", ts, o, c + TICK, o - TICK, c, np.full(n, 100))


def falling_market(n: int = 390, step: float = 1.0, start_px: float = 2000.0, session: str = "2020-10-05") -> Bars:
    ts = session_timestamps([session], rth_only=True, minutes=n)
    c = start_px - step * np.arange(1, n + 1)
    o = c + step
    return _bars("SYN", ts, o, o + TICK, c - TICK, c, np.full(n, 100))


def flat_market(n: int = 390, px: float = 1500.0, session: str = "2020-10-05") -> Bars:
    ts = session_timestamps([session], rth_only=True, minutes=n)
    p = np.full(n, px)
    return _bars("SYN", ts, p, p, p, p, np.full(n, 100))


def random_zero_edge_market(sessions: list[date], seed: int = 1, start_px: float = 10000.0) -> Bars:
    """Driftless symmetric random walk: no strategy has a true edge on it."""
    rng = np.random.default_rng(seed)
    ts = session_timestamps(sessions)
    close = start_px + np.cumsum(rng.choice([-TICK, TICK], size=len(ts)) * rng.integers(1, 5, len(ts)))
    o, h, l, c = _ohlc_from_close(close, rng, 0.5)
    return _bars("SYN", ts, o, h, l, c, _volume(ts, rng))


PLANT_EVERY = 30        # planted-edge marker: session minute divisible by 30
PLANT_BARS = 5          # bars of drift after each marker
PLANT_DRIFT = 2.0       # points per bar


def planted_edge_market(sessions: list[date], seed: int = 2, start_px: float = 10000.0) -> Bars:
    """Random walk plus a KNOWN edge: after each bar whose session minute is a multiple of
    PLANT_EVERY, the next PLANT_BARS bars each rise by PLANT_DRIFT points (+ tiny noise)."""
    rng = np.random.default_rng(seed)
    ts = session_timestamps(sessions)
    from quantlab5.data.sessions import session_fields
    _t, _l, _sd, sm = session_fields(ts)
    steps = rng.choice([-TICK, 0.0, TICK], size=len(ts))
    marker = (sm.astype(int) % PLANT_EVERY) == 0
    for k in range(1, PLANT_BARS + 1):
        idx = np.nonzero(marker)[0] + k
        idx = idx[idx < len(ts)]
        steps[idx] = PLANT_DRIFT
    close = start_px + np.cumsum(steps)
    c = np.round(close / TICK) * TICK
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + TICK
    l = np.minimum(o, c) - TICK
    return _bars("SYN", ts, o, h, l, c, _volume(ts, rng))


def planted_edge_signal(bars: Bars) -> np.ndarray:
    """The causal dummy signal matching the planted edge: fires at the close of each marker bar."""
    return (np.asarray(bars.sm).astype(int) % PLANT_EVERY) == 0


def correlated_pair(sessions: list[date], seed: int = 3, rho: float = 0.9, missing_every: int = 97):
    """NQ-like and ES-like instruments with correlated returns. ES is missing every
    `missing_every`-th bar (to test that alignment never forward-fills)."""
    rng = np.random.default_rng(seed)
    ts = session_timestamps(sessions)
    z1 = rng.standard_normal(len(ts))
    z2 = rho * z1 + np.sqrt(1 - rho ** 2) * rng.standard_normal(len(ts))
    nq_close = 12000 + np.cumsum(z1 * 2.0)
    es_close = 4000 + np.cumsum(z2 * 0.75)
    o1, h1, l1, c1 = _ohlc_from_close(nq_close, rng, 0.75)
    o2, h2, l2, c2 = _ohlc_from_close(es_close, rng, 0.25)
    nq = _bars("NQ", ts, o1, h1, l1, c1, _volume(ts, rng), np.full(len(ts), "NQZ0"))
    keep = np.ones(len(ts), bool)
    keep[missing_every - 1::missing_every] = False      # every k-th bar missing (none if k > n)
    es = _bars("ES", ts[keep], o2[keep], h2[keep], l2[keep], c2[keep], _volume(ts, rng)[keep],
               np.full(int(keep.sum()), "ESZ0"))
    return nq, es


def volume_spike_market(n: int = 390, spikes=(50, 120, 300), base: int = 100, spike: int = 5000,
                        session: str = "2020-10-05") -> Bars:
    ts = session_timestamps([session], rth_only=True, minutes=n)
    c = np.full(n, 1000.0)
    v = np.full(n, base)
    v[list(spikes)] = spike
    v[10] = 0                              # one known zero-volume bar
    return _bars("SYN", ts, c, c + TICK, c - TICK, c, v)


def session_boundary_market(sessions=("2021-03-11", "2021-03-12", "2021-03-15", "2021-03-16"),
                            seed: int = 4) -> Bars:
    """Full Globex sessions across the 2021 US DST change (Mar 14)."""
    rng = np.random.default_rng(seed)
    ts = session_timestamps([pd.Timestamp(s).date() for s in sessions])
    o, h, l, c = _ohlc_from_close(5000 + np.cumsum(rng.standard_normal(len(ts))), rng, 0.5)
    return _bars("SYN", ts, o, h, l, c, _volume(ts, rng))


def roll_boundary_market(seed: int = 5, gap: float = 40.0) -> Bars:
    """Two sessions; the contract changes (SYNZ0 -> SYNH1) at the start of the second,
    with an unadjusted price gap of `gap` points."""
    rng = np.random.default_rng(seed)
    ts = session_timestamps([date(2020, 12, 17), date(2020, 12, 18)])
    from quantlab5.data.sessions import session_fields
    _t, _l, sday, _sm = session_fields(ts)
    second = sday == sday.max()
    close = 12000 + np.cumsum(rng.choice([-TICK, TICK], size=len(ts))) + second * gap
    o, h, l, c = _ohlc_from_close(close, rng, 0.5)
    i0 = int(np.argmax(second))            # the new contract's first bar opens at its own level
    o[i0], h[i0], l[i0] = c[i0], c[i0] + TICK, c[i0] - TICK
    sym = np.where(second, "SYNH1", "SYNZ0")
    return _bars("SYN", ts, o, h, l, c, _volume(ts, rng), sym)
