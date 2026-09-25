"""Entry timing, stop/target ambiguity, time exits and session flattening.

(Ported from QuantLabV3 tests/test_engine_timing.py. Dropped: the two tests that
exercised V3 indicators / the V3 breakout family (not inherited). Rewritten: the
session-flat test now uses V4 run_signals instead of V3 execute_managed. Added: the
target trade-through policy.)"""
import numpy as np

from quantlab5.engine.backtest import run_backtest


def _arrays(n, o=None, h=None, l=None, c=None):
    c = np.asarray(c if c is not None else 100 + np.arange(n, dtype=float))
    o = np.asarray(o if o is not None else c - 0.25)
    h = np.asarray(h if h is not None else np.maximum(o, c) + 0.5)
    l = np.asarray(l if l is not None else np.minimum(o, c) - 0.5)
    tmin = np.arange(n, dtype=np.int64) + 27_000_000
    entry_ok = np.ones(n, bool)
    entry_ok[0] = False
    flat = np.zeros(n, bool)
    flat[-1] = True
    return o, h, l, c, tmin, entry_ok, flat


def test_close_signal_enters_at_next_open_never_same_bar():
    o, h, l, c, tmin, ok, flat = _arrays(10)
    sig = np.zeros(10, bool)
    sig[3] = True                       # condition true at the CLOSE of bar 3
    tr = run_backtest(o, h, l, c, tmin, ok, flat, sig, np.zeros(10, bool), "long", hold=2)
    assert tr.entry_idx.tolist() == [4]
    assert tr.entry_px[0] == o[4]       # the next bar's OPEN
    assert tr.entry_px[0] != c[3]       # never the close that produced the signal
    # hold 2 minutes: exit at the close of bar 5
    assert tr.exit_idx.tolist() == [5] and tr.exit_px[0] == c[5]


def test_short_side_and_direction_filter():
    o, h, l, c, tmin, ok, flat = _arrays(10)
    s = np.zeros(10, bool)
    s[2] = True
    tr = run_backtest(o, h, l, c, tmin, ok, flat, np.zeros(10, bool), s, "long", hold=1)
    assert tr.n == 0                    # long-only ignores short signals
    tr = run_backtest(o, h, l, c, tmin, ok, flat, np.zeros(10, bool), s, "short", hold=1)
    assert tr.side.tolist() == [-1] and tr.points[0] == -(c[3] - o[3])


def test_conflicting_signals_in_both_mode_take_no_trade():
    o, h, l, c, tmin, ok, flat = _arrays(6)
    s = np.zeros(6, bool)
    s[2] = True
    assert run_backtest(o, h, l, c, tmin, ok, flat, s, s, "both", hold=1).n == 0


def test_same_bar_stop_and_target_is_pessimistic_by_default():
    n = 6
    o = np.array([100, 100, 100, 100, 100, 100.0])
    c = o.copy()
    h = np.array([100.5, 100.5, 103, 100.5, 100.5, 100.5])
    l = np.array([99.5, 99.5, 97, 99.5, 99.5, 99.5])
    tmin = np.arange(n, dtype=np.int64)
    ok = np.ones(n, bool); ok[0] = False
    flat = np.zeros(n, bool); flat[-1] = True
    sig = np.zeros(n, bool); sig[0] = True          # enter at bar 1 open = 100
    d = np.full(n, 2.0)                             # stop 98, target 102
    pes = run_backtest(o, h, l, c, tmin, ok, flat, sig, np.zeros(n, bool), "long", 60, 1, d, 1, d)
    assert pes.exit_idx[0] == 2 and pes.exit_px[0] == 98 and pes.reason[0] == 1 and pes.ambiguous[0]
    opt = run_backtest(o, h, l, c, tmin, ok, flat, sig, np.zeros(n, bool), "long", 60, 1, d, 1, d,
                       ambiguity="optimistic")
    assert opt.exit_px[0] == 102 and opt.reason[0] == 2 and opt.ambiguous[0]


