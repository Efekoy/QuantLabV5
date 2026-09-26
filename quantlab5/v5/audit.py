"""Evaluation-only exact-cohort historical audit; no search or selection."""
from __future__ import annotations

from dataclasses import asdict
import numpy as np
from scipy.stats import norm

from quantlab5.search.candidate_id import candidate_id
from quantlab5.v5.holdout_confirmation import (ALPHA, BLOCK, HAC_LAGS,
                                                hac_mean_se)
from quantlab5.v5.inference import fixed_family_inference
from quantlab5.v5.market_search import _RISK_WINDOW_CFG, _shadow_clock_baseline, evaluate_spec
from quantlab5.v5.risk_coverage import evaluate_mnq_budgets
from quantlab5.v5.signals import SignalContext, signal_for_spec


def evaluate_exact_cohort(market, specs: dict[str, dict], costs, *, seed: int) -> dict:
    """Run every frozen exact specification once; return all labels, no filtering."""
    ids = tuple(sorted(specs))
    if any(candidate_id(specs[cid]) != cid for cid in ids):
        raise ValueError("audit candidate ID/specification mismatch")
    if not ids:
        return {"candidate_ids": [], "rows": {}, "bootstrap_reps": 0,
                "unresolved_ids": []}
    context = SignalContext(market)
    shadow = _shadow_clock_baseline(market, context.stop,
                                    costs.per_trade_points("NQ", "baseline"))
    records = tuple(evaluate_spec(market, specs[cid], context, costs,
                                  shadow_baseline=shadow) for cid in ids)
    if tuple(r.candidate_id for r in records) != ids:
        raise ValueError("audit evaluator changed a frozen Q5 ID")
    streams = np.column_stack([r.daily_r for r in records])
    inference = fixed_family_inference(streams, reps=500, block=BLOCK,
                                       lags=HAC_LAGS, seed=seed)
    reps = 500
    if np.any(np.abs(inference.adjusted_p-ALPHA) <= .01):
        inference = fixed_family_inference(streams, reps=2000, block=BLOCK,
                                           lags=HAC_LAGS, seed=seed+2000)
        reps = 2000
    unresolved = [r.candidate_id for r, p in zip(records, inference.adjusted_p)
                  if abs(p-ALPHA) <= .01]
    rows = {}
    for r, p, t in zip(records, inference.adjusted_p, inference.t):
        mean, se = hac_mean_se(r.daily_r)
        upper = mean+float(norm.ppf(.95))*se
        if r.candidate_id not in unresolved and p <= ALPHA and r.trades >= 20 and (
                r.stress_net_r > 0 and r.matched_excess_r > 0):
            label = "SUPPORTED"
        elif upper < 0:
            label = "REJECTED"
        else:
            label = "INCONCLUSIVE / UNDERPOWERED"
        rows[r.candidate_id] = {
            "classification": label, "trades": r.trades, "active_years": r.active_years,
            "mean_daily_net_r": mean, "hac_se_daily_r": se,
            "upper95_mean_daily_r": upper, "net_r": r.net_r,
            "expectancy_r": r.expectancy_r, "profit_factor": r.profit_factor,
            "max_drawdown_r": r.max_drawdown_r,
            "stress_net_r": r.stress_net_r, "matched_excess_r": r.matched_excess_r,
            "unadjusted_hac_p": float(norm.sf(t)), "adjusted_p": float(p),
            "daily_r": r.daily_r.tolist(), "daily_count": r.daily_count.tolist(),
        }
        lg, sh, stop = signal_for_spec(market, r.spec, context)
        rows[r.candidate_id]["mnq_budget_coverage"] = {
            str(b): asdict(v) for b, v in evaluate_mnq_budgets(
                market.nq, lg, sh, stop, _RISK_WINDOW_CFG, costs,
                hold=60, window_name="v5_rth").items()}
    return {"candidate_ids": list(ids), "rows": rows, "bootstrap_reps": reps,
            "unresolved_ids": sorted(unresolved)}
