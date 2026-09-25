"""Embargo: after each test interval, also drop training observations that START within
an embargo period, because serially correlated information (volatility, positioning)
from the test period can still be present in data shortly after it.

    embargoed if  test_end < information_start <= test_end + embargo

Use together with purging:  purge_and_embargo(...)  = purge, then embargo.
"""
from __future__ import annotations

import numpy as np

from quantlab5.validation.purging import purge


def embargo_mask(info_start, test_intervals, embargo: int) -> np.ndarray:
    if embargo < 0:
        raise ValueError("embargo must be >= 0")
    s = np.asarray(info_start, dtype=np.int64)
    m = np.zeros(len(s), dtype=bool)
    for _a, b in test_intervals:
        m |= (s > b) & (s <= b + embargo)
    return m


def apply_embargo(train_idx, info_start, test_intervals, embargo: int) -> np.ndarray:
    train_idx = np.asarray(train_idx, dtype=np.int64)
    m = embargo_mask(np.asarray(info_start)[train_idx], test_intervals, embargo)
    return train_idx[~m]


def purge_and_embargo(train_idx, info_start, info_end, test_intervals, embargo: int) -> np.ndarray:
    kept = purge(train_idx, info_start, info_end, test_intervals)
    return apply_embargo(kept, info_start, test_intervals, embargo)
