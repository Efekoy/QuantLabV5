"""Permanent V5.4 grammar and causal management checks on synthetic bars only."""
from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import numpy as np

from quantlab5.synthetic.market_builders import synthetic_market
from quantlab5.synthetic.markets import rising_market
from quantlab5.engine.execution import get_window, run_signals
from quantlab5.v54.engine import _sparse, evaluate
from quantlab5.v54.events import EventCache, Events
from quantlab5.v54.inference import discovery_qualifies, holm_adjust, validation_label
from quantlab5.v54.universe import (CORE, core_neighbor_indices, counts, id_for,
                                     managements, row_index, signal_configs,
                                     spec_at, specifications)


def test_all_30_families_and_exact_combinatorial_count():
    c = counts()
    assert len(CORE) == 30
    assert c["signal_configs"] == sum(c["family_signal_configs"].values())
    assert c["total_specs"] == c["signal_configs"] * c["management_variants"]
    assert all(n > 1000 for n in c["family_total_specs"].values())
    assert c["total_specs"] > 10_000_000
    assert len({id_for(x) for x in list(specifications("E01"))[:500]}) == 500
    assert len({tuple(sorted(x.as_dict().items())) for x in managements()}) == len(managements())
    for i in (0, 197, 198, 100_000, c["total_specs"]-1):
        assert row_index(spec_at(i)) == i
    assert len(core_neighbor_indices(spec_at(0))) == 2


def test_all_family_states_execute_on_seeded_synthetic_world():
    market = synthetic_market(date(2012, 1, 2), date(2012, 1, 20), seed=7)
    cache = EventCache(market)
    for family in CORE:
        events = cache.events(next(signal_configs(family)), "atr_1")
        assert events.family == family
        assert np.all(events.entry_idx > 0)
        assert np.all(events.stop_dist >= .25)


def _run(bars, highs, lows, *, opens=None, target=0., be=0., partial=0., trail=0., mech=False,
         mechanism_state=None):
    n = len(highs)
    o = np.full(n, 100., dtype=float) if opens is None else np.asarray(opens, float)
    h = np.asarray(highs, float)
    l = np.asarray(lows, float)
    c = np.full(n, 100., dtype=float)
    flat = np.zeros(n, bool)
    flat[-1] = True
    years = np.full(n, 2020, np.int32)
    state = np.ones(n, np.int8) if mechanism_state is None else np.asarray(mechanism_state, np.int8)
    return _sparse(o, h, l, c, np.arange(n, dtype=np.int64),
                   np.zeros(n, np.int16), flat, np.array([1], np.int32),
                   np.array([1], np.int8), np.array([1.]), years, state,
                   target, be, partial, trail, -1, mech, 0., 0.,
                   np.zeros((2, 1440)), True)


def test_same_bar_stop_wins_target_ambiguity():
    metrics, entry, exit_, r = _run(None, [100, 103, 100], [100, 98, 100], target=1.)
    assert metrics[0] == 1 and r.tolist() == [-1.]
    assert entry.tolist() == [1] and exit_.tolist() == [1]


def test_breakeven_change_is_effective_only_on_next_bar():
    metrics, _, exit_, r = _run(None, [100, 101.5, 100], [100, 99.5, 99.5], be=1.)
    assert metrics[0] == 1 and r.tolist() == [0.]
    assert exit_.tolist() == [2]


def test_partial_is_one_of_two_integer_contracts():
    metrics, _, exit_, r = _run(None, [100, 101.5, 100], [100, 99.5, 98.5], partial=1.)
    assert metrics[0] == 1 and r.tolist() == [0.]
    assert exit_.tolist() == [2]


def test_trail_is_based_on_completed_bar():
    metrics, _, exit_, r = _run(None, [100, 102.5, 102], [100, 99.5, 100.5],
                                opens=[100, 100, 102], trail=1.)
    assert metrics[0] == 1 and r.tolist() == [1.5]
    assert exit_.tolist() == [2]


def test_mechanism_exit_uses_previous_completed_state():
    metrics, _, exit_, r = _run(None, [100, 100.5, 100.5, 100],
                                [100, 99.5, 99.5, 100], mech=True,
                                mechanism_state=[1, 1, 0, 0])
    assert metrics[0] == 1 and r.tolist() == [0.]
    assert exit_.tolist() == [3]


