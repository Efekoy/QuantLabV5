"""Engine behaviour on synthetic markets with KNOWN properties (software correctness, not research)."""
from datetime import date

import numpy as np
import pytest

from quantlab5.diagnostics.lookahead import check_trade_causality
from quantlab5.engine.execution import ExecutionPolicy, get_window, run_signals, window_arrays
from quantlab5.synthetic import markets as M


@pytest.fixture()
def rth(sessions_cfg):
    return get_window(sessions_cfg, "rth")


@pytest.fixture()
def globex(sessions_cfg):
    return get_window(sessions_cfg, "globex")


def _sig(n, idx):
    s = np.zeros(n, bool)
    s[list(idx)] = True
    return s


def test_rising_market_long_wins_short_loses_exact_points(rth):
    b = M.rising_market(60)
    s = _sig(b.n, [5])
    lg = run_signals(b, s, np.zeros(b.n, bool), rth, "long", hold=10)
    assert lg.entry_idx.tolist() == [6] and lg.entry_px[0] == b.o[6]          # next bar's open
    assert lg.exit_idx.tolist() == [15] and lg.points[0] == b.c[15] - b.o[6] == 10.0
    sh = run_signals(b, np.zeros(b.n, bool), s, rth, "short", hold=10)
    assert sh.points[0] == -10.0


def test_falling_market_mirrors_rising(rth):
    b = M.falling_market(60)
    s = _sig(b.n, [5])
    assert run_signals(b, s, np.zeros(b.n, bool), rth, "long", hold=10).points[0] == -10.0
    assert run_signals(b, np.zeros(b.n, bool), s, rth, "short", hold=10).points[0] == 10.0


def test_flat_market_gives_zero_points_and_negative_net_after_costs(rth, costs_cfg):
    from quantlab5.engine.costs import CostModel
    b = M.flat_market(60)
    tr = run_signals(b, _sig(b.n, [3, 20]), np.zeros(b.n, bool), rth, "long", hold=5)
    assert tr.n == 2 and (tr.points == 0).all()
    cm = CostModel(costs_cfg, "t")
    assert cm.per_trade("SYN" if "SYN" in cm.instruments else "NQ", "baseline") > 0


def test_signal_on_last_bar_never_fills_and_no_same_bar_entry(rth):
    b = M.rising_market(30)
    tr = run_signals(b, _sig(b.n, [b.n - 1]), np.zeros(b.n, bool), rth, "long", hold=5)
    assert tr.n == 0
    tr = run_signals(b, _sig(b.n, range(0, b.n, 7)), np.zeros(b.n, bool), rth, "long", hold=3)
    assert (tr.entry_idx >= 1).all()
    for e in tr.entry_idx:
        assert tr.entry_px[list(tr.entry_idx).index(e)] == b.o[e]


def test_stop_and_target_policy_on_known_bars(rth):
    b = M.rising_market(60, step=1.0)
    s = _sig(b.n, [5])
    # target 3 points: long entered at o[6]; closes rise 1/bar, high = close + 0.25 -> trade-through needed
    tr = run_signals(b, s, np.zeros(b.n, bool), rth, "long", hold=30, stop_dist=5.0, tgt_dist=3.0,
                     policy=ExecutionPolicy("pessimistic", 1))
    assert tr.reason[0] == 2 and tr.exit_px[0] == b.o[6] + 3.0
    assert tr.exit_idx[0] == 8          # bar 8 high = o[6]+3.25 >= target + 1 tick
    # a short stop 2 points above entry on a rising market is hit at the stop price
    tr = run_signals(b, np.zeros(b.n, bool), s, rth, "short", hold=30, stop_dist=2.0)
    assert tr.reason[0] == 1 and tr.exit_px[0] == b.o[6] + 2.0


def test_session_close_and_no_trade_crosses_sessions(globex):
    b = M.session_boundary_market()
    s = np.zeros(b.n, bool)
    s[::97] = True
    tr = run_signals(b, s, np.zeros(b.n, bool), globex, "long", hold="eod")
    assert tr.n > 0
    assert (b.sday[tr.entry_idx] == b.sday[tr.exit_idx]).all()
    assert (np.asarray(b.sm)[tr.exit_idx] <= 1319).all()        # flat by 16:00 (last bar 15:59)


def test_no_trade_crosses_a_contract_roll(globex):
    b = M.roll_boundary_market()
    roll = int(np.nonzero(np.diff(b.seg))[0][0] + 1)
    s = np.zeros(b.n, bool)
    s[roll - 3: roll + 3] = True
    tr = run_signals(b, s, np.zeros(b.n, bool), globex, "long", hold=600)
    assert (b.seg[tr.entry_idx] == b.seg[tr.exit_idx]).all()
    ok, flat = window_arrays(b, globex)
    assert not ok[roll]                 # cannot enter on the new contract's first bar from an old-contract signal


def test_planted_edge_is_captured_exactly(globex):
    b = M.planted_edge_market([date(2020, 10, 5), date(2020, 10, 6)])
    sig = M.planted_edge_signal(b)
    tr = run_signals(b, sig, np.zeros(b.n, bool), globex, "long", hold=M.PLANT_BARS)
    assert tr.n > 0
    # entry at the open of the first drift bar (= marker close), exit at close of the 5th drift bar
    assert np.allclose(tr.points, M.PLANT_BARS * M.PLANT_DRIFT)


def test_zero_edge_market_same_rule_is_not_systematically_profitable(globex):
    b = M.random_zero_edge_market([date(2020, 10, 5), date(2020, 10, 6)])
    sig = M.planted_edge_signal(b)
    tr = run_signals(b, sig, np.zeros(b.n, bool), globex, "long", hold=M.PLANT_BARS)
    assert tr.n > 0 and not np.allclose(tr.points, M.PLANT_BARS * M.PLANT_DRIFT)


def test_engine_pipeline_is_causal_under_future_rewrites(globex):
    b = M.random_zero_edge_market([date(2020, 10, 5)])

    def pipeline(bars):
        c = np.asarray(bars.c)
        sig = np.zeros(bars.n, bool)
        sig[5:] = c[5:] > c[:-5]          # causal: compares with 5 bars ago
        return run_signals(bars, sig, ~sig, globex, "both", hold=20, stop_dist=3.0, tgt_dist=4.0)

    assert check_trade_causality(pipeline, b, [200, 600, 1000]) == []


def test_lookahead_bug_in_a_signal_is_detected(globex):
    b = M.random_zero_edge_market([date(2020, 10, 5)])

    def cheating_pipeline(bars):
        c = np.asarray(bars.c)
        sig = np.zeros(bars.n, bool)
        sig[:-3] = c[3:] > c[:-3]         # BUG: peeks 3 bars into the future
        return run_signals(bars, sig, np.zeros(bars.n, bool), globex, "long", hold=2)

    assert check_trade_causality(cheating_pipeline, b, [300, 700]) != []
