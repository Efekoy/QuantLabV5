"""Purging: remove training observations whose information interval overlaps a test interval.

Every observation (a label, an event, a forward-return target) carries
    information_start  -- the first moment whose data the observation depends on
    information_end    -- the last moment whose data the observation depends on
                          (for a forward-return label: the END of the label horizon)

A training observation leaks if [information_start, information_end] intersects any
test interval [test_start, test_end] (closed intervals: touching counts as overlap,
the conservative choice). Leaking observations are purged from training.

Times are int64 (e.g. UTC ns or minutes); only ordering matters.
"""
from __future__ import annotations

import numpy as np


def _check(info_start, info_end):
    s = np.asarray(info_start, dtype=np.int64)
    e = np.asarray(info_end, dtype=np.int64)
    if s.shape != e.shape:
        raise ValueError("information_start and information_end differ in length")
    if (e < s).any():
        raise ValueError("information_end before information_start")
    return s, e


def overlaps(info_start, info_end, intervals) -> np.ndarray:
    """Boolean mask: observation's information interval intersects ANY of `intervals` [(a, b), ...]."""
    s, e = _check(info_start, info_end)
    m = np.zeros(len(s), dtype=bool)
    for a, b in intervals:
        if b < a:
            raise ValueError("interval end before start")
        m |= (s <= b) & (e >= a)
    return m


def purge(train_idx, info_start, info_end, test_intervals) -> np.ndarray:
    """Training indices that remain after purging overlap with the test intervals."""
    train_idx = np.asarray(train_idx, dtype=np.int64)
    leak = overlaps(np.asarray(info_start)[train_idx], np.asarray(info_end)[train_idx], test_intervals)
    return train_idx[~leak]


def leaking(train_idx, info_start, info_end, test_intervals) -> np.ndarray:
    """Training indices that WOULD leak (for diagnostics / tests)."""
    train_idx = np.asarray(train_idx, dtype=np.int64)
    leak = overlaps(np.asarray(info_start)[train_idx], np.asarray(info_end)[train_idx], test_intervals)
    return train_idx[leak]
