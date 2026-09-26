"""Daily-stream inference for a fixed, predeclared candidate family.

This module is NOT a correction for adaptive B/C feature generation. Full-market
replay must call the complete search-selection procedure in every surrogate world.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import beta


def stationary_indices(n: int, mean_block: int, rng: np.random.Generator) -> np.ndarray:
    """Politis-Romano stationary bootstrap, one common index for every candidate."""
    if n < 1 or mean_block < 1:
        raise ValueError("n and mean_block must be positive")
    out = np.empty(n, dtype=np.int64)
    out[0] = rng.integers(n)
    restart = rng.random(n - 1) < 1.0 / mean_block
    fresh = rng.integers(n, size=n - 1)
    for i in range(1, n):
        out[i] = fresh[i - 1] if restart[i - 1] else (out[i - 1] + 1) % n
    return out


def hac_t(x: np.ndarray, lags: int = 20, variance_floor: float = 1e-12) -> np.ndarray:
    """One-sided t of mean daily net R, Bartlett HAC, calendar-zero days included."""
    a = np.asarray(x, dtype=np.float64)
    if a.ndim == 1:
        a = a[:, None]
    if a.ndim != 2 or a.shape[0] < 3 or not np.isfinite(a).all():
        raise ValueError("expected finite day x candidate matrix with >=3 days")
    n = a.shape[0]
    z = a - a.mean(axis=0)
    v = np.mean(z * z, axis=0)
    for k in range(1, min(lags, n - 1) + 1):
        v += 2 * (1 - k / (lags + 1)) * np.mean(z[k:] * z[:-k], axis=0)
    se = np.sqrt(np.maximum(v, variance_floor) / n)
    return a.mean(axis=0) / se


@dataclass(frozen=True)
class FixedFamilyResult:
    t: np.ndarray
    global_p: float
    adjusted_p: np.ndarray
    null_max: np.ndarray


def fixed_family_inference(streams: np.ndarray, *, reps: int = 500, block: int = 20,
                           lags: int = 20, seed: int = 0) -> FixedFamilyResult:
    """Centered max-t Reality Check and joint Romano-Wolf stepdown for FIXED rules.

    The same stationary-bootstrap indices are applied to all candidates. Each
    candidate is centered at the least-favorable null mean zero. Stepdown uses
    remaining-hypothesis maxima and enforces monotonic adjusted p-values.
    """
    x = np.asarray(streams, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] < 1 or reps < 1:
        raise ValueError("expected day x candidate matrix and positive reps")
    obs = hac_t(x, lags)
    centered = x - x.mean(axis=0)
    rng = np.random.default_rng(seed)
    null_t = np.empty((reps, x.shape[1]), dtype=np.float64)
    for b in range(reps):
        idx = stationary_indices(len(x), block, rng)
        null_t[b] = hac_t(centered[idx], lags)
    order = np.argsort(-obs, kind="stable")
    adj = np.empty(x.shape[1], dtype=float)
    prior = 0.0
    for rank, j in enumerate(order):
        mx = np.max(null_t[:, order[rank:]], axis=1)
        raw = (1 + np.count_nonzero(mx >= obs[j])) / (reps + 1)
        prior = max(prior, raw)
        adj[j] = prior
    null_max = np.max(null_t, axis=1)
    global_p = (1 + np.count_nonzero(null_max >= np.max(obs))) / (reps + 1)
    return FixedFamilyResult(obs, float(global_p), adj, null_max)


def clopper_pearson(k: int, n: int, error: float = 0.0025) -> tuple[float, float]:
    """Two-sided exact binomial interval, error spent at one sequential look."""
    if not 0 <= k <= n or n <= 0 or not 0 < error < 1:
        raise ValueError("invalid binomial count/error")
    lo = 0.0 if k == 0 else float(beta.ppf(error / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - error / 2, k + 1, n - k))
    return lo, hi


@dataclass(frozen=True)
class SequentialDecision:
    status: str
    n: int
    exceedances: int
    plus_one_p: float
    interval: tuple[float, float]


def sequential_decision(exceedances: np.ndarray, *, alpha: float = 0.05,
                        looks: tuple[int, ...] = (50, 100, 200, 500),
                        total_error: float = 0.01) -> SequentialDecision:
    """Anytime-valid across the four frozen looks by Bonferroni error spending."""
    x = np.asarray(exceedances, dtype=bool)
    if len(x) < looks[0] or any(a >= b for a, b in zip(looks, looks[1:])):
        raise ValueError("insufficient worlds or invalid looks")
    final = None
    for n in looks:
        if len(x) < n:
            break
        k = int(x[:n].sum())
        ci = clopper_pearson(k, n, total_error / len(looks))
        status = "SIGNIFICANT" if ci[1] < alpha else "NONSIGNIFICANT" if ci[0] > alpha else "UNRESOLVED"
        final = SequentialDecision(status, n, k, (k + 1) / (n + 1), ci)
        if status != "UNRESOLVED":
            break
    if final is None:
        raise ValueError("no completed look")
    return final
