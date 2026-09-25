"""Causal, group-aware rolling primitives (numba). Every output at bar i uses bars <= i only.

A "group" is a contiguous run of bars from the same session AND contract segment. A window
that would reach before the start of the current group yields NaN (never mixes sessions/rolls),
unless the function says otherwise.
"""
from __future__ import annotations

import numpy as np
from numba import njit


def group_ids(sday, seg) -> np.ndarray:
    sday = np.asarray(sday)
    seg = np.asarray(seg)
    br = np.zeros(len(sday), dtype=bool)
    if len(sday) > 1:
        br[1:] = (sday[1:] != sday[:-1]) | (seg[1:] != seg[:-1])
    return np.cumsum(br).astype(np.int64)


_GS_CACHE: list = []          # [(gid object, group_start array)] -- identity-keyed, tiny, performance only


def group_start(gid) -> np.ndarray:
    """Index of the first bar of each bar's group (memoised on the identity of the gid array)."""
    for g, gs in _GS_CACHE:
        if g is gid:
            return gs
    ga = np.asarray(gid)
    first = np.ones(len(ga), dtype=bool)
    first[1:] = ga[1:] != ga[:-1]
    idx = np.where(first, np.arange(len(ga)), 0)
    gs = np.maximum.accumulate(idx)
    gs.setflags(write=False)
    if isinstance(gid, np.ndarray):
        _GS_CACHE.insert(0, (gid, gs))
        del _GS_CACHE[4:]
    return gs


def pos_in_group(gid) -> np.ndarray:
    return np.arange(len(gid)) - group_start(gid)


def lag(x, n, gid):
    x = np.asarray(x, dtype=np.float64)
    out = np.full(len(x), np.nan)
    if 0 < n < len(x):
        # groups are contiguous, so gid[i] == gid[i-n]  <=>  i - group_start[i] >= n
        ok = (np.arange(n, len(x)) - group_start(gid)[n:]) >= n
        out[n:] = np.where(ok, x[:-n], np.nan)
    elif n == 0:
        out[:] = x
    return out


def diff1(x, gid):
    return np.asarray(x, dtype=np.float64) - lag(x, 1, gid)


@njit(cache=True)
def _group_prefix(x, gstart):
    """Prefix sums of finite x and finite counts, restarting at each group start (group-local, so the
    result depends only on the group's own bars -- never on where the series happens to begin)."""
    n = len(x)
    ps = np.empty(n + 1)
    pc = np.empty(n + 1, np.int64)
    ps[0] = 0.0
    pc[0] = 0
    acc = 0.0
    cnt = 0
    for i in range(n):
        if i == gstart[i]:
            acc = 0.0
            cnt = 0
        v = x[i]
        if v == v:
            acc += v
            cnt += 1
        ps[i + 1] = acc
        pc[i + 1] = cnt
    return ps, pc


@njit(cache=True)
def _rsum(x, n, gstart, need):
    N = len(x)
    ps, pc = _group_prefix(x, gstart)
    out = np.full(N, np.nan)
    for i in range(N):
        lo = i - n + 1
        if lo < gstart[i]:
            continue
        if lo == gstart[i]:
            s = ps[i + 1]
            c = pc[i + 1]
        else:
            s = ps[i + 1] - ps[lo]
            c = pc[i + 1] - pc[lo]
        if c >= need:
            out[i] = s
    return out


def rsum(x, n, gid, min_frac: float = 1.0):
    """Sum of x[i-n+1..i] within the group; NaNs count as missing. NaN if fewer than min_frac*n finite."""
    need = max(1, int(np.ceil(min_frac * n)))
    return _rsum(np.asarray(x, dtype=np.float64), int(n), group_start(gid), need)


