"""Fixed-library hierarchical inference on 30 families x 4 nearby rules.

The family statistic is the HAC t of the *daily average stream*, not a pooled
trade sample. A duplicated event contributes once to that daily average. This
module estimates evidence for a mechanism region, not an exact-spec p-value.
Adaptive candidate generation still requires full market-level replay.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import norm

from quantlab5.v5.inference import hac_t, stationary_indices
from quantlab5.v5.synthetic_streams import SHAPES, StructuredPanel


def holm_adjust(p: np.ndarray) -> np.ndarray:
    a = np.asarray(p, float)
    order = np.argsort(a, kind="stable")
    out = np.empty(len(a), float)
    last = 0.0
    for rank, i in enumerate(order):
        last = max(last, min(1.0, (len(a) - rank) * a[i]))
        out[i] = last
    return out


def deterministic_medoid(x: np.ndarray) -> int:
    """Representative closest in centered daily path to the family mean; ID tie break."""
    a = np.asarray(x, float)
    center = a.mean(axis=1)
    distance = np.mean((a - center[:, None]) ** 2, axis=0)
    return int(np.argmin(distance))


def cluster_support(x: np.ndarray) -> bool:
    """At least 3/4 positive, family average positive in both chronological halves."""
    a = np.asarray(x, float)
    if a.ndim != 2 or a.shape[1] != 4:
        raise ValueError("one family must have four neighboring specifications")
    h = len(a) // 2
    return bool(np.count_nonzero(a.mean(axis=0) > 0) >= 3 and
                a[:h].mean() > 0 and a[h:].mean() > 0)


@dataclass(frozen=True)
class HierarchyResult:
    naive_event_p: float
    single_hac_p: float
    single_bootstrap_p: float
    unadjusted_joint_p: float
    holm_p: float
    stepdown_p: float
    global_p: float
    family_adjusted_p: float
    family_supported: bool
    neighborhood_supported: bool
    representative_spec: int
    exact_t: float
    family_t: float


def evaluate_hierarchy(x: np.ndarray, *, target_events: np.ndarray | None = None,
                       reps: int = 199, block: int = 20, lags: int = 20,
                       seed: int = 0) -> HierarchyResult:
    """A–F decomposition using the same centered common-index resamples."""
    a = np.asarray(x, float)
    if a.ndim != 2 or a.shape[1] != 120 or reps < 19:
        raise ValueError("expected fixed day x 120 panel and >=19 resamples")
    fam = a.reshape(len(a), 30, 4).mean(axis=2)
    te = hac_t(a, lags)
    tf = hac_t(fam, lags)
    centered = a - a.mean(axis=0)
    rng = np.random.default_rng(seed)
    be = np.empty((reps, 120), float)
    bf = np.empty((reps, 30), float)
    for b in range(reps):
        ix = stationary_indices(len(a), block, rng)
        z = centered[ix]
        be[b] = hac_t(z, lags)
        bf[b] = hac_t(z.reshape(len(a), 30, 4).mean(axis=2), lags)
    marginal = (1 + np.count_nonzero(be >= te[None, :], axis=0)) / (reps + 1)
    ordered = np.argsort(-te, kind="stable")
    step = np.empty(120)
    last = 0.0
    for rank, j in enumerate(ordered):
        mx = np.max(be[:, ordered[rank:]], axis=1)
        raw = (1 + np.count_nonzero(mx >= te[j])) / (reps + 1)
        last = max(last, raw)
        step[j] = last
    # With 99 bootstrap draws the smallest marginal p is 0.01, making a
    # 120-hypothesis Holm test incapable of rejecting. Use the continuous
    # prespecified HAC normal p-values for this analytic comparator instead.
    holm = holm_adjust(norm.sf(te))
    global_observed = max(float(np.max(te)), float(np.max(tf)))
    global_null = np.maximum(np.max(be, axis=1), np.max(bf, axis=1))
    global_p = (1 + np.count_nonzero(global_null >= global_observed)) / (reps + 1)
    family_p = (1 + np.count_nonzero(np.max(bf, axis=1) >= tf[0])) / (reps + 1)
    region = cluster_support(a[:, :4])
    rep = deterministic_medoid(a[:, :4])
    if target_events is None or len(target_events) < 3 or np.std(target_events, ddof=1) == 0:
        naive_p = 1.0
    else:
        ev = np.asarray(target_events, float)
        naive_p = float(norm.sf(np.sqrt(len(ev)) * ev.mean() / ev.std(ddof=1)))
    return HierarchyResult(
        naive_event_p=naive_p, single_hac_p=float(norm.sf(te[0])),
        single_bootstrap_p=float(marginal[0]), unadjusted_joint_p=float(marginal[0]),
        holm_p=float(holm[0]), stepdown_p=float(step[0]),
        global_p=float(global_p), family_adjusted_p=float(family_p),
        family_supported=bool(global_p <= 0.05 and family_p <= 0.05),
        neighborhood_supported=bool(global_p <= 0.05 and family_p <= 0.05 and region),
        representative_spec=rep, exact_t=float(te[0]), family_t=float(tf[0]))


def event_cluster_t(daily_r: np.ndarray, daily_count: np.ndarray, lags: int = 20) -> float:
    """Event-mean null t with session/block dependence; at H0=0 equals daily-sum t."""
    r = np.asarray(daily_r, float)
    n = np.asarray(daily_count, float)
    if r.shape != n.shape or n.sum() <= 0:
        raise ValueError("invalid daily event aggregates")
    # Both the ratio estimate sum(R)/sum(N) and its null SE divide by mean(N).
    # The factor cancels from the t statistic, so counting same-day events does
    # not manufacture additional independent observations.
    return float(hac_t(r, lags)[0])


def evaluate_shape_effects(panel: StructuredPanel, shape: str, effects,
                           *, reps: int = 99, block: int = 20, lags: int = 20,
                           seed: int = 0) -> list[HierarchyResult]:
    """Exact A–F bootstrap results for many plants, reusing unaffected null columns.

    Every effect's affected centered streams are recomputed under the same frozen
    stationary-bootstrap indices. Other 116 candidates are byte-identical across
    effects, so their null t values are computed once per base world.
    """
    if shape not in SHAPES or reps < 19:
        raise ValueError("bad shape or too few resamples")
    a0 = panel.daily.copy()
    if shape == "regime":
        a0[~panel.regime, 0] = 0.0
    if a0.shape[1] != 120:
        raise ValueError("expected 120 candidate streams")
    n = len(a0)
    centered = a0 - a0.mean(axis=0)
    rng = np.random.default_rng(seed)
    indices = [stationary_indices(n, block, rng) for _ in range(reps)]
    be_base = np.empty((reps, 120))
    bf_base = np.empty((reps, 30))
    for b, ix in enumerate(indices):
        z = centered[ix]
        be_base[b] = hac_t(z, lags)
        bf_base[b] = hac_t(z.reshape(n, 30, 4).mean(axis=2), lags)
    strength = np.asarray(SHAPES[shape])
    active = panel.regime if shape == "regime" else np.ones(n, bool)
    shift = panel.counts[:, :4] * active[:, None] * strength[None, :]
    centered_shift = shift - shift.mean(axis=0)
    out = []
    for effect in effects:
        if effect < 0:
            raise ValueError("negative effect")
        x = a0.copy()
        x[:, :4] += effect * shift
        fam = x.reshape(n, 30, 4).mean(axis=2)
        te, tf = hac_t(x, lags), hac_t(fam, lags)
        be, bf = be_base.copy(), bf_base.copy()
        for b, ix in enumerate(indices):
            changed = centered[ix, :4] + effect * centered_shift[ix]
            be[b, :4] = hac_t(changed, lags)
            bf[b, 0] = hac_t(changed.mean(axis=1), lags)[0]
        marginal = (1 + np.count_nonzero(be >= te[None, :], axis=0)) / (reps + 1)
        ordered = np.argsort(-te, kind="stable")
        step = np.empty(120)
        last = 0.0
        for rank, j in enumerate(ordered):
            raw = (1 + np.count_nonzero(np.max(be[:, ordered[rank:]], axis=1) >= te[j])) / (reps + 1)
            last = max(last, raw)
            step[j] = last
        holm = holm_adjust(norm.sf(te))
        global_observed = max(float(np.max(te)), float(np.max(tf)))
        global_null = np.maximum(np.max(be, axis=1), np.max(bf, axis=1))
        global_p = (1 + np.count_nonzero(global_null >= global_observed)) / (reps + 1)
        family_p = (1 + np.count_nonzero(np.max(bf, axis=1) >= tf[0])) / (reps + 1)
        take = active[panel.target_event_day]
        ev = panel.target_event_r[take] + effect if shape == "regime" else panel.target_event_r + effect
        naive_p = 1.0 if len(ev) < 3 or ev.std(ddof=1) == 0 else float(
            norm.sf(np.sqrt(len(ev)) * ev.mean() / ev.std(ddof=1)))
        region = cluster_support(x[:, :4])
        out.append(HierarchyResult(
            naive_event_p=naive_p, single_hac_p=float(norm.sf(te[0])),
            single_bootstrap_p=float(marginal[0]), unadjusted_joint_p=float(marginal[0]),
            holm_p=float(holm[0]), stepdown_p=float(step[0]),
            global_p=float(global_p), family_adjusted_p=float(family_p),
            family_supported=bool(global_p <= 0.05 and family_p <= 0.05),
            neighborhood_supported=bool(global_p <= 0.05 and family_p <= 0.05 and region),
            representative_spec=deterministic_medoid(x[:, :4]), exact_t=float(te[0]),
            family_t=float(tf[0])))
    return out
