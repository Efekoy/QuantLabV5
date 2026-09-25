"""Deterministic cleaning pipeline v1, designed on DISCOVERY only (see V4_DATA_AUDIT.md).

The DISCOVERY audit found no invalid bars (0 duplicate/out-of-order/misaligned timestamps, 0 OHLC
violations, 0 off-tick prices, 0 missing/negative/zero volumes, no bars in the 17:00-18:00 break).
So v1 changes NO prices and removes NO bars. It only adds causal quality flags:

  roll_window[i]   True while the held contract is the EXPIRING quarterly contract and the session
                   date is on or after day ROLL_WINDOW_FIRST_DAY of an expiry month (Mar/Jun/Sep/Dec).
                   Reason: the source volume is SINGLE-CONTRACT front volume. In the session before
                   each roll the held contract's volume collapses to ~40% of normal (liquidity has
                   moved to the next contract). The roll date depends on that same session's volume,
                   so the degraded session cannot be identified causally. The whole calendar window
                   is flagged instead (conservative, causal). Volume-derived features are masked and
                   volume baselines skip these sessions.

Missing minutes are ABSENT rows, never filled. There are no zero-volume rows: a minute with no
trades has no bar.

The identical frozen function is applied unchanged to later partitions when their stages open.
"""
from __future__ import annotations

import numpy as np

CLEANING_VERSION = "clean_v1_2026-09-23"
ROLL_WINDOW_FIRST_DAY = 8
EXPIRY_CODES = {"H": 3, "M": 6, "U": 9, "Z": 12}


def contract_month(symbols) -> np.ndarray:
    """Delivery month (3/6/9/12) from symbols like 'NQZ8' / 'ESH1'; 0 if unrecognised."""
    sym = np.asarray(symbols).astype(str)
    uniq, inv = np.unique(sym, return_inverse=True)
    months = np.array([EXPIRY_CODES.get(s[-2], 0) if len(s) >= 2 else 0 for s in uniq], dtype=np.int8)
    return months[inv]


def roll_window_mask(sday: np.ndarray, symbols) -> np.ndarray:
    d = np.asarray(sday, dtype="int64").astype("datetime64[D]")
    month = (d.astype("datetime64[M]").astype(np.int64) % 12 + 1).astype(np.int8)
    dom = (d - d.astype("datetime64[M]")).astype(np.int64) + 1
    cm = contract_month(symbols)
    return (cm == month) & np.isin(month, (3, 6, 9, 12)) & (dom >= ROLL_WINDOW_FIRST_DAY)
