"""Synthetic NQ/ES Market builders for tests and null-validation experiments (no real data)."""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from quantlab5.data.schema import bars_from_arrays
from quantlab5.synthetic.markets import synthetic_bars
from quantlab5.data.market import build_market


def synthetic_market(start=date(2012, 1, 2), end=date(2012, 4, 30), seed=1, rho=0.85):
    """Correlated driftless NQ/ES random walks on the Globex calendar (quarterly rolls, integer volume)."""
    a = synthetic_bars(start, end, seed=seed, base=2500.0, symbol="NQ")
    b = synthetic_bars(start, end, seed=seed + 100, base=1300.0, symbol="ES")
    rng = np.random.default_rng(seed + 7)
    ra = np.diff(a["close"].to_numpy(), prepend=a["close"].iloc[0])
    rb = rho * ra * 0.4 + np.sqrt(1 - rho ** 2) * rng.standard_normal(len(ra)) * 0.4
    cb = np.round((1300.0 + np.cumsum(rb)) / 0.25) * 0.25
    ob = np.r_[cb[0], cb[:-1]]
    hb = np.maximum(ob, cb) + 0.25 * rng.integers(0, 3, len(cb))
    lb = np.minimum(ob, cb) - 0.25 * rng.integers(0, 3, len(cb))
    ts = pd.DatetimeIndex(a["ts_event"]).as_unit("ns").asi8
    nq = bars_from_arrays("NQ", ts, a["open"], a["high"], a["low"], a["close"], a["volume"], a["symbol"])
    esym = a["symbol"].str.replace("NQ", "ES").to_numpy()
    es = bars_from_arrays("ES", ts, ob, hb, lb, cb, b["volume"].to_numpy()[:len(ts)], esym)
    return build_market(nq, es, a["symbol"].to_numpy(), esym)


# ============================================================ 9-year calibration worlds (null validation)
from quantlab5.data.sessions import session_fields  # noqa: E402
from quantlab5.synthetic.markets import session_timestamps, weekdays  # noqa: E402

PLANTS = ("zero", "momentum", "volume", "persistence", "xmarket")


