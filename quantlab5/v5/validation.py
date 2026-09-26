"""Frozen family-supported validation of every DISCOVERY qualifying candidate.

The family-side daily ensemble is the multiplicity unit. Support of a family
does not imply exact-rule significance. Every member satisfying the frozen
individual economic/execution criteria survives; nomination is annotation.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from quantlab5.v5.inference import fixed_family_inference
from quantlab5.v5.market_search import (CandidateRecord, SearchTrace,
                                         _shadow_clock_baseline, evaluate_spec)
from quantlab5.v5.signals import SignalContext


@dataclass(frozen=True)
class ValidationTrace:
    evaluated: tuple[CandidateRecord, ...]
    family_side_p: dict[str, float]
    family_side_stable: dict[str, bool]
    survivor_ids: tuple[str, ...]
    discovery_nominee_ids: tuple[str, ...]
    mc_reps: int = 0
    unresolved_groups: tuple[str, ...] = ()


def validate_frozen_cohort(market, discovery: SearchTrace, costs,
                           *, seed: int = 515005, reps: int = 500,
                           evaluator=evaluate_spec) -> ValidationTrace:
    """Evaluate all frozen qualifiers unchanged on an independent market world."""
    by_id = {r.candidate_id: r for r in discovery.records}
    ids = tuple(discovery.qualifying_ids)
    if len(ids) != len(set(ids)) or not set(ids) <= by_id.keys():
        raise ValueError("invalid frozen discovery qualifying cohort")
    if not ids:
        return ValidationTrace((), {}, {}, (), discovery.nominee_ids)
    context = SignalContext(market)
    shadow = _shadow_clock_baseline(market, context.stop,
                                    costs.per_trade_points("NQ", "baseline"))
    records = tuple(evaluator(market, by_id[cid].spec, context, costs,
                              shadow_baseline=shadow) for cid in ids)
    if tuple(r.candidate_id for r in records) != ids:
        raise ValueError("validation evaluator changed a frozen candidate ID")
    groups: dict[str, list[CandidateRecord]] = {}
    for r in records:
        groups.setdefault(f"{r.family}:{r.side}", []).append(r)
    keys = sorted(groups)
    streams = np.column_stack([np.mean(np.column_stack([r.daily_r for r in groups[key]]), axis=1)
                               for key in keys])
    inference = fixed_family_inference(streams, reps=reps, block=20, lags=20, seed=seed)
    if reps == 500 and np.any(np.abs(inference.adjusted_p-.05) <= .01):
        inference = fixed_family_inference(streams, reps=2000, block=20, lags=20,
                                           seed=seed+2000)
        reps = 2000
    p = {key: float(inference.adjusted_p[j]) for j, key in enumerate(keys)}
    unresolved = tuple(key for key in keys if abs(p[key]-.05) <= .01)
    stable = {}
    survivors = []
    for key in keys:
        rows = groups[key]
        x = np.column_stack([r.daily_r for r in rows])
        half = len(x)//2
        stable[key] = bool(half > 0 and x[:half].mean() > 0 and x[half:].mean() > 0
                           and np.count_nonzero(x.mean(axis=0) > 0) >= int(np.ceil(.75*len(rows))))
        if p[key] > .05 or key in unresolved or not stable[key]:
            continue
        for r in rows:
            if (r.trades >= 40 and r.active_years >= 2 and r.daily_r.mean() > 0
                    and r.stress_net_r > 0 and r.matched_excess_r > 0):
                survivors.append(r.candidate_id)
    return ValidationTrace(records, p, stable, tuple(sorted(survivors)),
                           discovery.nominee_ids, reps, unresolved)
