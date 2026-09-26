import numpy as np

from quantlab5.data.market import build_market
from quantlab5.engine.costs import CostModel
from quantlab5.search.candidate_id import candidate_id
from quantlab5.synthetic.markets import correlated_pair, weekdays
from quantlab5.v5.market_search import (CandidateRecord, adaptive_search,
                                        calibrate_stage_a_reference, coverage_for_trace,
                                        evaluate_spec,
                                        replay_adaptive_null)
from quantlab5.nulls.base import MinuteSignFlipNull
from quantlab5.v5.signals import SignalContext
from quantlab5.v5.candidate_inventory import inventory
from datetime import date


def _short_market():
    nq, es = correlated_pair(weekdays(date(2020, 1, 2), date(2020, 1, 9)))
    return build_market(nq, es, np.full(nq.n, "NQZ0"), np.full(es.n, "ESZ0"))


def _mock_evaluator(market, spec, context, costs, *, shadow_baseline):
    cid = candidate_id(spec)
    t = {"A": 10.0, "B": 9.0, "C": 8.0}[spec["stage"]]
    return CandidateRecord(cid, spec["stage"], spec["family"], spec["side"], spec,
                           t, np.ones(40), np.ones(40, int), 120, 6, 1.0, 1.0,
                           cid, np.array([1], np.int32), np.array([1], np.int8))


def test_all_qualifying_families_expand_without_top_n(costs_cfg):
    market = _short_market()
    costs = CostModel(costs_cfg, "test")
    null = np.zeros((19, 30))
    trace = adaptive_search(market, costs, null, evaluator=_mock_evaluator)
    assert len(trace.records) == 331
    assert len(trace.expanded_families) == 30
    assert len(trace.b_winner_ids) == 28  # E11/E22 have no B axis
    assert len(trace.nominee_ids) == 56
    assert len(trace.qualifying_ids) == 331
    assert len(trace.exact_duplicate_of) == len(trace.behavior_duplicate_of) == 331


def test_no_stage_b_or_c_when_a_gate_fails(costs_cfg):
    trace = adaptive_search(_short_market(), CostModel(costs_cfg, "test"),
                            np.full((19, 30), 100.0), evaluator=_mock_evaluator)
    assert len(trace.records) == 60
    assert trace.expanded_families == () and trace.b_winner_ids == {}


def test_real_candidate_evaluation_uses_market_engine_and_daily_calendar(costs_cfg):
    market = _short_market()
    spec = inventory()["stage_a"][0]
    record = evaluate_spec(market, spec, SignalContext(market), CostModel(costs_cfg, "test"))
    assert record.candidate_id == candidate_id(spec)
    assert len(record.daily_r) == len(np.unique(market.nq.sday))
    assert record.trades == int(record.daily_count.sum())


def test_market_null_replays_the_same_adaptive_search_and_stops_at_frozen_look(costs_cfg):
    market = _short_market()
    seen_sources = []

    def evaluator(world, spec, context, costs, *, shadow_baseline):
        seen_sources.append(world.nq.source)
        return _mock_evaluator(world, spec, context, costs, shadow_baseline=shadow_baseline)

    out = replay_adaptive_null(market, MinuteSignFlipNull(joint=True), range(50),
                               CostModel(costs_cfg, "test"), np.full((19, 30), 100.0),
                               observed_global_statistic=0.0, evaluator=evaluator)
    assert out.decision.status == "NONSIGNIFICANT"
    assert len(out.traces) == len(out.seeds) == 50
    assert all(len(trace.records) == 60 for trace in out.traces)
    assert all(s.startswith("null:minute_sign_flip:") for s in seen_sources)


def test_stage_a_reference_is_rebuilt_from_market_surrogates(costs_cfg):
    ref = calibrate_stage_a_reference(_short_market(), MinuteSignFlipNull(joint=True),
                                      [11, 12], CostModel(costs_cfg, "test"),
                                      evaluator=_mock_evaluator)
    assert ref.shape == (2, 30)
    assert np.array_equal(ref, np.full((2, 30), 10.0))


def test_real_evaluator_runs_inside_market_level_null_replay(costs_cfg):
    market = _short_market()
    out = replay_adaptive_null(market, MinuteSignFlipNull(joint=True), [91],
                               CostModel(costs_cfg, "test"), np.full((19, 30), 100.0),
                               observed_global_statistic=0.0, looks=(1,))
    assert len(out.traces) == 1 and len(out.traces[0].records) == 60
    assert out.traces[0].records[0].stage == "A"


def test_fixed_risk_coverage_records_all_four_budgets_for_each_candidate(costs_cfg):
    market = _short_market()
    costs = CostModel(costs_cfg, "test")
    record = evaluate_spec(market, inventory()["stage_a"][0], SignalContext(market), costs)
    from dataclasses import replace
    trace = replace(adaptive_search(market, costs, np.full((19, 30), 100.0),
                                    evaluator=_mock_evaluator), records=(record,))
    result = coverage_for_trace(market, trace, costs)
    assert set(result[record.candidate_id]) == {250, 300, 350, 400}
    assert all(hasattr(x, "baseline_net_usd") and hasattr(x, "stress_net_usd")
               for x in result[record.candidate_id].values())
