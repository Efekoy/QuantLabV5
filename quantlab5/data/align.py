"""Synchronized cross-market alignment (NQ/ES).

(Adapted from quantlab3/data/loader.align_other; now works on Bars and carries volume.)

For primary bar i, the other market's values come ONLY from its bar with the SAME
start minute -- information that exists at the close of bar i. A missing bar is
NaN / valid=False; there is never a forward fill (a stale value would silently
pretend two markets were observed together when they were not).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from quantlab5.data.schema import Bars


@dataclass
class AlignedOther:
    instrument: str
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    v: np.ndarray
    seg: np.ndarray
    valid: np.ndarray


def align_other(bars: Bars, other: Bars) -> AlignedOther:
    n = bars.n
    if other.n == 0:
        valid = np.zeros(n, dtype=bool)
        pos_c = np.zeros(n, dtype=np.int64)
    else:
        pos = np.searchsorted(other.ts, bars.ts)
        pos_c = np.minimum(pos, other.n - 1)
        valid = np.asarray(other.ts)[pos_c] == np.asarray(bars.ts)

    def take(arr, fill, dtype):
        out = np.full(n, fill, dtype=dtype)
        out[valid] = np.asarray(arr)[pos_c[valid]]
        out.setflags(write=False)
        return out

    valid = np.asarray(valid, dtype=bool)
    valid.setflags(write=False)
    return AlignedOther(other.instrument, take(other.o, np.nan, np.float64), take(other.h, np.nan, np.float64),
                        take(other.l, np.nan, np.float64), take(other.c, np.nan, np.float64),
                        take(other.v, np.nan, np.float64), take(other.seg, -1, np.int32), valid)
