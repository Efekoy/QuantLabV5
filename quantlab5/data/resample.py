"""Causal higher-timeframe bars built from 1-minute bars.

(Copied from quantlab3/data/resample.py. V4 changes: volume is aggregated (sum; NaN
if any minute's volume is missing), buckets that straddle a session boundary are
flagged (`sday == -1`), and `htf_for_bars` replaces `htf_for_view`.)

A k-minute bar covers clock-aligned [T, T+k). It becomes AVAILABLE only when
it has fully closed, i.e. at the close of the 1-minute bar starting T+k-1 (or
at the first bar after T+k if that last minute is missing).

For every 1-minute bar t we expose `last[t]`: the index of the most recent
k-minute bar that had completely closed by the close of bar t. Every value a
strategy reads through `last[t]` was therefore knowable at bar t's close.

Buckets are aligned on UTC minutes. New York is always a whole number of hours
from UTC, so for k in {5, 15, 30, 60} the boundaries coincide with New York
clock boundaries (09:30, 10:00, ...) in both summer and winter time.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numba import njit


@dataclass
class HTF:
    k: int
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    v: np.ndarray        # summed volume; NaN if any minute in the bucket has missing volume
    seg: np.ndarray      # contract segment; -1 if the bucket straddles a roll
    sday: np.ndarray     # session day of the bucket; -1 if the bucket straddles a session boundary
    last: np.ndarray     # per 1-minute bar: index of last COMPLETED bucket, -1 if none

    @property
    def fresh(self) -> np.ndarray:
        """True on the 1-minute bar where a new completed bucket first becomes available."""
        f = np.zeros(len(self.last), dtype=bool)
        f[1:] = (self.last[1:] != self.last[:-1]) & (self.last[1:] >= 0)
        if len(f):
            f[0] = self.last[0] >= 0
        return f


@njit(cache=True)
def _group(bucket, o, h, l, c, v, seg, sday):
    n = len(bucket)
    if n == 0:
        e = np.empty(0, np.float64)
        return np.empty(0, np.int64), e, e, e, e, e, np.empty(0, np.int32), np.empty(0, np.int32)
    m = 1
    for i in range(1, n):
        if bucket[i] != bucket[i - 1]:
            m += 1
    bid = np.empty(m, np.int64)
    bo = np.empty(m, np.float64)
    bh = np.empty(m, np.float64)
    bl = np.empty(m, np.float64)
    bc = np.empty(m, np.float64)
    bv = np.empty(m, np.float64)
    bs = np.empty(m, np.int32)
    bd = np.empty(m, np.int32)
    j = 0
    bid[0] = bucket[0]; bo[0] = o[0]; bh[0] = h[0]; bl[0] = l[0]; bc[0] = c[0]; bv[0] = v[0]
    bs[0] = seg[0]; bd[0] = sday[0]
    for i in range(1, n):
        if bucket[i] != bucket[i - 1]:
            j += 1
            bid[j] = bucket[i]; bo[j] = o[i]; bh[j] = h[i]; bl[j] = l[i]; bc[j] = c[i]; bv[j] = v[i]
            bs[j] = seg[i]; bd[j] = sday[i]
        else:
            if h[i] > bh[j]:
                bh[j] = h[i]
            if l[i] < bl[j]:
                bl[j] = l[i]
            bc[j] = c[i]
            bv[j] = bv[j] + v[i]
            if seg[i] != bs[j]:
                bs[j] = -1
            if sday[i] != bd[j]:
                bd[j] = -1
    return bid, bo, bh, bl, bc, bv, bs, bd


def build_htf(tmin, o, h, l, c, seg, sday, k: int, v=None) -> HTF:
    if k < 1:
        raise ValueError("k must be >= 1")
    tmin = np.asarray(tmin, dtype=np.int64)
    if len(tmin) > 1 and (np.diff(tmin) <= 0).any():
        raise ValueError("timestamps must be strictly increasing")
    vv = np.full(len(tmin), np.nan) if v is None else np.asarray(v, np.float64)
    bucket = tmin // k
    bid, bo, bh, bl, bc, bv, bs, bd = _group(bucket, np.asarray(o, np.float64), np.asarray(h, np.float64),
                                             np.asarray(l, np.float64), np.asarray(c, np.float64), vv,
                                             np.asarray(seg, np.int32), np.asarray(sday, np.int32))
    completed_id = (tmin + 1) // k - 1          # every bucket <= this id has fully closed
    last = np.searchsorted(bid, completed_id, side="right") - 1
    return HTF(k, bo, bh, bl, bc, bv, bs, bd, last.astype(np.int64))


def htf_for_bars(bars, k: int) -> HTF:
    return build_htf(bars.tmin, bars.o, bars.h, bars.l, bars.c, bars.seg, bars.sday, k, v=bars.v)


def htf_value_at_minute(htf: HTF, arr: np.ndarray) -> np.ndarray:
    """Broadcast a per-bucket array to 1-minute bars using only COMPLETED buckets (NaN before any)."""
    out = np.full(len(htf.last), np.nan)
    ok = htf.last >= 0
    out[ok] = np.asarray(arr, dtype=np.float64)[htf.last[ok]]
    return out
