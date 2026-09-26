"""Primary exact-candidate confirmation on frozen day-clustered holdout streams."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from quantlab5.v5.inference import fixed_family_inference
from quantlab5.v5.market_search import CandidateRecord, SearchTrace, _shadow_clock_baseline, evaluate_spec
from quantlab5.v5.signals import SignalContext

ALPHA = .05
PRIMARY_REPS = 500
NEAR_BOUNDARY_REPS = 2000
BLOCK = 20
HAC_LAGS = 20
SEED = 515005


def hac_mean_se(x: np.ndarray) -> tuple[float, float]:
    """Mean and Bartlett HAC standard error on full session days, including zero days."""
    a = np.asarray(x, float)
    if a.ndim != 1 or len(a) < 3 or not np.isfinite(a).all():
        raise ValueError("finite daily stream with at least three days required")
    z = a-a.mean()
    v = float(np.mean(z*z))
    for lag in range(1, min(HAC_LAGS, len(a)-1)+1):
        v += 2*(1-lag/(HAC_LAGS+1))*float(np.mean(z[lag:]*z[:-lag]))
    return float(a.mean()), float(np.sqrt(max(v, 1e-12)/len(a)))


@dataclass(frozen=True)
class Confirmation:
    evaluated: tuple[CandidateRecord, ...]
    adjusted_p: dict[str, float]
    unadjusted_p: dict[str, float]
    classification: dict[str, str]
    survivor_ids: tuple[str, ...]
    upper95_mean_daily_r: dict[str, float]
    bootstrap_reps: int
    unresolved_ids: tuple[str, ...]


def confirm_frozen_candidates(market, discovery: SearchTrace, costs,
                              *, evaluator=evaluate_spec) -> Confirmation:
    """Test every qualifying Q5 specification unchanged on validation days."""
    by_id = {r.candidate_id: r for r in discovery.records}
    ids = tuple(discovery.qualifying_ids)
    if len(ids) != len(set(ids)) or not set(ids) <= set(by_id):
        raise ValueError("invalid frozen discovery candidate set")
    if not ids:
        return Confirmation((), {}, {}, {}, (), {}, 0, ())
    context = SignalContext(market)
    shadow = _shadow_clock_baseline(market, context.stop,
                                    costs.per_trade_points("NQ", "baseline"))
    rows = tuple(evaluator(market, by_id[cid].spec, context, costs,
                           shadow_baseline=shadow) for cid in ids)
    if tuple(x.candidate_id for x in rows) != ids:
        raise ValueError("validation evaluator changed a frozen Q5 ID")
    streams = np.column_stack([r.daily_r for r in rows])
    result = fixed_family_inference(streams, reps=PRIMARY_REPS, block=BLOCK,
                                    lags=HAC_LAGS, seed=SEED)
    reps = PRIMARY_REPS
    if np.any(np.abs(result.adjusted_p-ALPHA) <= .01):
        result = fixed_family_inference(streams, reps=NEAR_BOUNDARY_REPS,
                                        block=BLOCK, lags=HAC_LAGS,
                                        seed=SEED+NEAR_BOUNDARY_REPS)
        reps = NEAR_BOUNDARY_REPS
    unresolved = tuple(sorted(r.candidate_id for r, p in zip(rows, result.adjusted_p)
                              if abs(p-ALPHA) <= .01))
    # Single-candidate p uses its own centered bootstrap distribution. The
    # stepdown adjusted p is the primary, dependence-aware decision.
    # The unadjusted one-sided normal HAC p is descriptive, not a decision.
    from scipy.stats import norm
    raw = {r.candidate_id: float(norm.sf(t)) for r, t in zip(rows, result.t)}
    adj = {r.candidate_id: float(p) for r, p in zip(rows, result.adjusted_p)}
    upper = {}
    classes = {}
    for r in rows:
        mean, se = hac_mean_se(r.daily_r)
        upper[r.candidate_id] = mean+float(norm.ppf(.95))*se
        economic = (r.trades >= 40 and r.active_years >= 2 and mean > 0
                    and r.stress_net_r > 0 and r.matched_excess_r > 0)
        if r.candidate_id not in unresolved and adj[r.candidate_id] <= ALPHA and economic:
            classes[r.candidate_id] = "SUPPORTED"
        elif upper[r.candidate_id] < 0:
            classes[r.candidate_id] = "REJECTED"
        else:
            classes[r.candidate_id] = "INCONCLUSIVE / UNDERPOWERED"
    survivors = tuple(sorted(k for k, v in classes.items() if v == "SUPPORTED"))
    return Confirmation(rows, adj, raw, classes, survivors, upper, reps, unresolved)