def test_gap_through_stop_fills_at_open_and_target_never_better():
    n = 5
    o = np.array([100, 100, 95, 100, 100.0])
    c = np.array([100, 100, 95.5, 100, 100.0])
    h = np.array([100.5, 100.5, 96, 100.5, 100.5])
    l = np.array([99.5, 99.5, 94.5, 99.5, 99.5])
    tmin = np.arange(n, dtype=np.int64)
    ok = np.ones(n, bool); ok[0] = False
    flat = np.zeros(n, bool); flat[-1] = True
    sig = np.zeros(n, bool); sig[0] = True
    d = np.full(n, 2.0)
    tr = run_backtest(o, h, l, c, tmin, ok, flat, sig, np.zeros(n, bool), "long", 60, 1, d, 1, d)
    assert tr.exit_px[0] == 95 and tr.reason[0] == 1 and not tr.ambiguous[0]   # worse than the 98 stop
    o2 = np.array([100, 100, 106, 100, 100.0])
    h2 = np.array([100.5, 100.5, 107, 100.5, 100.5])
    l2 = np.array([99.5, 99.5, 105, 99.5, 99.5])
    c2 = np.array([100, 100, 106.5, 100, 100.0])
    tr = run_backtest(o2, h2, l2, c2, tmin, ok, flat, sig, np.zeros(n, bool), "long", 60, 1, d, 1, d)
    assert tr.exit_px[0] == 102 and tr.reason[0] == 2                          # not the better 106 open


def test_session_flat_and_no_position_crosses_sessions(sessions_cfg):
    from quantlab5.data.schema import bars_from_arrays
    from quantlab5.engine.execution import get_window, run_signals, window_arrays
    import pandas as pd
    d1 = pd.date_range(pd.Timestamp("2020-10-05 09:30", tz="America/New_York"), periods=390, freq="min")
    d2 = pd.date_range(pd.Timestamp("2020-10-06 09:30", tz="America/New_York"), periods=390, freq="min")
    ts = d1.append(d2).tz_convert("UTC").as_unit("ns").asi8
    c = 1000 + np.cumsum(np.random.default_rng(0).standard_normal(len(ts)))
    o = np.r_[c[0], c[:-1]]
    v = bars_from_arrays("NQ", ts, o, np.maximum(o, c) + 0.5, np.minimum(o, c) - 0.5, c, np.full(len(ts), 10))
    win = get_window(sessions_cfg, "rth")
    sig = np.zeros(len(ts), bool)
    sig[350] = True        # 15:20 on day 1 -> would want to hold 240 minutes
    sig[389] = True        # 15:59 on day 1: its "next bar" is in the NEXT session
    tr = run_signals(v, sig, np.zeros(len(ts), bool), win, "long", hold=240)
    assert tr.n == 1
    assert v.sday[tr.exit_idx[0]] == v.sday[tr.entry_idx[0]]
    assert v.sm[tr.exit_idx[0]] == 1319               # the 15:59 bar, flat at its close
    ok, flat = window_arrays(v, win)
    assert not ok[390]                                # day 2's first bar cannot act on day 1's last signal
    assert flat[389]


def test_time_exit_is_exact_hold():
    o, h, l, c, tmin, ok, flat = _arrays(20)
    sig = np.zeros(20, bool)
    sig[1] = True
    for hold in (1, 5, 15):
        tr = run_backtest(o, h, l, c, tmin, ok, flat, sig, np.zeros(20, bool), "long", hold=hold)
        assert tmin[tr.exit_idx[0]] + 1 - tmin[tr.entry_idx[0]] == hold


def test_target_requires_trade_through_not_a_touch():
    n = 6
    o = np.array([100, 100, 100, 100, 100, 100.0])
    c = o.copy()
    h = np.array([100.5, 100.5, 102.0, 102.25, 100.5, 100.5])   # bar 2 touches 102, bar 3 trades through
    l = np.array([99.5, 99.5, 99.5, 99.5, 99.5, 99.5])
    tmin = np.arange(n, dtype=np.int64)
    ok = np.ones(n, bool); ok[0] = False
    flat = np.zeros(n, bool); flat[-1] = True
    sig = np.zeros(n, bool); sig[0] = True
    d = np.full(n, 2.0)
    touch = run_backtest(o, h, l, c, tmin, ok, flat, sig, np.zeros(n, bool), "long", 60, 0, None, 1, d,
                         tgt_through=0.0)
    assert touch.exit_idx[0] == 2 and touch.exit_px[0] == 102
    thru = run_backtest(o, h, l, c, tmin, ok, flat, sig, np.zeros(n, bool), "long", 60, 0, None, 1, d,
                        tgt_through=0.25)
    assert thru.exit_idx[0] == 3 and thru.exit_px[0] == 102      # filled AT the target, never better
