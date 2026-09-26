"""Synthetic-only discovery nomination and independent holdout confirmation.

The four columns per family are related rule streams. Every statistic is formed
from common-calendar daily R; duplicate trades never become independent rows.
Null references are independent synthetic session worlds with the same joint
dependence. This is an architecture experiment, not market-level A/B/C replay.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import norm

from quantlab5.v5.hierarchy import deterministic_medoid, holm_adjust
from quantlab5.v5.inference import hac_t


@dataclass(frozen=True)
class Nomination:
    families: tuple[int, ...]
    representative: tuple[int, ...]
    qualified: tuple[int, ...]
    behavioral_duplicate_of: tuple[int, ...] = ()


def discovery_screen(daily: np.ndarray, counts: np.ndarray, *, stress_r: float = .02,
                     min_events: int = 120, corr_limit: float = .85) -> Nomination:
    """Frozen economic/stability screen, no significance claim or numeric cap.

    Three positive neighbors, positive daily family R in both halves, positive
    stress-cost family R, enough observations, then a discovery-only medoid.
    Cross-family representatives with correlation >= limit are annotated as
    related to the earlier canonical family. Every qualifier advances.
    """
    x, c = np.asarray(daily, float), np.asarray(counts, float)
    if x.ndim != 2 or x.shape != c.shape or x.shape[1] % 4 or len(x) < 40:
        raise ValueError("expected day x (family*4) daily R and counts")
    f = x.shape[1] // 4
    fam = x.reshape(len(x), f, 4)
    cnt = c.reshape(len(x), f, 4)
    h = len(x) // 2
    qualified = []
    for j in range(f):
        a, n = fam[:, j], cnt[:, j]
        if (np.count_nonzero(a.mean(axis=0) > 0) >= 3 and a[:h].mean() > 0
                and a[h:].mean() > 0 and (a - stress_r * n).mean() > 0
                and np.median(n.sum(axis=0)) >= min_events):
            qualified.append(j)
    kept, reps, duplicates = [], [], []
    for j in qualified:
        k = deterministic_medoid(fam[:, j])
        stream = fam[:, j, k]
        duplicate_of = j
        for old, rep in zip(kept, reps):
            other = fam[:, old, rep]
            if np.array_equal(stream, other):
                duplicate_of = old
                break
            if np.std(stream) > 0 and np.std(other) > 0 and np.corrcoef(stream, other)[0, 1] >= corr_limit:
                duplicate_of = old
                break
        kept.append(j)
        reps.append(k)
        duplicates.append(duplicate_of)
    return Nomination(tuple(kept), tuple(reps), tuple(qualified), tuple(duplicates))


def family_statistic(x: np.ndarray, method: str = "daily_mean", lags: int = 20) -> np.ndarray:
    """One statistic per family; candidates are *not* pooled as trade samples."""
    a = np.asarray(x, float)
    if a.ndim != 2 or a.shape[1] % 4:
        raise ValueError("expected four rule streams per family")
    n, f4 = a.shape
    if method == "daily_mean":
        return hac_t(a.reshape(n, f4 // 4, 4).mean(axis=2), lags)
    t = hac_t(a, lags).reshape(f4 // 4, 4)
    if method == "max":
        return np.max(t, axis=1)
    if method == "top2":
        return np.sort(t, axis=1)[:, -2:].mean(axis=1)
    if method == "median":
        return np.median(t, axis=1)
    raise ValueError(method)


def empirical_p(observed: np.ndarray, null: np.ndarray) -> np.ndarray:
    obs, z = np.asarray(observed, float), np.asarray(null, float)
    if z.ndim != 2 or z.shape[1] != len(obs):
        raise ValueError("null columns must match observed hypotheses")
    return (1 + np.count_nonzero(z >= obs[None, :], axis=0)) / (len(z) + 1)


def stepdown_p(observed: np.ndarray, null: np.ndarray) -> np.ndarray:
    obs, z = np.asarray(observed, float), np.asarray(null, float)
    if z.ndim != 2 or z.shape[1] != len(obs):
        raise ValueError("null columns must match observed hypotheses")
    order = np.argsort(-obs, kind="stable")
    out = np.empty(len(obs))
    prev = 0.0
    for rank, j in enumerate(order):
        prev = max(prev, (1 + np.count_nonzero(np.max(z[:, order[rank:]], axis=1) >= obs[j])) / (len(z) + 1))
        out[j] = prev
    return out


def fdr_adjust(p: np.ndarray, *, conservative: bool = False) -> np.ndarray:
    """Benjamini-Hochberg; BY harmonic factor for arbitrary dependence."""
    a = np.asarray(p, float)
    m = len(a)
    if not m:
        return a.copy()
    order = np.argsort(a, kind="stable")
    factor = sum(1 / j for j in range(1, m + 1)) if conservative else 1.0
    sorted_q = np.minimum.accumulate((a[order] * m * factor / np.arange(1, m + 1))[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(sorted_q, 1)
    return out


def validate(nomination: Nomination, daily: np.ndarray, exact_null: np.ndarray,
             family_null: np.ndarray, *, alpha: float = .05) -> dict[str, tuple[int, ...]]:
    """Compare FWER, BH/BY FDR, and family-first on frozen hypotheses only."""
    fam = np.array(nomination.families, dtype=int)
    rep = np.array(nomination.representative, dtype=int)
    if len(fam) == 0:
        return {k: () for k in ("holm", "stepdown", "bh", "by", "family_first")}
    cols = fam * 4 + rep
    t = hac_t(daily[:, cols])
    # Continuous HAC marginal p for Holm/BH/BY; finite null-world references
    # would otherwise make 120-way Holm incapable of rejecting at small B.
    p = norm.sf(t)
    z = exact_null[:, cols]
    tf = family_statistic(daily, "daily_mean")[fam]
    pf = stepdown_p(tf, family_null[:, fam])
    return {
        "holm": tuple(fam[holm_adjust(p) <= alpha]),
        "stepdown": tuple(fam[stepdown_p(t, z) <= alpha]),
        "bh": tuple(fam[fdr_adjust(p) <= alpha]),
        "by": tuple(fam[fdr_adjust(p, conservative=True) <= alpha]),
        # Family support alone cannot establish that the discovery medoid has
        # an edge (especially under a one-rule needle plant). Intersection
        # with its own one-sided holdout test prevents labeling a null medoid
        # as confirmed merely because another neighbor drives the family.
        "family_first": tuple(fam[(pf <= alpha) & (p <= alpha)]),
    }
