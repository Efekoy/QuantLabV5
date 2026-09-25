"""Contract-roll handling for continuous front-contract bars.

The source files are NOT back-adjusted: each bar carries the price of the contract
named in `symbol`, so a roll produces a price discontinuity. V4 therefore treats
every roll as a hard boundary:

  * `Bars.seg` increments whenever `symbol` changes;
  * the engine never holds a position across a segment change (flat at the close of
    the last bar of the old contract, no entry on the first bar of the new one);
  * features that look back across a roll must either reset at the roll or use
    returns that exclude the roll gap (`returns_excluding_rolls`).

Source roll rule (from the data builder's documentation, not re-derived here): each
session holds the outright with the greatest volume in the previous fully covered
session; switches happen only at the session boundary.
"""
from __future__ import annotations

import numpy as np


def roll_indices(seg: np.ndarray) -> np.ndarray:
    """Indices i where bar i is the first bar of a new contract segment."""
    seg = np.asarray(seg)
    if len(seg) < 2:
        return np.zeros(0, dtype=np.int64)
    return (np.nonzero(seg[1:] != seg[:-1])[0] + 1).astype(np.int64)


def same_segment_as_prev(seg: np.ndarray) -> np.ndarray:
    seg = np.asarray(seg)
    out = np.zeros(len(seg), dtype=bool)
    if len(seg) > 1:
        out[1:] = seg[1:] == seg[:-1]
    return out


def returns_excluding_rolls(c: np.ndarray, seg: np.ndarray) -> np.ndarray:
    """Close-to-close log returns with NaN on the first bar of each contract segment."""
    c = np.asarray(c, dtype=np.float64)
    r = np.full(len(c), np.nan)
    if len(c) > 1:
        r[1:] = np.log(c[1:] / c[:-1])
        r[1:][~same_segment_as_prev(seg)[1:]] = np.nan
    return r


def rolls_only_at_session_starts(seg: np.ndarray, sday: np.ndarray) -> bool:
    """True when every contract change coincides with a session change (the source roll rule)."""
    idx = roll_indices(seg)
    sday = np.asarray(sday)
    return bool(np.all(sday[idx] != sday[idx - 1])) if len(idx) else True


def check_roll_boundary_flags(seg: np.ndarray, roll_boundary: np.ndarray, sday: np.ndarray) -> dict:
    """Compare symbol-derived rolls to the source `roll_boundary` flag (structure only, no prices)."""
    rb = np.asarray(roll_boundary, dtype=bool)
    derived = np.zeros(len(rb), dtype=bool)
    derived[roll_indices(seg)] = True
    return {"derived_rolls": int(derived.sum()), "flagged_rolls": int(rb.sum()),
            "flag_matches_derived": bool(np.array_equal(derived, rb)),
            "rolls_only_at_session_start": rolls_only_at_session_starts(seg, sday)}
