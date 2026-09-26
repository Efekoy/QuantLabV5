"""Seeded signal equivalence for compiled E07 and E27 loops."""
from datetime import date

import numpy as np

from quantlab5.data.market import build_market
from quantlab5.features import ops as O
from quantlab5.synthetic.markets import correlated_pair, weekdays
from quantlab5.v5.signals import SignalContext


def test_compiled_e07_and_e27_match_original_formulas():
    nq, es = correlated_pair(weekdays(date(2020, 1, 2), date(2020, 2, 13)))
    market = build_market(nq, es, np.full(nq.n, "NQZ0"), np.full(es.n, "ESZ0"))
    ctx = SignalContext(market)
    close, gid = np.asarray(nq.c, float), market.gid
    gs = O.group_start(gid)
    for lookback in (15, 30, 60):
        start = O.lag(close, lookback, gid)
        original = np.full(market.n, np.nan)
        for i in range(market.n):
            if i-lookback >= gs[i]:
                original[i] = np.mean(close[i-lookback+1:i+1] > start[i])
        assert np.array_equal(ctx.e07_occupation(lookback), original, equal_nan=True)
    ctx.c15[:] = True
    range15 = O.rmax(nq.h, 15, gid) - O.rmin(nq.l, 15, gid)
    first10 = O.lag(O.rmax(nq.h, 10, gid) - O.rmin(nq.l, 10, gid), 5, gid)
    for lookback, threshold in ((30, 1.5), (60, 1.5), (120, 1.125)):
        original = np.zeros(market.n, np.int8)
        for i in np.flatnonzero(ctx.c15):
            if i-lookback < gs[i] or not np.isfinite(range15[i]) or range15[i] <= 0:
                continue
            previous = range15[i-lookback:i]
            if not np.isfinite(previous).all() or not np.isfinite(first10[i]):
                continue
            if (range15[i] >= threshold*np.median(previous)
                    and (range15[i]-first10[i])/range15[i] >= .7):
                original[i] = ctx.direction15[i]
        assert np.array_equal(ctx._e27(lookback, threshold), original)


def test_compiled_e23_kalman_matches_original_signal_decisions():
    nq, es = correlated_pair(weekdays(date(2020, 1, 2), date(2020, 7, 31)))
    market = build_market(nq, es, np.full(nq.n, "NQZ0"), np.full(es.n, "ESZ0"))
    ctx = SignalContext(market)
    days = np.asarray(nq.sday)
    unique, day_idx = np.unique(days, return_inverse=True)
    bounds = np.r_[0, np.flatnonzero(days[1:] != days[:-1]) + 1, market.n]
    daily_move = np.bincount(day_idx, weights=np.nan_to_num(ctx.r*ctx.r), minlength=len(unique))
    daily_range = np.bincount(day_idx, weights=(np.asarray(nq.h)-np.asarray(nq.l))**2,
                              minlength=len(unique))
    daily_count = np.bincount(day_idx, minlength=len(unique))
    for lookback, threshold in ((30, 1.5), (60, 1.5), (120, 1.125)):
        original = np.zeros(market.n, np.int8)
        for k in range(lookback, len(unique)):
            move_var = np.median(daily_move[k-lookback:k] / np.maximum(daily_count[k-lookback:k], 1))
            range_var = np.median(daily_range[k-lookback:k] / np.maximum(daily_count[k-lookback:k], 1))
            q = max(1e-8, move_var * float(nq.o[bounds[k]])**2)
            noise = max(.25**2, range_var)
            state = np.array([float(nq.o[bounds[k]]), 0.0])
            covariance = np.diag([noise, q])
            f = np.array([[1.0, 1.0], [0.0, 1.0]])
            process = np.diag([q*.01, q])
            for i in range(bounds[k], bounds[k+1]):
                if not np.isfinite(nq.c[i]):
                    continue
                state = f @ state
                covariance = f @ covariance @ f.T + process
                innovation = float(nq.c[i]) - state[0]
                denom = covariance[0, 0] + noise
                gain = covariance[:, 0] / denom
                state += gain * innovation
                covariance -= np.outer(gain, covariance[0, :])
                if (ctx.c15[i] and np.sign(state[1]) == ctx.direction15[i]
                        and abs(state[1]) >= threshold * np.sqrt(max(covariance[1, 1], 0))):
                    original[i] = ctx.direction15[i]
        assert np.array_equal(ctx._e23(lookback, threshold), original)
