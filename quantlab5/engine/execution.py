"""Turn (signals + exits + session window) into trades.

(Adapted from quantlab3/engine/execution.py. Kept: EXECUTION_ASSUMPTIONS,
window_arrays (entry/flat masks from sessions and contract segments), candidates.
Removed: execute_managed / stop_arrays, which were coupled to the V3 management
template library and V3 strategy families.)

Signals are boolean arrays aligned to the bars: sig[t] = "condition true at the
CLOSE of bar t". Research code never computes fills itself.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from quantlab5.data.sessions import Window, load_windows
from quantlab5.engine.backtest import Trades, run_backtest

EXECUTION_ASSUMPTIONS = {
    "signal_timing": "condition evaluated at bar close",
    "entry": "market order at the open of the next bar (same session and contract)",
    "time_exit": "scheduled; fills at the close of the last bar of the holding period",
    "stop": "stop order; gap through the stop fills at the bar open",
    "target": "limit order; fills at the target price (never better) only when the bar trades at least "
              "target_trade_through_ticks beyond it; a touch is not a fill",
    "same_bar_stop_and_target": "resolved by ambiguity policy (baseline: stop first)",
    "session_end": "flat at the close of the last bar before the window's flat time",
    "contract_roll": "flat at the close of the last bar of the old contract; no entry on the new contract's first bar",
    "position": "one position at a time, no pyramiding",
}


@dataclass(frozen=True)
class ExecutionPolicy:
    ambiguity: str = "pessimistic"
    target_trade_through_ticks: float = 1.0

    @classmethod
    def from_config(cls, cfg: dict) -> "ExecutionPolicy":
        return cls(cfg.get("ambiguity_policy", "pessimistic"), float(cfg.get("target_trade_through_ticks", 1)))


def window_arrays(bars, window: Window, tradable=None):
    """entry_ok[i]: a position may be OPENED at bar i's open.
    flat_bar[i]: an open position must be closed at bar i's close."""
    sm = np.asarray(bars.sm).astype(np.int64)
    sday = np.asarray(bars.sday)
    seg = np.asarray(bars.seg)
    n = len(sm)
    trad = np.ones(n, dtype=bool) if tradable is None else np.asarray(tradable, dtype=bool)
    same_prev = np.zeros(n, dtype=bool)
    if n > 1:
        same_prev[1:] = (sday[1:] == sday[:-1]) & (seg[1:] == seg[:-1])
    entry_ok = trad & same_prev & (sm >= window.entry_start) & (sm < window.entry_end) & (sm < window.flat_at)
    flat = np.zeros(n, dtype=bool)
    if n:
        flat[-1] = True
    if n > 1:
        flat[:-1] = (sday[1:] != sday[:-1]) | (seg[1:] != seg[:-1]) | (sm[1:] >= window.flat_at)
    flat |= sm >= window.flat_at
    return entry_ok, flat


def candidates(entry_ok, sig_long, sig_short) -> np.ndarray:
    any_sig = np.asarray(sig_long) | np.asarray(sig_short)
    return (np.nonzero(np.asarray(entry_ok)[1:] & any_sig[:-1])[0] + 1).astype(np.int64)


def get_window(sessions_cfg: dict, name: str) -> Window:
    return load_windows(sessions_cfg)[name]


def run_signals(bars, sig_long, sig_short, window: Window, direction: str = "both", hold="eod",
                stop_dist=None, tgt_dist=None, exit_on_opposite: bool = False,
                policy: ExecutionPolicy = ExecutionPolicy(), tick: float = 0.25, tradable=None) -> Trades:
    """Simulate one contract through the kernel. stop_dist / tgt_dist: points, per signal bar."""
    n = bars.n
    for name, a in (("sig_long", sig_long), ("sig_short", sig_short)):
        if len(a) != n:
            raise ValueError(f"{name} length {len(a)} != bars {n}")
    entry_ok, flat = window_arrays(bars, window, tradable)
    h = -1 if hold == "eod" else int(hold)
    return run_backtest(bars.o, bars.h, bars.l, bars.c, bars.tmin, entry_ok, flat, sig_long, sig_short,
                        direction, h, 1 if stop_dist is not None else 0,
                        None if stop_dist is None else np.broadcast_to(np.asarray(stop_dist, float), (n,)),
                        1 if tgt_dist is not None else 0,
                        None if tgt_dist is None else np.broadcast_to(np.asarray(tgt_dist, float), (n,)),
                        exit_on_opposite, policy.ambiguity, policy.target_trade_through_ticks * tick)
