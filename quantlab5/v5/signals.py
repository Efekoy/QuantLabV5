"""Causal V5 market signals. Work in progress: implemented families only.

Signal masks refer to the close of completed bar t. The execution engine enters
at t+1 open. All price-derived features are built from Market's aligned bars;
no partition loader is called here. A family not implemented below raises,
never silently returns an empty placeholder signal.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
from numba import njit

from quantlab5.data.market import Market
from quantlab5.data.sessions import months_of_sday
from quantlab5.features import ops as O
from quantlab5.search.candidate_id import candidate_id


def _valid_div(num, den):
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.asarray(num, float) / np.asarray(den, float)
    return np.where(np.isfinite(out) & (np.asarray(den) > 0), out, np.nan)


def _past_clock_quantile(x: np.ndarray, m: Market, sessions: int, q: float) -> np.ndarray:
    """Prior distinct sessions at the same NY session minute, never today.

    A repeated DST clock minute contributes at most one (last completed) value
    when it becomes a previous session. Missing observations disable the result;
    a full `sessions` historical values are required. References cross contract
    rolls for dimensionless returns, while roll-window bars are later masked.
    """
    if sessions < 1 or not 0 <= q <= 1:
        raise ValueError("bad historical quantile")
    a = np.asarray(x, float)
    if len(a) != m.n:
        raise ValueError("feature length mismatch")
    return _clock_quantile_kernel(a, np.asarray(m.nq.sm, np.int64),
                                  np.asarray(m.nq.sday, np.int64), sessions, q)


@njit(cache=True)
def _clock_quantile_kernel(a, sm, day, sessions, q):
    """Maintain one sorted prior-session window per NY clock minute."""
    out = np.full(len(a), np.nan)
    history = np.full((1380, sessions), np.nan)
    ordered = np.full((1380, sessions), np.nan)
    counts = np.zeros(1380, np.int64)
    valid = np.zeros(1380, np.int64)
    pointer = np.zeros(1380, np.int64)
    last_day = np.full(1380, -9223372036854775807, np.int64)
    pending = np.full(1380, np.nan)
    for i in range(len(a)):
        clock = sm[i]
        if clock < 0 or clock >= 1380:
            continue
        if day[i] != last_day[clock]:
            if last_day[clock] != -9223372036854775807:
                slot = pointer[clock]
                old = history[clock, slot]
                if np.isfinite(old):
                    position = 0
                    while position < valid[clock] and ordered[clock, position] != old:
                        position += 1
                    if position < valid[clock]:
                        for k in range(position, valid[clock]-1):
                            ordered[clock, k] = ordered[clock, k+1]
                        valid[clock] -= 1
                new = pending[clock]
                history[clock, slot] = new
                if np.isfinite(new):
                    position = 0
                    while position < valid[clock] and ordered[clock, position] <= new:
                        position += 1
                    for k in range(valid[clock], position, -1):
                        ordered[clock, k] = ordered[clock, k-1]
                    ordered[clock, position] = new
                    valid[clock] += 1
                pointer[clock] = (slot + 1) % sessions
                if counts[clock] < sessions:
                    counts[clock] += 1
            last_day[clock] = day[i]
        if counts[clock] == sessions and valid[clock] == sessions:
            rank = (sessions-1)*q
            lo = int(rank)
            hi = min(lo+1, sessions-1)
            fraction = rank-lo
            out[i] = ordered[clock, lo]*(1-fraction) + ordered[clock, hi]*fraction
        pending[clock] = a[i]
    return out


@njit(cache=True)
def _occupation_kernel(close, start, group_start, lookback):
    out = np.full(len(close), np.nan)
    for i in range(len(close)):
        if i-lookback < group_start[i]:
            continue
        count = 0
        for j in range(i-lookback+1, i+1):
            if close[j] > start[i]:
                count += 1
        out[i] = count/lookback
    return out


@njit(cache=True)
def _e27_kernel(range15, first10, c15, direction15, group_start,
                lookback, threshold):
    out = np.zeros(len(range15), np.int8)
    for i in range(len(range15)):
        if not c15[i] or i-lookback < group_start[i] or not np.isfinite(range15[i]) or range15[i] <= 0:
            continue
        previous = range15[i-lookback:i]
        if not np.all(np.isfinite(previous)) or not np.isfinite(first10[i]):
            continue
        if (range15[i] >= threshold*np.median(previous)
                and (range15[i]-first10[i])/range15[i] >= .7):
            out[i] = direction15[i]
    return out


@njit(cache=True)
def _e23_filter_kernel(close, opened, bounds, move_variance, range_variance,
                       c15, direction15, lookback, threshold):
    out = np.zeros(len(close), np.int8)
    for k in range(lookback, len(bounds)-1):
        q = max(1e-8, move_variance[k]*opened[bounds[k]]**2)
        noise = max(.25**2, range_variance[k])
        x0 = opened[bounds[k]]
        x1 = 0.0
        p00 = noise
        p01 = 0.0
        p10 = 0.0
        p11 = q
        for i in range(bounds[k], bounds[k+1]):
            if not np.isfinite(close[i]):
                continue
            prediction = x0+x1
            a = p00+p01+p10+p11+q*.01
            b = p01+p11
            c = p10+p11
            d = p11+q
            innovation = close[i]-prediction
            denom = a+noise
            k0 = a/denom
            k1 = c/denom
            x0 = prediction+k0*innovation
            x1 = x1+k1*innovation
            p00 = a-k0*a
            p01 = b-k0*b
            p10 = c-k1*a
            p11 = d-k1*b
            if (c15[i] and np.sign(x1) == direction15[i]
                    and abs(x1) >= threshold*np.sqrt(max(p11, 0.0))):
                out[i] = direction15[i]
    return out


def _rth_session_start(m: Market) -> np.ndarray:
    sm = np.asarray(m.nq.sm)
    gid = np.asarray(m.gid)
    return (sm >= 930) & (sm < 1320) & (np.r_[True, (sm[:-1] < 930) | (gid[1:] != gid[:-1])])


def _rolling_slope(x: np.ndarray, y: np.ndarray, n: int, gid: np.ndarray) -> np.ndarray:
    sx, sy = O.rsum(x, n, gid), O.rsum(y, n, gid)
    sxx, sxy = O.rsum(x*x, n, gid), O.rsum(x*y, n, gid)
    return _valid_div(sxy - sx*sy/n, sxx - sx*sx/n)


def _fit_logit(features: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """Deterministic L2 logistic fit; no random seed or test-period tuning."""
    x, y = np.asarray(features, float), np.asarray(labels, float)
    if len(x) < 30 or x.ndim != 2 or len(np.unique(y)) < 2 or not np.isfinite(x).all():
        return None
    mean = x.mean(axis=0)
    scale = np.maximum(x.std(axis=0), 1e-6)
    z = np.column_stack((np.ones(len(x)), (x - mean) / scale))
    beta = np.zeros(z.shape[1])
    ridge = np.diag(np.r_[0.0, np.ones(z.shape[1]-1)])
    for _ in range(20):
        p = 1 / (1 + np.exp(-np.clip(z @ beta, -30, 30)))
        h = z.T @ ((p*(1-p))[:, None] * z) + ridge
        grad = z.T @ (p-y) + ridge @ beta
        step = np.linalg.solve(h, grad)
        beta -= step
        if np.max(np.abs(step)) < 1e-7:
            break
    return mean, scale, beta


def _walkforward_probabilities(m: Market, event: np.ndarray, features: np.ndarray,
                               labels: np.ndarray, *, label_positive: bool,
                               training_sessions: int) -> np.ndarray:
    """Monthly refit from prior sessions, with one whole-session purge."""
    out = np.full(m.n, np.nan)
    days = np.asarray(m.nq.sday)
    unique_days, session_idx = np.unique(days, return_inverse=True)
    months = months_of_sday(days)
    valid = event & np.isfinite(labels) & np.isfinite(features).all(axis=1)
    for month in np.unique(months):
        target = np.flatnonzero((months == month) & event & np.isfinite(features).all(axis=1))
        if not len(target):
            continue
        first_session = int(session_idx[target[0]])
        train = np.flatnonzero(valid & (session_idx < first_session-1)
                              & (session_idx >= max(0, first_session-1-training_sessions)))
        y = labels[train] if label_positive else 1-labels[train]
        fitted = _fit_logit(features[train], y)
        if fitted is None:
            continue
        mean, scale, beta = fitted
        z = np.column_stack((np.ones(len(target)), (features[target]-mean)/scale))
        out[target] = 1/(1+np.exp(-np.clip(z @ beta, -30, 30)))
    return out


@dataclass
class SignalContext:
    market: Market
    cache: dict = field(default_factory=dict)

    def __post_init__(self):
        m = self.market
        b, g = m.nq, m.gid
        self.session_days, self.session_inverse = np.unique(
            np.asarray(b.sday), return_inverse=True)
        self.calendar_years = m.years()
        close = np.asarray(b.c, float)
        prev = O.lag(close, 1, g)
        self.r = np.log(_valid_div(close, prev))
        self.er = np.log(_valid_div(np.asarray(m.ec, float), O.lag(m.ec, 1, g)))
        self.tick_return = .25 / close
        self.v = np.maximum(_past_clock_quantile(np.abs(self.r), m, 20, .5), self.tick_return)
        self.ret15 = O.rsum(self.r, 15, g)
        self.es_ret15 = O.rsum(self.er, 15, g)
        self.direction15 = np.sign(np.nan_to_num(self.ret15, nan=0.0)).astype(np.int8)
        self.c15 = (np.isfinite(self.ret15) & np.isfinite(self.v)
                    & (np.abs(self.ret15) >= 1.5 * self.v * np.sqrt(15)))
        tr = np.maximum(np.asarray(b.h) - np.asarray(b.l),
                        np.maximum(np.abs(np.asarray(b.h) - prev),
                                   np.abs(np.asarray(b.l) - prev)))
        self.stop = O.lag(O.rmean(tr, 15, g), 1, g)
        sm = np.asarray(b.sm)
        entry = np.zeros(m.n, bool)
        dec = np.asarray(m.dec, int)
        if len(dec):
            nxt = dec + 1
            entry[dec] = ((sm[nxt] >= 935) & (sm[nxt] <= 1275)
                          & (sm[dec] >= 930))
        self.base_ok = (entry & ~np.asarray(m.rw, bool) & np.isfinite(self.stop)
                        & (self.stop >= .25) & np.isfinite(self.v))

    def _cached(self, key, make):
        if key not in self.cache:
            self.cache[key] = make()
        return self.cache[key]

    def c15_side(self, side: int) -> np.ndarray:
        return self.c15 & (self.direction15 == side)

    def e03_surprise(self, lookback: int = 20) -> np.ndarray:
        def build():
            forecast = O.lag(O.ewm(np.abs(self.r), lookback, self.market.gid), 15, self.market.gid)
            return _valid_div(np.abs(self.ret15), forecast * np.sqrt(15))
        return self._cached(("E03_ratio", lookback), build)

    def e07_occupation(self, lookback: int = 30) -> np.ndarray:
        def build():
            c = np.asarray(self.market.nq.c, float)
            start = O.lag(c, lookback, self.market.gid)
            # Count closes relative to the completed window's starting close.
            gs = O.group_start(self.market.gid)
            return _occupation_kernel(c, start, gs, lookback)
        return self._cached(("E07_fraction", lookback), build)

    def _e01(self, lookback: int, threshold: float) -> np.ndarray:
        m = self.market
        b = m.nq
        g, sm = m.gid, np.asarray(b.sm)
        v5 = O.rsum(np.where((sm >= 930) & (sm < 1320), b.v, np.nan), 5, g)
        target = _past_clock_quantile(v5, m, lookback, .5)
        out = np.zeros(m.n, np.int8)
        bucket_volume = bucket_return = 0.0
        last: list[float] = []
        prior_group = None
        for i in range(m.n):
            if g[i] != prior_group or sm[i] == 930:
                bucket_volume = bucket_return = 0.0
                last = []
                prior_group = g[i]
            if not (930 <= sm[i] < 1320 and np.isfinite(target[i])
                    and target[i] > 0 and np.isfinite(self.r[i]) and np.isfinite(b.v[i])):
                continue
            bucket_volume += b.v[i]
            bucket_return += self.r[i]
            if bucket_volume >= target[i]:
                last.append(bucket_return)
                last = last[-max(1, int(np.ceil(threshold))):]
                bucket_volume = bucket_return = 0.0
            if len(last) == max(1, int(np.ceil(threshold))) and self.c15[i]:
                side = int(self.direction15[i])
                if all(side * x > 0 for x in last):
                    out[i] = side
        return out

    def _e02(self, lookback: int, threshold: float) -> np.ndarray:
        m = self.market
        c, g = np.asarray(m.nq.c), m.gid
        hi = O.lag(O.rmax(c, lookback, g), 1, g)
        lo = O.lag(O.rmin(c, lookback, g), 1, g)
        barrier = threshold * self.v * c * np.sqrt(15)
        out = np.zeros(m.n, np.int8)
        state = 0
        confirm = reach = 0.0
        last_group = None
        for i in range(m.n):
            if g[i] != last_group:
                state = 0
                last_group = g[i]
            if not (np.isfinite(hi[i]) and np.isfinite(lo[i]) and np.isfinite(barrier[i])):
                continue
            if state == 0:
                down = hi[i] - c[i] >= barrier[i]
                up = c[i] - lo[i] >= barrier[i]
                if down != up:
                    state = -1 if down else 1
                    confirm = c[i]
                    reach = .5 * barrier[i]
            elif state * (c[i] - confirm) >= reach:
                out[i] = state
                state = 0
        return out

    def _e04_alarm(self, threshold: float) -> np.ndarray:
        key = ("E04_alarm", threshold)
        def build():
            out = np.zeros(self.market.n, np.int8)
            sm, g = np.asarray(self.market.nq.sm), self.market.gid
            up = down = 0.0
            fired = False
            prior = None
            for i in range(self.market.n):
                if g[i] != prior or sm[i] == 930:
                    up = down = 0.0
                    fired = False
                    prior = g[i]
                if not 930 <= sm[i] < 1320 or not np.isfinite(self.v[i]) or not np.isfinite(self.r[i]):
                    continue
                z = self.r[i] / self.v[i]
                up = max(0.0, up + z - .5)
                down = max(0.0, down - z - .5)
                if not fired and max(up, down) >= threshold:
                    out[i] = 1 if up >= down else -1
                    fired = True
            return out
        return self._cached(key, build)

    def _e05(self, lookback: int, threshold: float) -> np.ndarray:
        trend = O.ewm(self.r, lookback, self.market.gid)
        sign = np.sign(trend)
        changed = (sign != O.lag(sign, 1, self.market.gid)) & np.isfinite(sign)
        age = O.bars_since(changed, self.market.gid)
        return np.where((age >= 5) & (age <= threshold) & (sign == self.direction15)
                        & self.c15, sign, 0).astype(np.int8)

    def _e06(self, lookback: int, threshold: float) -> np.ndarray:
        m = self.market
        b = m.nq
        sm, g = np.asarray(b.sm), m.gid
        out = np.zeros(m.n, np.int8)
        open_px = np.nan
        first_side = 0
        first_minute = 0
        prior = None
        for i in range(m.n):
            if g[i] != prior or sm[i] == 930:
                open_px = b.o[i] if sm[i] == 930 else np.nan
                first_side = 0
                prior = g[i]
            if not (930 <= sm[i] < 1320 and np.isfinite(open_px) and np.isfinite(self.v[i])):
                continue
            barrier = 2 * self.v[i] * b.c[i] * np.sqrt(lookback)
            if first_side == 0 and abs(b.c[i] - open_px) >= barrier:
                first_side = 1 if b.c[i] > open_px else -1
                first_minute = int(sm[i])
            if first_side and first_minute - 930 <= threshold and self.c15[i] and self.direction15[i] == first_side:
                out[i] = first_side
        return out

    def _e08(self, lookback: int, threshold: float) -> tuple[np.ndarray, np.ndarray]:
        m = self.market
        c, g = np.asarray(m.nq.c), m.gid
        impulse_start = O.lag(c, 15, g)
        out = np.zeros(m.n, np.int8)
        duration = np.full(m.n, np.nan)
        side = 0
        endpoint = magnitude = 0.0
        impulse_i = pullback_i = -1
        prior = None
        for i in range(m.n):
            if g[i] != prior:
                side = 0
                prior = g[i]
            if side and i - impulse_i > lookback + 3:
                side = 0
            if side:
                if pullback_i < 0 and i - impulse_i >= 3 and side * (c[i] - endpoint) <= -threshold * magnitude:
                    pullback_i = i
                if pullback_i >= 0 and i - pullback_i <= lookback and side * (c[i] - endpoint) >= 0:
                    out[i] = side
                    duration[i] = pullback_i - impulse_i
                    side = 0
            if side == 0 and self.c15[i] and np.isfinite(impulse_start[i]):
                side = int(self.direction15[i])
                endpoint = c[i]
                magnitude = abs(c[i] - impulse_start[i])
                impulse_i = i
                pullback_i = -1
        return out, duration

    def _e11(self) -> np.ndarray:
        m = self.market
        b = m.nq
        sm, days = np.asarray(b.sm), np.asarray(b.sday)
        out = np.zeros(m.n, np.int8)
        for d in np.unique(days):
            ix = np.flatnonzero(days == d)
            signs = []
            for lo, hi in ((0, 480), (480, 840), (840, 930)):
                seg = ix[(sm[ix] >= lo) & (sm[ix] < hi)]
                if len(seg) < max(2, (hi-lo)//2) or not np.isfinite(b.o[seg[0]]) or not np.isfinite(b.c[seg[-1]]):
                    signs = []
                    break
                signs.append(int(np.sign(b.c[seg[-1]] - b.o[seg[0]])))
            if len(signs) != 3 or signs[0] == 0 or signs.count(signs[0]) != 3:
                continue
            rth = ix[(sm[ix] >= 930) & (sm[ix] < 1320)]
            hit = rth[self.base_ok[rth] & self.c15[rth]
                      & (self.direction15[rth] == signs[0])]
            if len(hit):
                out[hit[0]] = signs[0]
        return out

    def _e12(self, lookback: int, threshold: float) -> np.ndarray:
        m = self.market
        es_vol = np.maximum(_past_clock_quantile(np.abs(self.er), m, 20, .5),
                            .25 / np.asarray(m.ec, float))
        nq_return = O.rsum(self.r, lookback, m.gid)
        es_return = O.rsum(self.er, lookback, m.gid)
        nq_z = _valid_div(np.abs(nq_return), self.v * np.sqrt(lookback))
        es_z = _valid_div(np.abs(es_return), es_vol * np.sqrt(lookback))
        nq_q = _past_clock_quantile(nq_z, m, 60, threshold)
        es_q = _past_clock_quantile(es_z, m, 60, threshold)
        both = (self.c15 & (nq_z > nq_q) & (es_z > es_q)
                & (np.sign(es_return) == self.direction15)
                & np.asarray(m.evalid) & ~np.asarray(m.es_rw))
        return np.where(both, self.direction15, 0).astype(np.int8)

    def _e13(self, lookback: int, threshold: float) -> np.ndarray:
        m = self.market
        days = np.asarray(m.nq.sday)
        unique, day_idx = np.unique(days, return_inverse=True)
        residual = np.full(m.n, np.nan)
        prev_std = np.full(m.n, np.nan)
        valid = (np.isfinite(self.r) & np.isfinite(self.er)
                 & np.asarray(m.evalid) & ~np.asarray(m.es_rw) & ~np.asarray(m.rw))
        cross = np.bincount(day_idx, weights=np.where(valid, self.r * self.er, 0.0), minlength=len(unique))
        es_var = np.bincount(day_idx, weights=np.where(valid, self.er * self.er, 0.0), minlength=len(unique))
        cross_cum, var_cum = np.r_[0.0, np.cumsum(cross)], np.r_[0.0, np.cumsum(es_var)]
        bounds = np.r_[0, np.flatnonzero(days[1:] != days[:-1]) + 1, m.n]
        for k in range(lookback, len(unique)):
            ix = np.arange(bounds[k], bounds[k+1])
            denominator = float(var_cum[k] - var_cum[k-lookback])
            if denominator <= 0:
                continue
            beta = float((cross_cum[k] - cross_cum[k-lookback]) / denominator)
            prev = np.arange(bounds[k-1], bounds[k])
            prev = prev[valid[prev]]
            if len(prev) < 60:
                continue
            previous_residual = self.r[prev] - beta * self.er[prev]
            previous_15 = np.convolve(previous_residual, np.ones(15), mode="valid")
            scale = float(np.nanstd(previous_15))
            if not np.isfinite(scale) or scale <= 0:
                continue
            residual[ix[valid[ix]]] = self.r[ix[valid[ix]]] - beta * self.er[ix[valid[ix]]]
            prev_std[ix] = scale
        z = O.rsum(residual, 15, m.gid)
        return np.where(np.abs(z) > threshold * prev_std, np.sign(z), 0).astype(np.int8)

    def _e14(self, lookback: int, threshold: float) -> np.ndarray:
        nq = np.sign(O.ewm(self.r, lookback, self.market.gid))
        es = np.sign(O.ewm(self.er, lookback, self.market.gid))
        m = self.market
        out = np.zeros(m.n, np.int8)
        run = 0
        prev = None
        for i in range(m.n):
            if m.gid[i] != prev:
                run = 0
                prev = m.gid[i]
            if not (np.isfinite(nq[i]) and np.isfinite(es[i]) and m.evalid[i]):
                run = 0
                continue
            if nq[i] != 0 and es[i] != 0 and nq[i] != es[i]:
                run += 1
            else:
                if run >= threshold and nq[i] == es[i] == self.direction15[i] and self.c15[i]:
                    out[i] = int(nq[i])
                run = 0
        return out

    def _e15(self, threshold: float) -> np.ndarray:
        alarm = self._e04_alarm(4)
        age = O.bars_since(alarm != 0, self.market.gid)
        last_side = O.last_value_where(alarm != 0, alarm, self.market.gid)
        return np.where(self.c15 & (age >= 5) & (age <= threshold)
                        & (last_side == self.direction15),
                        self.direction15, 0).astype(np.int8)

    def _e16_ratio(self, lookback: int = 120) -> np.ndarray:
        return self._cached(("E16_ratio", lookback), lambda: _valid_div(
            O.ewm(self.r * self.r, 10, self.market.gid),
            O.ewm(self.r * self.r, lookback, self.market.gid)))

    def _e16(self, lookback: int, threshold: float) -> np.ndarray:
        ratio = self._e16_ratio(lookback)
        prior = O.lag(ratio, 1, self.market.gid)
        return np.where(self.c15 & (prior <= threshold) & (ratio > threshold),
                        self.direction15, 0).astype(np.int8)

    def _e17(self, lookback: int, threshold: float) -> np.ndarray:
        g, sm = self.market.gid, np.asarray(self.market.nq.sm)
        five = O.rsum(self.r, 5, g)
        block_end = (sm % 5) == 4
        one_var = O.rsum(self.r * self.r, lookback, g)
        five_var = O.rsum(np.where(block_end, five * five, 0.0), lookback, g)
        ratio = _valid_div(one_var, five_var)
        return np.where(self.c15 & (ratio >= threshold), self.direction15, 0).astype(np.int8)

    def _e18_state(self, lookback: int, threshold: float) -> np.ndarray:
        m = self.market
        b = m.nq
        volume_q = _past_clock_quantile(np.asarray(b.v, float), m, lookback, threshold)
        range_q = _past_clock_quantile(np.asarray(b.h-b.l, float), m, lookback, 1-threshold)
        thin = (np.isfinite(b.v) & (b.v < volume_q) & ((b.h-b.l) > range_q))
        return thin & (O.lag(thin.astype(float), 1, m.gid) == 1)

    def _e19(self, lookback: int, threshold: float) -> np.ndarray:
        m = self.market
        z = _valid_div(self.r, self.v)
        state = np.where(z > 1, 2, np.where(z < -1, 0, 1)).astype(np.int8)
        good = np.isfinite(z)
        days = np.asarray(m.nq.sday)
        unique = np.unique(days)
        out = np.zeros(m.n, np.int8)
        counts = np.zeros((3, 3), float)
        daily = []
        for d in unique:
            ix = np.flatnonzero(days == d)
            if len(daily) >= lookback:
                totals = np.sum(daily[-lookback:], axis=0)
                prob = (np.diag(totals) + 1) / (totals.sum(axis=1) + 3)
                take = ix[self.c15[ix] & good[ix] & (state[ix] != 1)
                          & (prob[state[ix]] >= threshold)
                          & (((state[ix] == 2) & (self.direction15[ix] == 1))
                             | ((state[ix] == 0) & (self.direction15[ix] == -1)))]
                out[take] = self.direction15[take]
            counts = np.zeros((3, 3), float)
            for a, b in zip(ix[:-1], ix[1:]):
                if good[a] and good[b] and m.gid[a] == m.gid[b]:
                    counts[state[a], state[b]] += 1
            daily.append(counts)
        return out

    def _barrier_labels(self, event: np.ndarray, horizon: int = 30,
                        directions: np.ndarray | None = None) -> np.ndarray:
        """Causal *training labels*: only previous-session mature labels are read."""
        m, b = self.market, self.market.nq
        labels = np.full(m.n, np.nan)
        for i in np.flatnonzero(event):
            if i + 1 >= m.n or m.gid[i+1] != m.gid[i] or not self.stop[i] > 0:
                continue
            side = int(self.direction15[i] if directions is None else directions[i])
            if side not in (-1, 1):
                continue
            entry = float(b.o[i+1])
            bound = .5 * self.stop[i]
            last = min(m.n-1, i + horizon)
            for j in range(i+1, last+1):
                if m.gid[j] != m.gid[i]:
                    break
                lose = (entry - b.l[j] >= bound) if side == 1 else (b.h[j] - entry >= bound)
                win = (b.h[j] - entry >= bound) if side == 1 else (entry - b.l[j] >= bound)
                if lose or win:
                    labels[i] = 0.0 if lose else 1.0  # pessimistic same-bar order
                    break
        return labels

    def _e20(self, lookback: int, threshold: float) -> np.ndarray:
        m = self.market
        labels = self._cached("C15_barrier_labels", lambda: self._barrier_labels(self.c15))
        out = np.zeros(m.n, np.int8)
        sm, day = np.asarray(m.nq.sm), np.asarray(m.nq.sday)
        for side in (1, -1):
            values = np.where(self.c15_side(side), labels, np.nan)
            for clock in np.unique(sm):
                ix = np.flatnonzero(sm == clock)
                history: list[float] = []
                prev_day = None
                pending = np.nan
                for i in ix:
                    d = int(day[i])
                    if d != prev_day:
                        if prev_day is not None:
                            history.append(float(pending))
                            if len(history) > lookback:
                                history.pop(0)
                        prev_day = d
                    if self.c15[i] and self.direction15[i] == side:
                        mature = np.asarray(history, float)
                        mature = mature[np.isfinite(mature)]
                        if len(mature) and (mature.sum() + 1) / (len(mature) + 2) >= threshold:
                            out[i] = side
                    pending = values[i]
        return out

    def _e21(self, lookback: int, threshold: float) -> np.ndarray:
        m = self.market
        impact = _valid_div(np.abs(self.ret15), O.rsum(m.nq.v, 15, m.gid))
        impact_q = _past_clock_quantile(impact, m, 60, .8)
        occ = self.e07_occupation(30)
        oriented_occ = np.where(self.direction15 == 1, occ, 1-occ)
        feat = np.column_stack((self.e03_surprise(20), oriented_occ,
                                (impact > impact_q).astype(float)))
        labels = self._cached("C15_barrier_labels", lambda: self._barrier_labels(self.c15))
        probability = _walkforward_probabilities(m, self.c15, feat, labels,
                                                  label_positive=True, training_sessions=lookback)
        return np.where(self.c15 & (probability >= threshold), self.direction15, 0).astype(np.int8)

    def _e22(self) -> np.ndarray:
        occ = self.e07_occupation(30)
        orientation = np.where(self.direction15 == 1, occ, 1-occ)
        return np.where(self.c15 & (orientation >= .8) & (self.e03_surprise(20) >= 1.5),
                        self.direction15, 0).astype(np.int8)

    def _e23(self, lookback: int, threshold: float) -> np.ndarray:
        m, b = self.market, self.market.nq
        days = np.asarray(b.sday)
        unique, day_idx = np.unique(days, return_inverse=True)
        bounds = np.r_[0, np.flatnonzero(days[1:] != days[:-1]) + 1, m.n]
        daily_move = np.bincount(day_idx, weights=np.nan_to_num(self.r*self.r), minlength=len(unique))
        daily_range = np.bincount(day_idx, weights=(np.asarray(b.h)-np.asarray(b.l))**2,
                                  minlength=len(unique))
        daily_count = np.bincount(day_idx, minlength=len(unique))
        move_variance = np.zeros(len(unique))
        range_variance = np.zeros(len(unique))
        for k in range(lookback, len(unique)):
            move_variance[k] = np.median(daily_move[k-lookback:k] / np.maximum(daily_count[k-lookback:k], 1))
            range_variance[k] = np.median(daily_range[k-lookback:k] / np.maximum(daily_count[k-lookback:k], 1))
        return _e23_filter_kernel(np.asarray(b.c, float), np.asarray(b.o, float),
                                  bounds, move_variance, range_variance, self.c15,
                                  self.direction15, lookback, threshold)

    def _e24(self, lookback: int, threshold: float) -> np.ndarray:
        m = self.market
        z = _valid_div(self.r, self.v)
        sm, day = np.asarray(m.nq.sm), np.asarray(m.nq.sday)
        out = np.zeros(m.n, np.int8)
        bins = np.array([-np.inf, -2, -1, -.5, 0, .5, 1, 2, np.inf])
        by_clock = {int(clock): np.flatnonzero(sm == clock) for clock in np.unique(sm)}
        gs = O.group_start(m.gid)
        # Each reference is a concatenation of 20 complete rolling windows.
        # Count the same bins once per window, then add those integer counts.
        # This avoids repeated array concatenation and histogram sorting for
        # every C15 decision bar while retaining the original reference set.
        valid = O.rsum(np.isfinite(z).astype(float), lookback, m.gid) == lookback
        bin_id = np.searchsorted(bins, z, side="right") - 1
        hist = np.column_stack([
            O.rsum((bin_id == k).astype(float), lookback, m.gid)
            for k in range(len(bins) - 1)
        ])
        for i in np.flatnonzero(self.c15):
            if i-lookback+1 < gs[i] or not valid[i]:
                continue
            previous = by_clock[int(sm[i])]
            previous = previous[day[previous] < day[i]][-20:]
            if len(previous) != 20:
                continue
            if not np.all((previous-lookback+1 >= gs[previous]) & valid[previous]):
                continue
            p = hist[i] + .5
            q = hist[previous].sum(axis=0) + .5
            p /= p.sum(); q /= q.sum()
            mix = .5*(p+q)
            js = .5*(np.sum(p*np.log(p/mix)) + np.sum(q*np.log(q/mix)))
            if js > threshold:
                out[i] = self.direction15[i]
        return out

    def _e25(self, lookback: int, threshold: float) -> np.ndarray:
        m = self.market
        z = _valid_div(self.r, self.v)
        extreme_q = _past_clock_quantile(np.abs(z), m, 60, .95)
        extreme = np.isfinite(z) & (np.abs(z) > extreme_q)
        count = O.rsum(extreme.astype(float), lookback, m.gid)
        signed = O.rsum(np.where(extreme, np.sign(z), 0), lookback, m.gid)
        return np.where(self.c15 & (count >= threshold)
                        & (np.sign(signed) == self.direction15), self.direction15, 0).astype(np.int8)

    def _e26(self, lookback: int, threshold: float) -> np.ndarray:
        m, b = self.market, self.market.nq
        sm, g = np.asarray(b.sm), m.gid
        out = np.zeros(m.n, np.int8)
        opened = np.nan
        hi = lo = np.nan
        prior = None
        for i in range(m.n):
            if g[i] != prior or sm[i] == 930:
                prior = g[i]
                opened = b.o[i] if sm[i] == 930 else np.nan
                hi = lo = opened
            if not (930 <= sm[i] < 1320 and np.isfinite(opened)):
                continue
            hi = max(hi, b.h[i]); lo = min(lo, b.l[i])
            if not self.c15[i] or sm[i]-930 < lookback:
                continue
            fav = (hi-opened) if self.direction15[i] == 1 else (opened-lo)
            adv = (opened-lo) if self.direction15[i] == 1 else (hi-opened)
            if fav+adv > 0 and fav/(fav+adv) >= threshold:
                out[i] = self.direction15[i]
        return out

    def _e27(self, lookback: int, threshold: float) -> np.ndarray:
        m, b = self.market, self.market.nq
        g = m.gid
        range15 = O.rmax(b.h, 15, g) - O.rmin(b.l, 15, g)
        first10 = O.lag(O.rmax(b.h, 10, g) - O.rmin(b.l, 10, g), 5, g)
        gs = O.group_start(g)
        return _e27_kernel(range15, first10, self.c15, self.direction15, gs,
                           lookback, threshold)

    def _e28(self, lookback: int, threshold: float) -> np.ndarray:
        m, b = self.market, self.market.nq
        x = np.log(np.asarray(b.v, float) + 1)
        y = np.log(np.abs(self.r) + self.tick_return)
        slope = _rolling_slope(x, y, lookback, m.gid)
        q = _past_clock_quantile(slope, m, 60, threshold)
        return np.where(self.c15 & (slope > q), self.direction15, 0).astype(np.int8)

    def _e29(self, lookback: int, threshold: float) -> np.ndarray:
        m = self.market
        es_vol = np.maximum(_past_clock_quantile(np.abs(self.er), m, 20, .5),
                            .25 / np.asarray(m.ec, float))
        nq_z, es_z = _valid_div(self.r, self.v), _valid_div(self.er, es_vol)
        slope = _rolling_slope(es_z, nq_z, lookback, m.gid)
        days, sm = np.asarray(m.nq.sday), np.asarray(m.nq.sm)
        unique = np.unique(days)
        reference = np.full(m.n, np.nan)
        previous = np.empty(0)
        bounds = np.r_[0, np.flatnonzero(days[1:] != days[:-1]) + 1, m.n]
        for k in range(len(unique)):
            ix = np.arange(bounds[k], bounds[k+1])
            if len(previous) >= 20:
                reference[ix] = np.quantile(previous, threshold)
            previous = slope[ix[(sm[ix] >= 930) & (sm[ix] < 1320) & np.isfinite(slope[ix])]]
        return np.where(self.c15 & (slope > reference) & (np.sign(self.es_ret15) == self.direction15)
                        & np.asarray(m.evalid) & ~np.asarray(m.es_rw), self.direction15, 0).astype(np.int8)

    def _e30(self, lookback: int, threshold: float) -> np.ndarray:
        m = self.market
        recovery, duration = self._e08(10, .5)
        event = recovery != 0
        liquidity = self._e18_state(60, .2).astype(float)
        features = np.column_stack((duration, self._e16_ratio(120), liquidity))
        labels = self._barrier_labels(event, directions=recovery)
        failure_probability = _walkforward_probabilities(m, event, features, labels,
                                                          label_positive=False,
                                                          training_sessions=lookback)
        return np.where(event & (failure_probability <= threshold), recovery, 0).astype(np.int8)

    def interaction_mask(self, interaction: str, side: int) -> np.ndarray:
        """Preregistered C filters, all decided at the completed signal bar."""
        m = self.market
        if interaction == "c15":
            return self.c15_side(side)
        if interaction == "occupation":
            fraction = self.e07_occupation(30)
            return (fraction >= .8) if side == 1 else (fraction <= .2)
        if interaction == "previous_rth_open":
            b = m.nq
            days, sm = np.asarray(b.sday), np.asarray(b.sm)
            unique = np.unique(days)
            out = np.zeros(m.n, bool)
            bounds = np.r_[0, np.flatnonzero(days[1:] != days[:-1]) + 1, m.n]
            previous = 0
            for k in range(len(unique)):
                ix = np.arange(bounds[k], bounds[k+1])
                out[ix] = previous == side
                rth = ix[(sm[ix] >= 930) & (sm[ix] < 1320)]
                previous = (int(np.sign(b.c[rth[-1]] - b.o[rth[0]]))
                            if len(rth) >= 300 else 0)
            return out
        raise ValueError(f"unregistered Stage C interaction: {interaction}")

    def direction(self, family: str, lookback: int | None, threshold: float | None) -> np.ndarray:
        """Return -1/0/+1 state for a complete mechanism; fail closed otherwise."""
        return self._cached(("direction", family, lookback, threshold),
                            lambda: self._direction_uncached(family, lookback, threshold))

    def _direction_uncached(self, family: str, lookback: int | None,
                            threshold: float | None) -> np.ndarray:
        if family not in {f"E{i:02d}" for i in range(1, 31)}:
            raise NotImplementedError(f"{family} has no executable signal yet")
        m = self.market
        g, b = m.gid, m.nq
        side = self.direction15
        if family == "E01":
            out = self._e01(int(lookback), float(threshold))
        elif family == "E02":
            out = self._e02(int(lookback), float(threshold))
        elif family == "E03":
            out = np.where(self.c15 & (self.e03_surprise(int(lookback)) >= float(threshold)), side, 0)
        elif family == "E04":
            out = np.where(self.c15 & (self._e04_alarm(float(threshold)) == side), side, 0)
        elif family == "E05":
            out = self._e05(int(lookback), float(threshold))
        elif family == "E06":
            out = self._e06(int(lookback), float(threshold))
        elif family == "E07":
            fraction = self.e07_occupation(int(lookback))
            out = np.where(self.c15 & (((side == 1) & (fraction >= float(threshold)))
                                         | ((side == -1) & (fraction <= 1 - float(threshold)))), side, 0)
        elif family == "E08":
            out, _ = self._e08(int(lookback), float(threshold))
        elif family == "E09":
            signed = O.rsum(np.sign(self.r) * b.v, int(lookback), g)
            vol = O.rsum(b.v, int(lookback), g)
            imbalance = _valid_div(signed, vol)
            out = np.where(self.c15 & (side * imbalance >= float(threshold)), side, 0)
        elif family == "E10":
            impact = _valid_div(np.abs(self.ret15), O.rsum(b.v, int(lookback), g))
            q80 = _past_clock_quantile(impact, m, 60, float(threshold))
            out = np.where(self.c15 & (impact > q80), side, 0)
        elif family == "E11":
            out = self._e11()
        elif family == "E12":
            out = self._e12(int(lookback), float(threshold))
        elif family == "E13":
            out = self._e13(int(lookback), float(threshold))
        elif family == "E14":
            out = self._e14(int(lookback), float(threshold))
        elif family == "E15":
            out = self._e15(float(threshold))
        elif family == "E16":
            out = self._e16(int(lookback), float(threshold))
        elif family == "E17":
            out = self._e17(int(lookback), float(threshold))
        elif family == "E18":
            out = np.where(self.c15 & self._e18_state(int(lookback), float(threshold)), side, 0)
        elif family == "E19":
            out = self._e19(int(lookback), float(threshold))
        elif family == "E20":
            out = self._e20(int(lookback), float(threshold))
        elif family == "E21":
            out = self._e21(int(lookback), float(threshold))
        elif family == "E22":
            out = self._e22()
        elif family == "E23":
            out = self._e23(int(lookback), float(threshold))
        elif family == "E24":
            out = self._e24(int(lookback), float(threshold))
        elif family == "E25":
            out = self._e25(int(lookback), float(threshold))
        elif family == "E26":
            out = self._e26(int(lookback), float(threshold))
        elif family == "E27":
            out = self._e27(int(lookback), float(threshold))
        elif family == "E28":
            out = self._e28(int(lookback), float(threshold))
        elif family == "E29":
            out = self._e29(int(lookback), float(threshold))
        else:  # E30
            out = self._e30(int(lookback), float(threshold))
        return np.where(self.base_ok & np.isfinite(out), out, 0).astype(np.int8)


def signal_for_spec(market: Market, spec: dict, context: SignalContext | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return long, short and point-stop arrays for a canonical A/B/C spec."""
    if spec.get("stage") not in ("A", "B", "C") or spec.get("side") not in ("long", "short"):
        raise ValueError("only canonical directional A/B/C specs are accepted")
    if spec["stage"] in ("A", "B"):
        if spec not in _canonical_ab_specs():
            raise ValueError("unregistered Stage A/B specification")
    ctx = context if context is not None else SignalContext(market)
    if ctx.market is not market:
        raise ValueError("context belongs to another market")
    if spec["stage"] == "C":
        parent = dict(spec)
        parent.pop("parent_id", None)
        parent.update(stage="B", interaction=None)
        if candidate_id(parent) != spec.get("parent_id"):
            raise ValueError("Stage C parent ID does not match its B specification")
        from quantlab5.v5.candidate_inventory import stage_c_spec
        if stage_c_spec(parent, spec["interaction"]) != spec:
            raise ValueError("unregistered Stage C specification")
    state = ctx.direction(spec["family"], spec["lookback"], spec["threshold"])
    wanted = 1 if spec["side"] == "long" else -1
    mask = state == wanted
    if spec["stage"] == "C":
        mask &= ctx.interaction_mask(spec["interaction"], wanted)
    return (mask if wanted == 1 else np.zeros(market.n, bool),
            mask if wanted == -1 else np.zeros(market.n, bool), ctx.stop.copy())


@lru_cache(maxsize=1)
def _canonical_ab_specs() -> tuple[dict, ...]:
    from quantlab5.v5.candidate_inventory import inventory
    rules = inventory()
    return tuple(rules["stage_a"] + rules["stage_b"])
