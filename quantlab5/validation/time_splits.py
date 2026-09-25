"""Chronological sub-period utilities for INTERNAL DISCOVERY validation.

These divide a set of session dates (normally DISCOVERY's) into chronological
sub-periods. They are NOT data partitions: they never touch files, never widen what
the stage gate allows, and `within_partition` lets callers assert that every split
stays inside the partition they loaded.

  calendar_year_splits      year-by-year stability
  walk_forward_splits       rolling or anchored train -> test windows (no overlap,
                            test always strictly after train; optional gap)
  cscv_blocks / cscv_splits S contiguous blocks and all C(S, S/2) train/test
                            combinations for CSCV / PBO-style diagnostics

Random K-fold over time series is deliberately NOT provided.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from itertools import combinations

import numpy as np


@dataclass(frozen=True)
class Split:
    name: str
    train: tuple[date, date] | None
    test: tuple[date, date]


def _dates(sessions) -> np.ndarray:
    d = np.unique(np.asarray(sessions, dtype="datetime64[D]"))
    if len(d) == 0:
        raise ValueError("no sessions")
    return d


def _pd(x) -> date:
    return np.datetime64(x, "D").astype(object)


def within_partition(splits, first: date, last: date) -> bool:
    for s in splits:
        for iv in (s.train, s.test):
            if iv is not None and (iv[0] < first or iv[1] > last):
                return False
    return True


def calendar_year_splits(sessions) -> list[Split]:
    d = _dates(sessions)
    years = d.astype("datetime64[Y]").astype(int) + 1970
    out = []
    for y in np.unique(years):
        dy = d[years == y]
        out.append(Split(f"Y{y}", None, (_pd(dy[0]), _pd(dy[-1]))))
    return out


def walk_forward_splits(sessions, train_sessions: int, test_sessions: int, step: int | None = None,
                        anchored: bool = False, gap_sessions: int = 0) -> list[Split]:
    d = _dates(sessions)
    step = step or test_sessions
    if min(train_sessions, test_sessions, step) < 1 or gap_sessions < 0:
        raise ValueError("bad walk-forward sizes")
    out = []
    t0 = train_sessions
    k = 0
    while t0 + gap_sessions + test_sessions <= len(d):
        tr_a = 0 if anchored else t0 - train_sessions
        tr = (_pd(d[tr_a]), _pd(d[t0 - 1]))
        te_a = t0 + gap_sessions
        te = (_pd(d[te_a]), _pd(d[te_a + test_sessions - 1]))
        out.append(Split(f"WF{k:03d}", tr, te))
        t0 += step
        k += 1
    return out


def cscv_blocks(sessions, n_blocks: int) -> list[tuple[date, date]]:
    if n_blocks < 2 or n_blocks % 2:
        raise ValueError("n_blocks must be an even number >= 2")
    d = _dates(sessions)
    if len(d) < n_blocks:
        raise ValueError("fewer sessions than blocks")
    parts = np.array_split(d, n_blocks)
    return [(_pd(p[0]), _pd(p[-1])) for p in parts]


def cscv_splits(sessions, n_blocks: int) -> list[tuple[tuple[int, ...], tuple[int, ...]]]:
    """All C(S, S/2) (train_blocks, test_blocks) index combinations, in deterministic order."""
    cscv_blocks(sessions, n_blocks)
    idx = tuple(range(n_blocks))
    out = []
    for tr in combinations(idx, n_blocks // 2):
        te = tuple(i for i in idx if i not in tr)
        out.append((tr, te))
    return out
