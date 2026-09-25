"""Canonical exit templates and precomputed trade outcomes.

For every decision bar t, every exit template e and both directions, simulate ONE trade entered at
the open of bar t+1 under the frozen execution rules (identical to quantlab5.engine.backtest):
  * stop = stop_mult * STOP_K * stop_scale[t] points, rounded UP to the tick (never tighter);
    a gap through the stop fills at the (worse) open; stop checked from the entry bar on
  * target (R templates) = R * stop distance; fills at the target only on a 1-tick trade-through;
    a gap beyond target+1 tick fills at the target (never better)
  * same-bar stop and target -> stop first (pessimistic)
  * time exits fill at the close of the last bar of the holding period (minutes)
  * always flat at the close of the last bar before 16:00, at a session change or at a roll
Result: pnl points (per contract, gross) and the exit bar index. A candidate then takes its
events greedily: an event at bar t is taken only if t >= the previous trade's exit bar (one
position at a time, exactly as the engine: a signal on the exit bar's close can enter next bar).
Equivalence with engine.backtest.run_backtest is tested in tests/test_v4_outcomes.py.
"""
from __future__ import annotations

import numpy as np
from numba import njit

STOP_K = float(np.sqrt(10.0))
TICK = 0.25
THROUGH_TICKS = 1.0
FLAT_SM = 1320

EXITS = []
for _m in (1.0, 2.0):
    for _k, _hold, _R in (("T15", 15, 0.0), ("T30", 30, 0.0), ("T60", 60, 0.0), ("T120", 120, 0.0),
                          ("EOD", -1, 0.0), ("R2", -1, 2.0), ("R3", -1, 3.0)):
        EXITS.append({"id": f"S{_m:g}_{_k}", "stop_mult": _m, "hold": _hold, "target_R": _R})
EXIT_IDS = [e["id"] for e in EXITS]


@njit(cache=True)
def _simulate(o, h, l, c, tmin, gid, sm, dec, stopd, dirn, hold, R, tick, through, flat_sm, pnl, xbar):
    n = len(o)
    for k in range(len(dec)):
        t = dec[k]
        e = t + 1
        d = stopd[k]
        if not (d > 0.0) or e >= n:
            pnl[k] = np.nan
            xbar[k] = -1
            continue
        ep = o[e]
        sp = ep - dirn * d
        has_t = R > 0.0
        tp = ep + dirn * R * d
        emin = tmin[e]
        i = e
        while True:
            s_hit = (l[i] <= sp) if dirn == 1 else (h[i] >= sp)
            t_hit = False
            if has_t:
                t_hit = (h[i] >= tp + through) if dirn == 1 else (l[i] <= tp - through)
            if s_hit or t_hit:
                gap_s = i > e and ((o[i] <= sp) if dirn == 1 else (o[i] >= sp))
                gap_t = has_t and i > e and ((o[i] >= tp + through) if dirn == 1 else (o[i] <= tp - through))
                if gap_s:
                    fill = o[i]
                elif gap_t:
                    fill = tp
                elif s_hit:
                    fill = sp
                else:
                    fill = tp
                pnl[k] = dirn * (fill - ep)
                xbar[k] = i
                break
            done = False
            if hold > 0 and tmin[i] - emin >= hold - 1:
                done = True
            elif i == n - 1 or gid[i + 1] != gid[i] or sm[i + 1] >= flat_sm or sm[i] >= flat_sm:
                done = True
            if done:
                pnl[k] = dirn * (c[i] - ep)
                xbar[k] = i
                break
            i += 1


def stop_distances(stop_scale, dec, mult, tick=TICK):
    raw = mult * STOP_K * np.asarray(stop_scale, np.float64)[dec]
    d = np.ceil(raw / tick - 1e-9) * tick
    return np.where(np.isfinite(d) & (d >= tick), d, np.nan)


def compute_outcomes(market, stop_scale):
    """Returns pnl float32 [n_exit, n_dec, 2] (dir 0 = long, 1 = short) and exit bar int32 [same]."""
    b = market.nq
    o, h, l, c = (np.asarray(x, np.float64) for x in (b.o, b.h, b.l, b.c))
    tmin = np.asarray(b.tmin, np.int64)
    sm = np.asarray(b.sm, np.int64)
    dec = market.dec
    nd = len(dec)
    pnl = np.empty((len(EXITS), nd, 2), np.float32)
    xbar = np.empty((len(EXITS), nd, 2), np.int32)
    tmp_p = np.empty(nd, np.float64)
    tmp_x = np.empty(nd, np.int64)
    for ei, ex in enumerate(EXITS):
        sd = stop_distances(stop_scale, dec, ex["stop_mult"])
        for di, dirn in enumerate((1, -1)):
            _simulate(o, h, l, c, tmin, market.gid, sm, dec, sd, dirn, int(ex["hold"]), float(ex["target_R"]),
                      TICK, THROUGH_TICKS * TICK, FLAT_SM, tmp_p, tmp_x)
            pnl[ei, :, di] = tmp_p
            xbar[ei, :, di] = tmp_x
    return pnl, xbar