def test_capture_rerun_reproduces_first_pass_metrics():
    b = rising_market(n=30)
    market = SimpleNamespace(nq=b, years=lambda: np.full(b.n, 2020))
    events = Events(np.array([2], np.int32), np.array([1], np.int8),
                    np.array([2.]), np.r_[np.zeros(29, bool), True], "E01", {},
                    np.ones(b.n, np.int8), np.full(b.n, 2020, np.int32))
    for management in managements():
        a = evaluate(market, events, management.as_dict(),
                     baseline_cost_points=.1, stress_cost_points=.2, capture=False)
        z = evaluate(market, events, management.as_dict(),
                     baseline_cost_points=.1, stress_cost_points=.2, capture=True)
        assert np.array_equal(a[0], z[0], equal_nan=True)
        assert len(z[1]) == int(z[0][0])


def test_fixed_stop_target_matches_reference_engine_on_seeded_world():
    market = synthetic_market(date(2012, 1, 2), date(2012, 2, 28), seed=1)
    cache = EventCache(market)
    config = {"family": "E03", "lookback": 10, "threshold": .75,
              "direction": "long", "session": "rth", "filters": (),
              "entry": "next_open"}
    events = cache.events(config, "atr_1")
    state = cache.context.direction("E03", 10, .75) == 1
    reference = run_signals(market.nq, state, np.zeros(market.n, bool),
                            get_window(cache.sessions_cfg, "rth"), "long",
                            hold=60, stop_dist=cache.context.stop,
                            tgt_dist=cache.context.stop)
    management = next(x.as_dict() for x in managements()
                      if x.template == "T1_FIXED_TARGET" and x.stop == "atr_1"
                      and x.target_r == 1.0)
    optimized = evaluate(market, events, management, baseline_cost_points=0.,
                         stress_cost_points=0., capture=True)
    assert reference.n == int(optimized[0][0]) > 100
    assert np.array_equal(reference.entry_idx, optimized[1])
    assert np.array_equal(reference.exit_idx, optimized[2])
    assert np.allclose(np.asarray(reference.points)/np.asarray(reference.initial_risk),
                       optimized[3], rtol=0., atol=2e-13)


def test_filters_and_structure_stops_are_past_only():
    full = synthetic_market(date(2012, 1, 2), date(2012, 1, 20), seed=12)
    from quantlab5.data.market import build_market
    cut = int(np.searchsorted(full.nq.sday, np.unique(full.nq.sday)[-5]))
    ecut = int(np.searchsorted(full.es.sday, np.unique(full.nq.sday)[-5]))
    prefix = build_market(full.nq.slice(0, cut), full.es.slice(0, ecut),
                          full.nq_symbols[:cut], full.es_symbols[:ecut])
    a, b = EventCache(prefix), EventCache(full)
    config = {"family": "E03", "lookback": 20, "threshold": 1.5,
              "direction": "both", "session": "rth_am",
              "filters": ("vol_high", "eff_high"), "entry": "delay_one_bar"}
    for filter_name in config["filters"]:
        assert np.array_equal(a.filter(filter_name), b.filter(filter_name)[:cut])
    for stop in ("atr_1", "signal_bar", "swing_5", "swing_15"):
        ea, eb = a.events(config, stop), b.events(config, stop)
        mask = eb.entry_idx < cut-2
        assert np.array_equal(ea.entry_idx, eb.entry_idx[mask])
        assert np.array_equal(ea.side, eb.side[mask])
        assert np.array_equal(ea.stop_dist, eb.stop_dist[mask], equal_nan=True)


def test_no_cap_discovery_gate_and_dependence_safe_holm():
    assert discovery_qualifies(trades=120, active_years=6, net_r=.01,
                               stress_net_r=.01, matched_excess_r=.01)
    assert not discovery_qualifies(trades=119, active_years=6, net_r=1,
                                   stress_net_r=1, matched_excess_r=1)
    adjusted = holm_adjust(np.array([.01, .04, .03]))
    assert np.allclose(adjusted, [.03, .06, .06])
    assert validation_label(adjusted_p=.03, trades=40, active_years=2,
                            mean_daily_net_r=.01, stress_net_r=1,
                            matched_excess_r=.01, upper95_mean_daily_net_r=.02) == "SUPPORTED"
    assert validation_label(adjusted_p=.06, trades=40, active_years=2,
                            mean_daily_net_r=.01, stress_net_r=1,
                            matched_excess_r=.01, upper95_mean_daily_net_r=.02) == "INCONCLUSIVE / UNDERPOWERED"