def calibration_world(kind: str, seed: int, start=date(2010, 6, 7), end=date(2018, 12, 31)):
    """A DISCOVERY-length synthetic NQ/ES world with realistic structure and optionally ONE planted edge.

    Base: 1-min returns = sigma_tod x GARCH-like clustering x N(0,1); NQ/ES contemporaneous corr 0.8;
    integer volume = tod profile x (1 + |z|) Poisson; quarterly rolls. Planted edges (in NQ):
      momentum     after a 15-bar move > 2 sd, the next 15 bars drift +0.07 sd/bar in the same direction
      volume       after a bar with volume > 4x its tod norm AND |z|>1, the next 30 bars drift 0.05 sd/bar in its direction
      persistence  in random 60-bar regimes (~20% of RTH) returns follow AR(1) with phi = +0.25
      xmarket      NQ return at t gets + 0.35 x ES standardized return at t-1 (ES leads by one minute)
    """
    kind, _, mult = kind.partition("_x")          # e.g. "volume_x2" = volume plant at 2x strength
    k_str = float(mult) if mult else 1.0
    rng = np.random.default_rng(seed)
    ts = session_timestamps(weekdays(start, end))
    n = len(ts)
    _t, _l, sday, sm = session_fields(ts)
    sm = sm.astype(np.int64)
    rth = (sm >= 930) & (sm < 1320)
    prof = np.where(rth, 1.0, 0.35) * (1 + 1.2 * np.exp(-((sm - 930) / 20.0) ** 2) + 0.8 * np.exp(-((sm - 1319) / 15.0) ** 2))
    # slow volatility regime (session-level) x fast clustering
    days, sidx = np.unique(sday, return_inverse=True)
    reg = np.exp(np.cumsum(rng.standard_normal(len(days)) * 0.08))
    reg = reg / np.exp(np.convolve(np.log(reg), np.ones(60) / 60, mode="same"))
    fast = np.exp(0.35 * np.convolve(rng.standard_normal(n), np.ones(30) / np.sqrt(30), mode="same"))
    sd = prof * reg[sidx] * fast
    z_nq = rng.standard_normal(n)
    z_es = 0.8 * z_nq + 0.6 * rng.standard_normal(n)
    r_nq = z_nq * sd * 1.0
    r_es = z_es * sd * 0.4
    vol_mult = np.ones(n)
    first = np.r_[True, sday[1:] != sday[:-1]]
    if kind == "momentum":
        c15 = np.convolve(z_nq, np.ones(15), mode="full")[:n] / np.sqrt(15)
        ev = np.nonzero(rth & (np.abs(c15) > 2.0))[0]
        drift = np.zeros(n)
        for i in ev[::1]:
            j = slice(i + 1, min(i + 16, n))
            drift[j] += 0.07 * k_str * np.sign(c15[i])
        r_nq = r_nq + drift * sd
    elif kind == "volume":
        spike = rth & (rng.random(n) < 0.004) & (np.abs(z_nq) > 1.0)
        vol_mult = np.where(spike, 6.0, 1.0)
        drift = np.zeros(n)
        for i in np.nonzero(spike)[0]:
            drift[i + 1:min(i + 31, n)] += 0.05 * k_str * np.sign(z_nq[i])
        r_nq = r_nq + drift * sd
    elif kind == "persistence":
        on = np.zeros(n, bool)
        starts = np.nonzero(rth & (rng.random(n) < 0.2 / 60))[0]
        for i in starts:
            on[i:min(i + 60, n)] = True
        z = z_nq.copy()
        for i in np.nonzero(on)[0]:
            if i > 0 and not first[i]:
                phi = min(0.25 * k_str, 0.9)
                z[i] = phi * z[i - 1] + np.sqrt(1 - phi ** 2) * z_nq[i]
        r_nq = z * sd
        r_es = (0.8 * z + 0.6 * rng.standard_normal(n)) * sd * 0.4
    elif kind == "xmarket":
        lead = np.r_[0.0, z_es[:-1]] / 1.0
        lead[first] = 0.0
        r_nq = r_nq + 0.35 * k_str * lead * sd * np.where(rth, 1.0, 0.0)
    elif kind != "zero":
        raise ValueError(kind)
    # quarterly rolls with a gap
    d = sday.astype("datetime64[D]")
    q = (d.astype("datetime64[Y]").astype(int) * 4 + (d.astype("datetime64[M]").astype(int) % 12) // 3)
    roll = np.r_[False, q[1:] != q[:-1]]

    def build(r, base, gap, sym_root):
        close = base + np.cumsum(r + roll * gap)
        c = np.round(close / 0.25) * 0.25
        o = np.r_[c[0], c[:-1]]
        w = np.abs(rng.standard_normal(n)) * np.maximum(sd, 0.1) * 0.6
        h = np.maximum(o, c) + np.round(w / 0.25) * 0.25
        l_ = np.minimum(o, c) - np.round(np.abs(rng.standard_normal(n)) * np.maximum(sd, 0.1) * 0.6 / 0.25) * 0.25
        return o, h, l_, c

    vol_base_nq = 60 * prof * reg[sidx] * (1 + np.abs(z_nq)) * vol_mult
    vol_base_es = 300 * prof * reg[sidx] * (1 + np.abs(z_es))
    o, h, l_, c = build(r_nq, 3000.0, 8.0, "NQ")
    eo, eh, el, ec = build(r_es, 1500.0, 3.0, "ES")
    code = np.array(["H", "M", "U", "Z"])[q % 4]
    yr = (d.astype("datetime64[Y]").astype(int) + 1970) % 10
    nq_sym = np.char.add(np.char.add("NQ", code), yr.astype(str))
    es_sym = np.char.add(np.char.add("ES", code), yr.astype(str))
    nq = bars_from_arrays("NQ", ts, o, h, l_, c, rng.poisson(vol_base_nq), nq_sym, source=f"synthetic:{kind}")
    es = bars_from_arrays("ES", ts, eo, eh, el, ec, rng.poisson(vol_base_es), es_sym, source=f"synthetic:{kind}")
    return build_market(nq, es, nq_sym, es_sym)
