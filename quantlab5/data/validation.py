"""Data integrity checks. Serious problems are REPORTED, never silently repaired.

(Copied from quantlab3/data/validation.py. V4 change: quick_check also validates
volume -- negative or non-integral volume is an integrity error; NaN volume is
allowed and means "missing", it is never zero-filled. full_report was removed:
it computed price-jump statistics, which V4 only computes inside an explicit,
stage-gated audit.)
"""
from __future__ import annotations

import numpy as np


class DataIntegrityError(Exception):
    pass


def quick_check(instrument: str, ts, o, h, l, c, v=None) -> None:
    """Run on every load. Raises on anything that would make results wrong."""
    problems = []
    if len(ts) > 1:
        d = np.diff(ts)
        if (d == 0).any():
            problems.append(f"{int((d == 0).sum())} duplicate timestamps")
        if (d < 0).any():
            problems.append(f"{int((d < 0).sum())} out-of-order timestamps")
    if len(ts) and (np.asarray(ts) % 60_000_000_000 != 0).any():
        problems.append("timestamps not aligned to whole minutes")
    for name, a in (("open", o), ("high", h), ("low", l), ("close", c)):
        bad = ~np.isfinite(a) | (a <= 0)
        if bad.any():
            problems.append(f"{int(bad.sum())} non-finite or non-positive {name} prices")
    if (h < np.maximum(o, c) - 1e-9).any():
        problems.append(f"{int((h < np.maximum(o, c) - 1e-9).sum())} bars with high < max(open, close)")
    if (l > np.minimum(o, c) + 1e-9).any():
        problems.append(f"{int((l > np.minimum(o, c) + 1e-9).sum())} bars with low > min(open, close)")
    if (h < l).any():
        problems.append(f"{int((h < l).sum())} bars with high < low")
    if v is not None:
        v = np.asarray(v, dtype="float64")
        if len(v) != len(ts):
            problems.append("volume length differs from timestamps")
        else:
            fin = np.isfinite(v)
            if (v[fin] < 0).any():
                problems.append(f"{int((v[fin] < 0).sum())} negative volume values")
            if (np.floor(v[fin]) != v[fin]).any():
                problems.append("non-integral volume values")
            if np.isinf(v).any():
                problems.append("infinite volume values")
    if problems:
        raise DataIntegrityError(f"{instrument}: " + "; ".join(problems) +
                                 ". Nothing was repaired.")
