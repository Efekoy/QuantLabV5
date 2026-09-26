"""Causality and interface smoke tests for every executable V5 family."""
from datetime import date

import numpy as np
import pytest

from quantlab5.data.market import build_market
from quantlab5.data.schema import bars_from_arrays
from quantlab5.synthetic.markets import session_timestamps, weekdays
from quantlab5.v5.candidate_inventory import (MECHANISMS, inventory,
                                              stage_c_interactions, stage_c_spec)
from quantlab5.v5.signals import SignalContext, _clock_quantile_kernel, signal_for_spec


def _market(days=75, rewrite_after=None):
    sessions = weekdays(date(2020, 1, 2), date(2020, 6, 30))[:days]
    ts = session_timestamps(sessions, rth_only=True)
    rng = np.random.default_rng(812)
    z = rng.normal(size=len(ts))
    e = .7*z + .714*rng.normal(size=len(ts))
    arrays = []
    for name, base, step in (("NQ", 10000, z), ("ES", 4000, e)):
        c = np.round((base + np.cumsum(step)) * 4) / 4
        o = np.r_[c[0], c[:-1]]
        h = np.maximum(o, c) + .25
        l = np.minimum(o, c) - .25
        if rewrite_after is not None:
            o[rewrite_after:] += 100
            h[rewrite_after:] += 100
            l[rewrite_after:] += 100
            c[rewrite_after:] += 100
        v = rng.integers(100, 300, size=len(ts))
        sym = np.full(len(ts), name + "Z0")
        arrays.append(bars_from_arrays(name, ts, o, h, l, c, v, sym))
    return build_market(arrays[0], arrays[1], np.full(len(ts), "NQZ0"), np.full(len(ts), "ESZ0"))


def test_all_thirty_stage_a_families_execute_and_have_causal_prefixes():
    original = _market()
    cutoff = 65*390
    changed = _market(rewrite_after=cutoff)
    before, after = SignalContext(original), SignalContext(changed)
    specs = [s for s in inventory()["stage_a"] if s["side"] == "long"]
    assert len(specs) == 30
    for spec in specs:
        a, _, stop_a = signal_for_spec(original, spec, before)
        b, _, stop_b = signal_for_spec(changed, spec, after)
        assert a.dtype == b.dtype == bool and len(a) == original.n
        assert np.array_equal(a[:cutoff], b[:cutoff]), spec["family"]
        assert np.allclose(stop_a[:cutoff], stop_b[:cutoff], equal_nan=True)


def test_short_spec_only_emits_short_mask_and_uses_next_bar_eligibility():
    market = _market()
    ctx = SignalContext(market)
    spec = next(s for s in inventory()["stage_a"] if s["family"] == "E07" and s["side"] == "short")
    lg, sh, stop = signal_for_spec(market, spec, ctx)
    assert not lg.any()
    assert not (sh & ~ctx.base_ok).any()
    assert np.isfinite(stop[sh]).all()


def test_registered_stage_c_children_are_parent_signal_subsets():
    market = _market()
    ctx = SignalContext(market)
    parent = next(s for s in inventory()["stage_b"] if s["family"] == "E02" and s["side"] == "long")
    parent_long, _, _ = signal_for_spec(market, parent, ctx)
    for interaction in ("previous_rth_open", "occupation", "c15"):
        child = stage_c_spec(parent, interaction)
        child_long, _, _ = signal_for_spec(market, child, ctx)
        assert not (child_long & ~parent_long).any()
        assert child["parent_id"]


def test_session_handoff_runs_on_full_globex_market_across_dst():
    sessions = weekdays(date(2021, 2, 1), date(2021, 3, 22))
    ts = session_timestamps(sessions)
    n = len(ts)
    bars = []
    for name, base in (("NQ", 10000.), ("ES", 4000.)):
        c = base + .25*np.arange(1, n+1)
        o = c-.25
        bars.append(bars_from_arrays(name, ts, o, c+.25, o-.25, c,
                                     np.full(n, 150), np.full(n, name+"Z0")))
    market = build_market(bars[0], bars[1], np.full(n, "NQZ0"), np.full(n, "ESZ0"))
    spec = next(s for s in inventory()["stage_a"] if s["family"] == "E11" and s["side"] == "long")
    signals, _, _ = signal_for_spec(market, spec)
    assert signals.any()
    assert len(np.unique(market.nq.sday[signals])) == signals.sum()  # first RTH C15 only


def test_cross_market_rules_require_synchronized_es_bar():
    from quantlab5.synthetic.markets import correlated_pair
    days = weekdays(date(2020, 1, 2), date(2020, 4, 15))
    nq, es = correlated_pair(days, missing_every=97)
    market = build_market(nq, es, np.full(nq.n, "NQZ0"), np.full(es.n, "ESZ0"))
    ctx = SignalContext(market)
    for family in ("E12", "E13", "E14", "E29"):
        spec = next(s for s in inventory()["stage_a"] if s["family"] == family and s["side"] == "long")
        long, _, _ = signal_for_spec(market, spec, ctx)
        assert not long[~market.evalid].any(), family


def test_every_stage_b_axis_and_every_reachable_c_interaction_executes():
    market = _market()
    ctx = SignalContext(market)
    inv = inventory()
    assert len(inv["stage_b"]) == 214
    for spec in inv["stage_b"]:
        lg, sh, stop = signal_for_spec(market, spec, ctx)
        assert len(lg) == len(sh) == len(stop) == market.n
    for mechanism in MECHANISMS:
        parents = [s for s in inv["stage_b"] if s["family"] == mechanism.code]
        if not parents:
            continue
        for interaction in stage_c_interactions(mechanism):
            spec = stage_c_spec(parents[0], interaction)
            lg, sh, _ = signal_for_spec(market, spec, ctx)
            assert not (lg & sh).any()


def test_unregistered_stage_a_and_b_parameters_fail_closed():
    market = _market(days=4)
    for stage in ("A", "B"):
        original = inventory()["stage_a" if stage == "A" else "stage_b"][0]
        changed = dict(original, threshold=12345.0)
        with pytest.raises(ValueError, match="unregistered"):
            signal_for_spec(market, changed)


def test_fast_same_clock_reference_uses_only_prior_distinct_sessions():
    values = np.array([1., 2., 3., 4., np.nan, 6., 7., 8.])
    days = np.array([1, 1, 2, 3, 4, 5, 6, 7])
    clocks = np.full(len(days), 930)
    actual = _clock_quantile_kernel(values, clocks, days, 2, .5)
    expected = np.array([np.nan, np.nan, np.nan, 2.5, 3.5,
                         np.nan, np.nan, 6.5])
    np.testing.assert_allclose(actual, expected, equal_nan=True)


def test_fast_same_clock_reference_matches_plain_history_calculation():
    rng = np.random.default_rng(15)
    days = np.repeat(np.arange(35), 3)
    clocks = np.tile(np.array([930, 931, 932]), 35)
    values = rng.normal(size=len(days))
    values[[7, 46]] = np.nan
    actual = _clock_quantile_kernel(values, clocks, days, 7, .8)
    expected = np.full(len(values), np.nan)
    for i in range(len(values)):
        prev = values[(clocks == clocks[i]) & (days < days[i])][-7:]
        if len(prev) == 7 and np.isfinite(prev).all():
            expected[i] = np.quantile(prev, .8)
    np.testing.assert_allclose(actual, expected, equal_nan=True)
