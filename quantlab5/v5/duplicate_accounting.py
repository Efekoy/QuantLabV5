"""Outcome-blind exact signal duplicate accounting for future V5 market runs."""
from __future__ import annotations

from hashlib import sha256
from dataclasses import dataclass

import numpy as np


def signal_fingerprint(long_mask: np.ndarray, short_mask: np.ndarray,
                       execution_key: str) -> str:
    """Hash same-clock signal paths and execution semantics, including all zeros."""
    lg = np.asarray(long_mask, dtype=bool)
    sh = np.asarray(short_mask, dtype=bool)
    if lg.ndim != 1 or lg.shape != sh.shape or not execution_key:
        raise ValueError("invalid signal masks or execution key")
    h = sha256()
    h.update(len(lg).to_bytes(8, "little"))
    h.update(np.packbits(lg).tobytes())
    h.update(np.packbits(sh).tobytes())
    h.update(execution_key.encode("utf-8"))
    return h.hexdigest()


def exact_duplicate_map(rows) -> dict[str, str]:
    """Map every candidate ID to its first identical signal+execution ID.

    `rows` contains (candidate_id, long_mask, short_mask, execution_key) in
    canonical inventory order. Empty-signal rules are still recorded, never
    silently omitted. This is exact identity, not behavioral correlation.
    """
    first: dict[str, str] = {}
    out: dict[str, str] = {}
    for cid, lg, sh, execution in rows:
        if cid in out:
            raise ValueError(f"duplicate candidate ID: {cid}")
        key = signal_fingerprint(lg, sh, execution)
        out[cid] = first.setdefault(key, cid)
    return out


def behavioral_duplicate_map(ids, daily_r: np.ndarray, *, threshold: float = 0.85) -> dict[str, str]:
    """Annotate highly correlated daily paths without removing any candidate.

    A candidate is mapped to the first canonical ID in its connected behavior
    component. Correlation is computed on a common calendar including zero days.
    Constant paths are related only when exactly equal, because their Pearson
    correlation is undefined. The caller retains every ID for scientific gates.
    """
    keys = tuple(str(x) for x in ids)
    x = np.asarray(daily_r, dtype=float)
    if (x.ndim != 2 or x.shape[1] != len(keys) or len(set(keys)) != len(keys)
            or len(x) < 3 or not np.isfinite(x).all() or not 0 < threshold <= 1):
        raise ValueError("invalid behavior paths, IDs or threshold")
    parent = list(range(len(keys)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    centered = x - x.mean(axis=0)
    norms = np.sqrt(np.sum(centered * centered, axis=0))
    for i in range(len(keys)):
        for j in range(i):
            if norms[i] == 0 or norms[j] == 0:
                same = np.array_equal(x[:, i], x[:, j])
            else:
                same = float(np.dot(centered[:, i], centered[:, j]) / (norms[i] * norms[j])) >= threshold
            if same:
                ri, rj = root(i), root(j)
                parent[max(ri, rj)] = min(ri, rj)
    return {key: keys[root(i)] for i, key in enumerate(keys)}


@dataclass(frozen=True)
class PairSimilarity:
    left_id: str
    right_id: str
    exact_signals: bool
    exact_entries: bool
    same_direction_entry_jaccard: float
    trade_stream_overlap: float
    daily_pnl_correlation: float | None
    highly_overlapping: bool
    behaviorally_similar: bool
    simultaneous_position_overlap: float = 0.0


def _position_overlap(a, b) -> float:
    """Fraction of the smaller executed position-time shared by two rules."""
    if getattr(a, "exit_indices", None) is None or getattr(b, "exit_indices", None) is None:
        return 0.0
    ae, ax = np.asarray(a.entry_indices, int), np.asarray(a.exit_indices, int)
    be, bx = np.asarray(b.entry_indices, int), np.asarray(b.exit_indices, int)
    if len(ae) != len(ax) or len(be) != len(bx) or np.any(ax < ae) or np.any(bx < be):
        raise ValueError("invalid executed position intervals")
    if not len(ae) or not len(be):
        return 0.0
    i = j = shared = 0
    while i < len(ae) and j < len(be):
        shared += max(0, min(int(ax[i]), int(bx[j])) - max(int(ae[i]), int(be[j])) + 1)
        if ax[i] <= bx[j]:
            i += 1
        else:
            j += 1
    smaller = min(int(np.sum(ax-ae+1)), int(np.sum(bx-be+1)))
    return shared / smaller if smaller else 0.0


def pairwise_duplicate_analysis(records, *, entry_overlap_threshold: float = .8,
                                pnl_correlation_threshold: float = .85) -> tuple[PairSimilarity, ...]:
    """Outcome-blind annotations; returns pairs, never a filtered candidate set.

    Each record supplies ID, signal hash, executed entry indices/sides and daily
    net R on one common session grid. Same-direction entry Jaccard divides by
    the union; stream overlap divides by the smaller trade count. An empty pair
    has zero overlap even though both execution paths are exactly empty.
    """
    rows = tuple(records)
    if len({r.candidate_id for r in rows}) != len(rows):
        raise ValueError("duplicate candidate ID")
    out = []
    for i, a in enumerate(rows):
        ea = set(zip(map(int, a.entry_indices), map(int, a.trade_sides)))
        for b in rows[i+1:]:
            eb = set(zip(map(int, b.entry_indices), map(int, b.trade_sides)))
            common = len(ea & eb)
            union = len(ea | eb)
            jaccard = common / union if union else 0.0
            overlap = common / min(len(ea), len(eb)) if ea and eb else 0.0
            x, y = np.asarray(a.daily_r, float), np.asarray(b.daily_r, float)
            if x.shape != y.shape:
                raise ValueError("daily P&L calendars differ")
            corr = (float(np.corrcoef(x, y)[0, 1])
                    if np.std(x) > 0 and np.std(y) > 0 else None)
            exact_entries = np.array_equal(a.entry_indices, b.entry_indices) and np.array_equal(a.trade_sides, b.trade_sides)
            similar = corr is not None and corr >= pnl_correlation_threshold
            position_overlap = _position_overlap(a, b)
            if (a.signal_hash == b.signal_hash or exact_entries or common or similar or position_overlap):
                out.append(PairSimilarity(a.candidate_id, b.candidate_id,
                                          a.signal_hash == b.signal_hash, exact_entries,
                                          jaccard, overlap, corr,
                                          overlap >= entry_overlap_threshold, similar,
                                          position_overlap))
    return tuple(out)
