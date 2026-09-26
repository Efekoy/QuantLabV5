"""Check E24's rolling histogram against its original window formulation."""
from datetime import date

import numpy as np
import yaml

from quantlab5.data.market import build_market
from quantlab5.engine.costs import CostModel
from quantlab5.features import ops as O
from quantlab5.synthetic.markets import correlated_pair, weekdays
from quantlab5.v5.signals import SignalContext, _valid_div
from quantlab5.v5.market_search import adaptive_search


def _reference_e24(ctx, lookback, threshold):
    m = ctx.market
    z = _valid_div(ctx.r, ctx.v)
    sm, day = np.asarray(m.nq.sm), np.asarray(m.nq.sday)
    out = np.zeros(m.n, np.int8)
    bins = np.array([-np.inf, -2, -1, -.5, 0, .5, 1, 2, np.inf])
    by_clock = {int(clock): np.flatnonzero(sm == clock) for clock in np.unique(sm)}
    gs = O.group_start(m.gid)
    for i in np.flatnonzero(ctx.c15):
        if i-lookback+1 < gs[i] or not np.isfinite(z[i-lookback+1:i+1]).all():
            continue
        previous = by_clock[int(sm[i])]
        previous = previous[day[previous] < day[i]][-20:]
        if len(previous) != 20:
            continue
        refs = [z[j-lookback+1:j+1] for j in previous
                if j-lookback+1 >= gs[j] and np.isfinite(z[j-lookback+1:j+1]).all()]
        if len(refs) != 20:
            continue
        p = np.histogram(z[i-lookback+1:i+1], bins)[0].astype(float) + .5
        q = np.histogram(np.concatenate(refs), bins)[0].astype(float) + .5
        p /= p.sum(); q /= q.sum()
        mix = .5*(p+q)
        js = .5*(np.sum(p*np.log(p/mix)) + np.sum(q*np.log(q/mix)))
        if js > threshold:
            out[i] = ctx.direction15[i]
    return out


def test_e24_rolling_bins_match_original_windows():
    nq, es = correlated_pair(weekdays(date(2020, 1, 2), date(2020, 2, 13)))
    market = build_market(nq, es, np.full(nq.n, "NQZ0"), np.full(es.n, "ESZ0"))
    ctx = SignalContext(market)
    days, inverse = np.unique(np.asarray(market.nq.sday), return_inverse=True)
    assert np.array_equal(ctx.session_days, days)
    assert np.array_equal(ctx.session_inverse, inverse)
    assert np.array_equal(ctx.calendar_years, market.years())
    ctx.c15[:] = True  # Exercise every eligible window, including both directions.
    for lookback in (15, 30, 60):
        for threshold in (-1.0, 0.15):
            assert np.array_equal(ctx._e24(lookback, threshold),
                                  _reference_e24(ctx, lookback, threshold))


def test_e24_search_trace_matches_original_windows(monkeypatch):
    nq, es = correlated_pair(weekdays(date(2020, 1, 2), date(2020, 2, 13)))
    market = build_market(nq, es, np.full(nq.n, "NQZ0"), np.full(es.n, "ESZ0"))
    from pathlib import Path
    cfg = yaml.safe_load((Path(__file__).resolve().parents[1] / "config/costs.yaml").read_text())
    costs = CostModel(cfg, "test")
    reference = np.full((19, 30), 100.0)
    fast = adaptive_search(market, costs, reference)
    monkeypatch.setattr(SignalContext, "_e24", _reference_e24)
    original = adaptive_search(market, costs, reference)
    assert len(fast.records) == len(original.records)
    assert fast.expanded_families == original.expanded_families
    assert fast.b_winner_ids == original.b_winner_ids
    assert fast.qualifying_ids == original.qualifying_ids
    assert fast.nominee_ids == original.nominee_ids
    assert fast.exact_duplicate_of == original.exact_duplicate_of
    assert fast.behavior_duplicate_of == original.behavior_duplicate_of
    assert fast.pair_similarities == original.pair_similarities
    assert fast.global_statistic == original.global_statistic
    assert fast.family_statistics == original.family_statistics
    for a, b in zip(fast.records, original.records):
        assert a.candidate_id == b.candidate_id
        assert a.statistic == b.statistic
        assert a.trades == b.trades
        assert a.stress_net_r == b.stress_net_r
        assert a.matched_excess_r == b.matched_excess_r
        assert a.signal_hash == b.signal_hash
        for name in ("daily_r", "daily_count", "entry_indices", "trade_sides", "exit_indices"):
            assert np.array_equal(getattr(a, name), getattr(b, name))