def test_v54_access_gate_refuses_premature_holdout_and_live_forward(monkeypatch, tmp_path):
    import quantlab5.v54.access as access
    project = SimpleNamespace(root=tmp_path, partitions=lambda: {
        "registry": {"historical_audit_2_last_session": {
            "NQ": "2026-08-10", "ES": "2026-08-14"}}})
    monkeypatch.setattr(access, "ready", lambda _: (True, "frozen"))
    monkeypatch.setattr(access, "_frozen_file", lambda *args: (True, "frozen"))
    cols = ["open", "high", "low", "close", "volume", "symbol"]
    assert access.authorize(project, "V5_4_FROZEN_BROAD_DISCOVERY", "DISCOVERY",
                            "NQ", "2010-06-08", "2018-12-31", cols,
                            "VALIDATION_FROZEN")[0]
    assert not access.authorize(project, "V5_4_FROZEN_VALIDATION", "VALIDATION",
                                "NQ", "2019-01-02", "2022-12-30", cols,
                                "DISCOVERY")[0]
    assert not access.authorize(project, "V5_4_FROZEN_BROAD_DISCOVERY", "VALIDATION",
                                "NQ", "2019-01-02", "2022-12-30", cols,
                                "VALIDATION_FROZEN")[0]
    assert not access.authorize(project, "V5_4_BLIND_AUDIT_2", "HISTORICAL_AUDIT_2",
                                "NQ", "2026-01-02", "2026-08-14", cols,
                                "VALIDATION_FROZEN")[0]
    assert not access.authorize(project, "V5_4_FROZEN_BROAD_DISCOVERY", "LIVE_FORWARD",
                                "NQ", "2010-06-08", "2018-12-31", cols,
                                "VALIDATION_FROZEN")[0]


def test_short_stop_gap_and_favorable_limit_gap_are_conservative():
    o = np.array([100., 100., 102., 100.])
    h = np.array([100., 100.5, 102.5, 100.])
    l = np.array([100., 99.5, 101.5, 100.])
    years = np.full(4, 2020, np.int32)
    flat = np.array([False, False, False, True])
    args = (o, h, l, np.full(4, 100.), np.arange(4, dtype=np.int64),
            np.zeros(4, np.int16), flat, np.array([1], np.int32),
            np.array([-1], np.int8), np.array([1.]), years,
            np.full(4, -1, np.int8))
    stop_gap = _sparse(*args, 1., 0., 0., 0., -1, False, 0., 0.,
                       np.zeros((2, 1440)), True)
    assert stop_gap[3].tolist() == [-2.]
    # A short target reached on a favorable opening gap executes at its limit.
    o2 = o.copy(); o2[2] = 98.
    h2 = h.copy(); h2[2] = 98.5
    l2 = l.copy(); l2[2] = 97.5
    favorable = _sparse(o2, h2, l2, *args[3:], 1., 0., 0., 0., -1,
                        False, 0., 0., np.zeros((2, 1440)), True)
    assert favorable[3].tolist() == [1.]


def test_first_pass_resumes_at_next_complete_signal_group(tmp_path, monkeypatch):
    import research.run_v54_discovery as runner
    market = synthetic_market(date(2012, 1, 2), date(2012, 1, 6), seed=21)
    first, second = list(signal_configs("E03"))[:2]
    monkeypatch.setattr(runner, "WORK", tmp_path)
    monkeypatch.setattr(runner, "ROWS", tmp_path/"first_pass.npy")
    monkeypatch.setattr(runner, "PROGRESS", tmp_path/"progress.json")
    monkeypatch.setattr(runner, "QUALIFIERS", tmp_path/"qualifying_rows.npy")
    monkeypatch.setattr(runner, "DONE", tmp_path/"first_pass_complete.json")
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "_configs", lambda: iter((first, second)))
    monkeypatch.setattr(runner, "counts", lambda: {"total_specs": 2*len(managements())})
    monkeypatch.setattr(runner, "file_sha256", lambda _: "frozen-hash")
    monkeypatch.setattr(runner, "_shadow_clock_baseline", lambda *args: np.zeros((2, 1440)))
    costs = SimpleNamespace(per_trade_points=lambda *args: .1)
    rows, progress = runner.first_pass(market, costs, limit_signal_configs=1)
    assert progress["completed_rows"] == len(managements())
    original = rows[:len(managements())].copy()
    rows, progress = runner.first_pass(market, costs, limit_signal_configs=2)
    assert progress["completed_rows"] == 2*len(managements())
    assert rows[:len(managements())].tobytes() == original.tobytes()
    assert rows[-1]["candidate_id"] != b""