def rmean(x, n, gid, min_frac: float = 1.0):
    x = np.asarray(x, dtype=np.float64)
    s = rsum(x, n, gid, min_frac)
    c = rsum(np.isfinite(x).astype(np.float64), n, gid, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return s / c


def rstd(x, n, gid, min_frac: float = 1.0):
    m = rmean(x, n, gid, min_frac)
    m2 = rmean(np.asarray(x, dtype=np.float64) ** 2, n, gid, min_frac)
    return np.sqrt(np.maximum(m2 - m * m, 0.0))


@njit(cache=True)
def _rmaxmin(x, n, gstart, want_max):
    """Rolling max/min of the FINITE values in x[i-n+1..i] (NaN if the window leaves the group, or no finite
    value). O(N) monotonic deque; returns exactly the same values as the direct O(N*n) scan."""
    N = len(x)
    out = np.full(N, np.nan)
    dq = np.empty(N, np.int64)
    head = 0
    tail = 0
    for i in range(N):
        if i == gstart[i]:
            head = 0
            tail = 0
        v = x[i]
        if v == v:
            if want_max:
                while tail > head and x[dq[tail - 1]] <= v:
                    tail -= 1
            else:
                while tail > head and x[dq[tail - 1]] >= v:
                    tail -= 1
            dq[tail] = i
            tail += 1
        lo = i - n + 1
        while tail > head and dq[head] < lo:
            head += 1
        if lo < gstart[i]:
            continue
        if tail > head:
            out[i] = x[dq[head]]
    return out


def rmax(x, n, gid):
    return _rmaxmin(np.asarray(x, np.float64), int(n), group_start(gid), True)


def rmin(x, n, gid):
    return _rmaxmin(np.asarray(x, np.float64), int(n), group_start(gid), False)


@njit(cache=True)
def _ewm(x, alpha, gstart, min_obs):
    out = np.full(len(x), np.nan)
    m = np.nan
    cnt = 0
    for i in range(len(x)):
        if i == gstart[i]:
            m = np.nan
            cnt = 0
        v = x[i]
        if v == v:
            m = v if m != m else (1.0 - alpha) * m + alpha * v
            cnt += 1
        if cnt >= min_obs:
            out[i] = m
    return out


def ewm(x, span, gid, min_obs=None):
    alpha = 2.0 / (span + 1.0)
    return _ewm(np.asarray(x, np.float64), alpha, group_start(gid), int(min_obs or max(2, span // 2)))


@njit(cache=True)
def _ewm_global(x, alpha, seg, min_obs):
    """EWMA that continues across sessions but resets at contract rolls."""
    out = np.full(len(x), np.nan)
    m = np.nan
    cnt = 0
    for i in range(len(x)):
        if i > 0 and seg[i] != seg[i - 1]:
            m = np.nan
            cnt = 0
        v = x[i]
        if v == v:
            m = v if m != m else (1.0 - alpha) * m + alpha * v
            cnt += 1
        if cnt >= min_obs:
            out[i] = m
    return out


def ewm_across_sessions(x, span, seg, min_obs=None):
    return _ewm_global(np.asarray(x, np.float64), 2.0 / (span + 1.0), np.asarray(seg, np.int64),
                       int(min_obs or max(2, span // 2)))


@njit(cache=True)
def _cum_restart(x, br):
    out = np.empty(len(x))
    acc = 0.0
    for i in range(len(x)):
        if br[i]:
            acc = 0.0
        acc += x[i]
        out[i] = acc
    return out


def cum_in_group(x, gid, start_mask=None):
    """Cumulative sum within group (NaN treated as 0); restarts where start_mask is True. Group-local."""
    x = np.nan_to_num(np.asarray(x, dtype=np.float64))
    br = np.ones(len(x), dtype=bool)
    br[1:] = gid[1:] != gid[:-1]
    if start_mask is not None:
        br |= np.asarray(start_mask, dtype=bool)
    return _cum_restart(x, br)


def last_value_where(mask, x, gid):
    """At each bar: the value of x at the most recent bar (<= i, same group) where mask is True; else NaN."""
    mask = np.asarray(mask, dtype=bool)
    idx = np.where(mask, np.arange(len(mask)), -1)
    idx = np.maximum.accumulate(idx)
    out = np.full(len(mask), np.nan)
    ok = idx >= 0
    ok[ok] &= gid[idx[ok]] == gid[ok]
    out[ok] = np.asarray(x, np.float64)[idx[ok]]
    return out


def bars_since(mask, gid):
    mask = np.asarray(mask, dtype=bool)
    idx = np.where(mask, np.arange(len(mask)), -1)
    idx = np.maximum.accumulate(idx)
    out = np.full(len(mask), np.nan)
    ok = idx >= 0
    ok[ok] &= gid[idx[ok]] == gid[ok]
    out[ok] = (np.arange(len(mask)) - idx)[ok]
    return out


@njit(cache=True)
def _path_stats(c, n, gstart):
    """Per window of n+1 closes ending at i: max retracement against net direction, reversal count,
    directional bar fraction, longest directional run, largest same-direction step share,
    top-3 step share of total path, early/late thirds' share of net move."""
    N = len(c)
    retr = np.full(N, np.nan)
    revs = np.full(N, np.nan)
    dfrac = np.full(N, np.nan)
    run = np.full(N, np.nan)
    big1 = np.full(N, np.nan)
    top3 = np.full(N, np.nan)
    early = np.full(N, np.nan)
    late = np.full(N, np.nan)
    for i in range(N):
        lo = i - n
        if lo < gstart[i]:
            continue
        net = c[i] - c[lo]
        s = 1.0 if net >= 0 else -1.0
        peak = c[lo]
        worst = 0.0
        nrev = 0
        ndir = 0
        best_run = 0
        cur = 0
        prev_sign = 0.0
        path = 0.0
        m1 = 0.0
        m2 = 0.0
        m3 = 0.0
        mx = 0.0
        for j in range(lo + 1, i + 1):
            d = c[j] - c[j - 1]
            ad = abs(d)
            path += ad
            if ad > m1:
                m3 = m2
                m2 = m1
                m1 = ad
            elif ad > m2:
                m3 = m2
                m2 = ad
            elif ad > m3:
                m3 = ad
            if s * d > mx:
                mx = s * d
            sg = 1.0 if d > 0 else (-1.0 if d < 0 else 0.0)
            if sg != 0.0:
                if prev_sign != 0.0 and sg != prev_sign:
                    nrev += 1
                prev_sign = sg
            if sg == s:
                ndir += 1
                cur += 1
                if cur > best_run:
                    best_run = cur
            elif sg != 0.0:
                cur = 0
            if s * (c[j] - peak) > 0:
                peak = c[j]
            dd = s * (peak - c[j])
            if dd > worst:
                worst = dd
        an = abs(net)
        retr[i] = worst / an if an > 0 else np.nan
        revs[i] = nrev / n
        dfrac[i] = ndir / n
        run[i] = best_run
        big1[i] = mx / an if an > 0 else np.nan
        top3[i] = (m1 + m2 + m3) / path if path > 0 else np.nan
        k1 = lo + n // 3
        k2 = lo + (2 * n) // 3
        early[i] = (c[k1] - c[lo]) / net if an > 0 else np.nan
        late[i] = (c[i] - c[k2]) / net if an > 0 else np.nan
    return retr, revs, dfrac, run, big1, top3, early, late


def path_stats(c, n, gid):
    return _path_stats(np.asarray(c, np.float64), int(n), group_start(gid))


def rolling_ols(y, n, gid):
    """OLS of y on time over the last n bars: (slope, t-stat, R^2, residual sd). Closed form."""
    y = np.asarray(y, dtype=np.float64)
    t = pos_in_group(gid).astype(np.float64)          # local time: no global-origin cancellation
    sy = rsum(y, n, gid)
    sty = rsum(t * y, n, gid)
    syy = rsum(y * y, n, gid)
    st = rsum(t, n, gid)
    stt = rsum(t * t, n, gid)
    with np.errstate(invalid="ignore", divide="ignore"):
        sxx = stt - st * st / n
        sxy = sty - st * sy / n
        syy_c = syy - sy * sy / n
        slope = sxy / sxx
        ssr = np.maximum(syy_c - slope * sxy, 0.0)
        r2 = np.where(syy_c > 0, 1.0 - ssr / syy_c, np.nan)
        se = np.sqrt(ssr / max(n - 2, 1) / sxx)
        tstat = slope / se
        resid_sd = np.sqrt(ssr / max(n - 2, 1))
    tstat = np.where(np.isfinite(tstat), tstat, np.nan)
    return slope, np.clip(tstat, -50, 50), r2, resid_sd


def rolling_corr(x, y, n, gid):
    mx, my = rmean(x, n, gid), rmean(y, n, gid)
    mxy = rmean(np.asarray(x) * np.asarray(y), n, gid)
    sx, sy = rstd(x, n, gid), rstd(y, n, gid)
    with np.errstate(invalid="ignore", divide="ignore"):
        return (mxy - mx * my) / (sx * sy)


def rolling_beta(y, x, n, gid):
    mx, my = rmean(x, n, gid), rmean(y, n, gid)
    mxy = rmean(np.asarray(x) * np.asarray(y), n, gid)
    vx = rstd(x, n, gid) ** 2
    with np.errstate(invalid="ignore", divide="ignore"):
        return (mxy - mx * my) / vx
