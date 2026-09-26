"""Adaptive V5 market search over executable A/B/C signal specifications.

No real-partition loader is used. The caller supplies a Market and an independent
market-null Stage A reference. Every surrogate world can call the same function.
All evaluated candidates and qualifying nominees remain in the returned trace.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from quantlab5.data.sessions import Window
from quantlab5.data.market import build_market
from quantlab5.engine.execution import run_signals
from quantlab5.search.candidate_id import candidate_id
from quantlab5.v5.candidate_inventory import (MECHANISMS, activated_inventory,
                                              inventory, stage_a_expansion_gate)
from quantlab5.v5.duplicate_accounting import (PairSimilarity, behavioral_duplicate_map,
                                                pairwise_duplicate_analysis, signal_fingerprint)
from quantlab5.v5.inference import fixed_family_inference, hac_t
from quantlab5.v5.inference import SequentialDecision, sequential_decision
from quantlab5.v5.signals import SignalContext, signal_for_spec
from quantlab5.v5.risk_coverage import evaluate_mnq_budgets

WINDOW = Window("v5_rth", 935, 1276, 1315)
_RISK_WINDOW_CFG = {"windows": {"v5_rth": {
    "entry_start": "09:35", "entry_end": "15:16", "flat_at": "15:55"}}}


@dataclass(frozen=True)
class CandidateRecord:
    candidate_id: str
    stage: str
    family: str
    side: str
    spec: dict
    statistic: float
    daily_r: np.ndarray
    daily_count: np.ndarray
    trades: int
    active_years: int
    stress_net_r: float
    matched_excess_r: float
    signal_hash: str
    entry_indices: np.ndarray
    trade_sides: np.ndarray
    exit_indices: np.ndarray | None = None
    net_r: float = 0.0
    expectancy_r: float = 0.0
    profit_factor: float | None = None
    max_drawdown_r: float = 0.0


@dataclass(frozen=True)
class SearchTrace:
    records: tuple[CandidateRecord, ...]
    stage_a_family_p: dict[str, float]
    expanded_families: tuple[str, ...]
    b_winner_ids: dict[str, str]
    nominee_ids: tuple[str, ...]
    exact_duplicate_of: dict[str, str]
    behavior_duplicate_of: dict[str, str]
    pair_similarities: tuple[PairSimilarity, ...]
    global_statistic: float
    family_statistics: dict[str, float]
    qualifying_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class AdaptiveNullReplay:
    generator_name: str
    seeds: tuple[int, ...]
    traces: tuple[SearchTrace, ...]
    decision: SequentialDecision


def coverage_for_trace(market, trace: SearchTrace, costs) -> dict[str, dict]:
    """Four fixed MNQ budgets for every evaluated candidate, independent of rank."""
    context = SignalContext(market)
    out = {}
    for record in trace.records:
        lg, sh, stop = signal_for_spec(market, record.spec, context)
        out[record.candidate_id] = evaluate_mnq_budgets(
            market.nq, lg, sh, stop, _RISK_WINDOW_CFG, costs,
            hold=60, window_name="v5_rth")
    return out


def calibrate_stage_a_reference(market, generator, seeds, costs,
                                *, evaluator=None) -> np.ndarray:
    """Independent market-surrogate reference for 30 Stage A family maxima."""
    if not seeds:
        raise ValueError("at least one independent reference seed is required")
    if evaluator is None:
        evaluator = evaluate_spec
    out = np.empty((len(seeds), 30), float)
    source = {"NQ": market.nq, "ES": market.es}
    specs = inventory()["stage_a"]
    for row, seed in enumerate(seeds):
        bars = generator.generate(source, int(seed))
        world = build_market(bars["NQ"], bars["ES"], market.nq_symbols, market.es_symbols)
        context = SignalContext(world)
        shadow = _shadow_clock_baseline(world, context.stop,
                                        costs.per_trade_points("NQ", "baseline"))
        records = [evaluator(world, s, context, costs, shadow_baseline=shadow) for s in specs]
        out[row] = [max(r.statistic for r in records if r.family == m.code)
                    for m in MECHANISMS]
    return out


def _shadow_clock_baseline(market, stop: np.ndarray, baseline_cost_points: float) -> np.ndarray:
    """Unconditional same-clock 60-minute directional drift, in net R.

    This diagnostic uses next-open to 60-minute close without an intervening
    stop, so it is not an independent predictive test. The same formula is used
    in every real or null world; the final prereg must explicitly accept or
    replace it before search authorization.
    """
    b, g = market.nq, market.gid
    n = market.n
    future = np.arange(n) + 60
    ok = (future < n) & np.isfinite(stop) & (stop > 0)
    safe = np.minimum(future, n-1)
    ok &= (g[safe] == g)
    # Eligibility is checked against Market.dec rather than a bar count.
    decision = np.zeros(n, bool)
    decision[np.asarray(market.dec, int)] = True
    ok &= decision
    raw = np.full(n, np.nan)
    ix = np.flatnonzero(ok)
    raw[ix] = ((np.asarray(b.c)[safe[ix]] - np.asarray(b.o)[ix+1])
               - baseline_cost_points) / stop[ix]
    baseline = np.zeros((2, 1440), float)
    sm = np.asarray(b.sm, int)
    for clock in np.unique(sm[ix]):
        a = raw[ix[sm[ix] == clock]]
        baseline[0, clock] = float(np.mean(a))
        baseline[1, clock] = float(np.mean(-a - 2*baseline_cost_points/stop[ix[sm[ix] == clock]]))
    return baseline


def evaluate_spec(market, spec: dict, context: SignalContext, costs,
                  *, shadow_baseline: np.ndarray | None = None) -> CandidateRecord:
    """Run the shared conservative engine and aggregate on a full session grid."""
    lg, sh, stop = signal_for_spec(market, spec, context)
    tr = run_signals(market.nq, lg, sh, WINDOW, spec["side"], hold=60,
                     stop_dist=stop, tick=.25)
    inv = context.session_inverse
    daily = np.zeros(len(context.session_days), float)
    count = np.zeros(len(context.session_days), int)
    risk = np.asarray(tr.initial_risk, float)
    baseline_points = costs.per_trade_points("NQ", "baseline")
    stress_points = costs.per_trade_points("NQ", "stress")
    net = (np.asarray(tr.points, float) - baseline_points) / risk if tr.n else np.empty(0)
    stressed = (np.asarray(tr.points, float) - stress_points) / risk if tr.n else np.empty(0)
    if tr.n:
        np.add.at(daily, inv[tr.entry_idx], net)
        np.add.at(count, inv[tr.entry_idx], 1)
    active = len(np.unique(context.calendar_years[tr.entry_idx])) if tr.n else 0
    excess = 0.0
    if tr.n and shadow_baseline is not None:
        clock = np.asarray(market.nq.sm)[tr.entry_idx-1].astype(int)
        row = 0 if spec["side"] == "long" else 1
        excess = float(np.mean(net - shadow_baseline[row, clock]))
    mask_key = signal_fingerprint(lg, sh, "v5_next_open_atr15_stop60_flat1555")
    t = float(hac_t(daily)[0]) if len(daily) >= 3 else float("-inf")
    gain = float(net[net > 0].sum())
    loss = float(-net[net < 0].sum())
    pf = gain/loss if loss > 0 else None
    path = np.r_[0.0, np.cumsum(net)]
    drawdown = float(np.max(np.maximum.accumulate(path)-path))
    return CandidateRecord(candidate_id(spec), spec["stage"], spec["family"], spec["side"],
                           spec, t, daily, count, int(tr.n), active,
                           float(stressed.sum()), excess, mask_key,
                           np.asarray(tr.entry_idx, np.int32), np.asarray(tr.side, np.int8),
                           np.asarray(tr.exit_idx, np.int32),
                           float(net.sum()), float(net.mean()) if tr.n else 0.0,
                           pf, drawdown)


def _nominate(records: tuple[CandidateRecord, ...]) -> tuple[str, ...]:
    """Stable-region medoid within family and direction; no rank cap."""
    out = []
    for family in sorted({r.family for r in records}):
        for side in ("long", "short"):
            group = [r for r in records if r.family == family and r.side == side]
            good = [r for r in group if r.trades >= 120 and r.active_years >= 6
                    and r.stress_net_r > 0 and r.matched_excess_r > 0
                    and r.daily_r.mean() > 0]
            if len(good) < 3:
                continue
            x = np.column_stack([r.daily_r for r in good])
            half = len(x)//2
            if x[:half].mean() <= 0 or x[half:].mean() <= 0:
                continue
            center = x.mean(axis=1)
            distance = np.mean((x-center[:, None])**2, axis=0)
            eligible = [k for k in range(len(good))
                        if x[:half, k].mean() > 0 and x[half:, k].mean() > 0]
            if not eligible:
                continue
            chosen = min(eligible, key=lambda k: (distance[k], good[k].candidate_id))
            out.append(good[chosen].candidate_id)
    return tuple(sorted(out))


def _qualifying_ids(records: tuple[CandidateRecord, ...]) -> tuple[str, ...]:
    """Discovery economic/stability gate for every evaluated rule; no rank cap."""
    return tuple(sorted(r.candidate_id for r in records
                        if r.trades >= 120 and r.active_years >= 6
                        and r.daily_r.mean() > 0 and r.stress_net_r > 0
                        and r.matched_excess_r > 0))


def _stage_a_stream_family_p(records: list[CandidateRecord]) -> dict[str, float]:
    """Exploratory family max-t from centered, common-day Stage A streams."""
    if len(records) != 60 or {r.family for r in records} != {m.code for m in MECHANISMS}:
        raise ValueError("stream reference requires the complete 60-rule Stage A inventory")
    streams = np.column_stack([r.daily_r for r in records])
    result = fixed_family_inference(streams, reps=500, block=20, lags=20,
                                    seed=515001)
    null_max = result.null_max
    return {m.code: float((1+np.count_nonzero(null_max >= max(
        r.statistic for r in records if r.family == m.code)))/(len(null_max)+1))
            for m in MECHANISMS}


def adaptive_search(market, costs, stage_a_null_family_t: np.ndarray | None = None,
                    *, evaluator=evaluate_spec) -> SearchTrace:
    """Replay all transitions in a Market world; no top-N or correlation removal."""
    if stage_a_null_family_t is not None:
        reference = np.asarray(stage_a_null_family_t, float)
        if reference.ndim != 2 or reference.shape[1] != 30 or len(reference) < 19 or not np.isfinite(reference).all():
            raise ValueError("need independent null-world Stage A family statistics")
    inv = inventory()
    context = SignalContext(market)
    shadow = _shadow_clock_baseline(market, context.stop,
                                    costs.per_trade_points("NQ", "baseline"))
    records = [evaluator(market, spec, context, costs, shadow_baseline=shadow)
               for spec in inv["stage_a"]]
    family_t = {m.code: max(r.statistic for r in records if r.family == m.code)
                for m in MECHANISMS}
    if stage_a_null_family_t is None:
        family_p = _stage_a_stream_family_p(records)
    else:
        reference_max = np.max(reference, axis=1)
        family_p = {family: float((1+np.count_nonzero(reference_max >= t))/(len(reference)+1))
                    for family, t in family_t.items()}
    expanded = []
    for m in MECHANISMS:
        family_rows = [r for r in records if r.family == m.code]
        if any(stage_a_expansion_gate(adjusted_family_p=family_p[m.code],
                                      trades=r.trades, active_years=r.active_years,
                                      stress_net=r.stress_net_r,
                                      matched_excess=r.matched_excess_r)
               for r in family_rows):
            expanded.append(m.code)
    activated = activated_inventory(expanded, {})
    records.extend(evaluator(market, spec, context, costs, shadow_baseline=shadow)
                   for spec in activated["stage_b"])
    winners = {}
    for family in expanded:
        choices = [r for r in records if r.family == family and r.stage == "B"
                   and r.trades >= 120 and r.stress_net_r > 0 and r.statistic > 0]
        if choices:
            chosen = min(choices, key=lambda r: (-r.statistic, r.candidate_id))
            winners[family] = chosen.spec
    conditional = activated_inventory(expanded, winners)
    records.extend(evaluator(market, spec, context, costs, shadow_baseline=shadow)
                   for spec in conditional["stage_c"])
    rec = tuple(records)
    first = {}
    exact = {}
    for r in rec:
        exact[r.candidate_id] = first.setdefault(r.signal_hash, r.candidate_id)
    behavior = behavioral_duplicate_map(tuple(r.candidate_id for r in rec),
                                         np.column_stack([r.daily_r for r in rec]))
    pair_similarities = pairwise_duplicate_analysis(rec)
    family_all = {m.code: max(r.statistic for r in rec if r.family == m.code)
                  for m in MECHANISMS}
    return SearchTrace(rec, family_p, tuple(expanded),
                       {k: candidate_id(v) for k, v in winners.items()},
                       _nominate(rec), exact, behavior, pair_similarities,
                       max(family_all.values()), family_all,
                       _qualifying_ids(rec))


def replay_adaptive_null(market, generator, seeds, costs, stage_a_null_family_t,
                         observed_global_statistic: float, *, evaluator=evaluate_spec,
                         looks: tuple[int, ...] = (50, 100, 200, 500)) -> AdaptiveNullReplay:
    """Recompute full adaptive A/B/C search in each market-level null world.

    The independent Stage A reference is fixed before this outer replay. At each
    prespecified look, the same error-spent sequential rule decides whether to
    stop. All generated worlds and seeds are retained for audit.
    """
    if len(seeds) < looks[0] or not np.isfinite(observed_global_statistic):
        raise ValueError("insufficient seeds or invalid observed statistic")
    source = {"NQ": market.nq, "ES": market.es}
    traces = []
    used = []
    exceeds = []
    decision = None
    for seed in seeds[:looks[-1]]:
        bars = generator.generate(source, int(seed))
        world = build_market(bars["NQ"], bars["ES"], market.nq_symbols, market.es_symbols)
        trace = adaptive_search(world, costs, stage_a_null_family_t, evaluator=evaluator)
        traces.append(trace)
        used.append(int(seed))
        exceeds.append(trace.global_statistic >= observed_global_statistic)
        if len(used) in looks:
            decision = sequential_decision(np.asarray(exceeds, bool), looks=looks)
            if decision.status != "UNRESOLVED":
                break
    if decision is None:
        raise ValueError("no completed sequential look")
    return AdaptiveNullReplay(generator.name, tuple(used), tuple(traces), decision)
