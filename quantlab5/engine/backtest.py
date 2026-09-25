"""The execution core: one position at a time, conservative fills.

(Copied from quantlab3/engine/backtest.py -- V3's reference kernel. V4 change: the
V3 engine-v2 target policy is applied here too: a resting target fills only when
the bar trades `tgt_through` points BEYOND it (a touch is not a fill); default
1 tick via config/execution.yaml. With tgt_through=0 the kernel is byte-identical
in behaviour to V3's reference kernel.)

Timing contract (bar t = the 1-minute bar starting at t):

  * A signal array value sig[t] means "the condition was true at the CLOSE of
    bar t". The earliest fill is the OPEN of bar t+1, and only if bar t+1 is
    in the same session and contract and inside the entry window.
  * Stops/targets are checked from the entry bar onward using each bar's
    high/low. The entry bar counts: it starts at the entry price.
  * If a bar gaps through the stop at its open, the fill is the OPEN (worse).
    If a bar gaps through the target, the fill is the TARGET (never better).
  * If stop and target are BOTH touched inside one bar and the open does not
    decide it, the order is unknowable. Baseline policy 'pessimistic' books the
    stop. The number of such bars is recorded on every trade.
  * Time exits are pre-scheduled and fill at the close of the last bar of the
    holding period (a market order at the scheduled time).
  * Every position is flattened at the close of the last bar before the
    window's flat time, at a session/contract change, or at the end of data.
  * 'Opposite signal' exits fill at the next bar's open, like any signal.

No pyramiding, no averaging, no reversal inside a bar. Sizing is one contract.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numba import njit

REASONS = {1: "stop", 2: "target", 3: "time", 4: "session_end", 5: "opposite_signal"}

DIR_CODE = {"long": 1, "short": 2, "both": 3}


@njit(cache=True)
def _backtest(o, h, l, c, tmin, entry_ok, flat_bar, sig_long, sig_short, dir_mode, hold,
              stop_mode, stop_arr, tgt_mode, tgt_arr, exit_opp, pessimistic, cap, tgt_through):
    n = len(o)
    e_idx = np.empty(cap, np.int64)
    x_idx = np.empty(cap, np.int64)
    side = np.empty(cap, np.int8)
    e_px = np.empty(cap, np.float64)
    x_px = np.empty(cap, np.float64)
    reason = np.empty(cap, np.int8)
    amb = np.zeros(cap, np.bool_)
    mae = np.empty(cap, np.float64)
    mfe = np.empty(cap, np.float64)
    k = 0

    pos = 0
    ei = 0
    ep = 0.0
    emin = 0
    sp = np.nan
    tp = np.nan
    cur_mae = 0.0
    cur_mfe = 0.0
    pend_exit = False

    for i in range(1, n):
        # ---- 1. pending opposite-signal exit fills at this bar's open ----------
        if pos != 0 and pend_exit:
            e_idx[k] = ei; x_idx[k] = i; side[k] = pos; e_px[k] = ep; x_px[k] = o[i]
            reason[k] = 5
            fav = pos * (o[i] - ep)
            mae[k] = max(cur_mae, -fav)
            mfe[k] = max(cur_mfe, fav)
            k += 1
            pos = 0
            pend_exit = False

        # ---- 2. entry at this bar's open from the PREVIOUS bar's signal --------
        if pos == 0 and entry_ok[i] and k < cap:
            want = 0
            lg = sig_long[i - 1] and (dir_mode & 1) != 0
            sh = sig_short[i - 1] and (dir_mode & 2) != 0
            if lg and not sh:
                want = 1
            elif sh and not lg:
                want = -1
            if want != 0:
                px = o[i]
                ok = True
                sp = np.nan
                tp = np.nan
                if stop_mode == 1:
                    d = stop_arr[i - 1]
                    if not (d > 0.0):
                        ok = False
                    else:
                        sp = px - want * d
                elif stop_mode == 2:
                    sp = stop_arr[i - 1]
                    if not (want * (px - sp) > 0.0):
                        ok = False
                if tgt_mode == 1:
                    d = tgt_arr[i - 1]
                    if not (d > 0.0):
                        ok = False
                    else:
                        tp = px + want * d
                elif tgt_mode == 2:
                    tp = tgt_arr[i - 1]
                    if not (want * (tp - px) > 0.0):
                        ok = False
                if ok:
                    pos = want
                    ei = i
                    ep = px
                    emin = tmin[i]
                    cur_mae = 0.0
                    cur_mfe = 0.0

        if pos == 0:
            continue

        # ---- 3. intrabar stop / target -----------------------------------------
        has_s = not np.isnan(sp)
        has_t = not np.isnan(tp)
        s_hit = False
        t_hit = False
        if has_s:
            s_hit = (l[i] <= sp) if pos == 1 else (h[i] >= sp)
        if has_t:
            t_hit = (h[i] >= tp + tgt_through) if pos == 1 else (l[i] <= tp - tgt_through)
        if s_hit or t_hit:
            fill = 0.0
            rcode = 0
            ambiguous = False
            gap_s = has_s and i > ei and ((o[i] <= sp) if pos == 1 else (o[i] >= sp))
            gap_t = has_t and i > ei and ((o[i] >= tp + tgt_through) if pos == 1 else (o[i] <= tp - tgt_through))
            if gap_s:
                fill = o[i]
                rcode = 1
            elif gap_t:
                fill = tp
                rcode = 2
            elif s_hit and t_hit:
                ambiguous = True
                if pessimistic:
                    fill = sp
                    rcode = 1
                else:
                    fill = tp
                    rcode = 2
            elif s_hit:
                fill = sp
                rcode = 1
            else:
                fill = tp
                rcode = 2
            e_idx[k] = ei; x_idx[k] = i; side[k] = pos; e_px[k] = ep; x_px[k] = fill
            reason[k] = rcode
            amb[k] = ambiguous
            fav = pos * (fill - ep)
            # excursion inside the exit bar is bounded by the fill itself
            mae[k] = max(cur_mae, -fav)
            mfe[k] = max(cur_mfe, fav)
            k += 1
            pos = 0
            pend_exit = False
            continue

        # whole bar held: update excursions
        if pos == 1:
            adv = ep - l[i]
            fv = h[i] - ep
        else:
            adv = h[i] - ep
            fv = ep - l[i]
        if adv > cur_mae:
            cur_mae = adv
        if fv > cur_mfe:
            cur_mfe = fv

        # ---- 4. at the close: time exit, session flat, opposite signal ----------
        rcode = 0
        if hold > 0 and tmin[i] - emin >= hold - 1:
            rcode = 3
        elif flat_bar[i]:
            rcode = 4
        if rcode != 0:
            e_idx[k] = ei; x_idx[k] = i; side[k] = pos; e_px[k] = ep; x_px[k] = c[i]
            reason[k] = rcode
            mae[k] = cur_mae
            mfe[k] = cur_mfe
            k += 1
            pos = 0
            pend_exit = False
            continue
        if exit_opp:
            if (pos == 1 and sig_short[i]) or (pos == -1 and sig_long[i]):
                pend_exit = True

    return (e_idx[:k], x_idx[:k], side[:k], e_px[:k], x_px[:k], reason[:k], amb[:k],
            mae[:k], mfe[:k])


@dataclass
class Trades:
    entry_idx: np.ndarray
    exit_idx: np.ndarray
    side: np.ndarray        # +1 long, -1 short
    entry_px: np.ndarray
    exit_px: np.ndarray
    reason: np.ndarray
    ambiguous: np.ndarray
    mae: np.ndarray         # points, >= 0
    mfe: np.ndarray         # points, >= 0
    initial_risk: np.ndarray | None = None   # points, only when a stop is defined

    @property
    def n(self) -> int:
        return len(self.entry_idx)

    @property
    def points(self) -> np.ndarray:
        return self.side.astype(np.float64) * (self.exit_px - self.entry_px)


_EMPTY = np.empty(1, np.float64)


def run_backtest(o, h, l, c, tmin, entry_ok, flat_bar, sig_long, sig_short, direction: str,
                 hold: int = -1, stop_mode: int = 0, stop_arr=None, tgt_mode: int = 0, tgt_arr=None,
                 exit_on_opposite: bool = False, ambiguity: str = "pessimistic",
                 tgt_through: float = 0.0) -> Trades:
    """Thin, typed wrapper around the Numba core."""
    sig_long = np.ascontiguousarray(sig_long, dtype=np.bool_)
    sig_short = np.ascontiguousarray(sig_short, dtype=np.bool_)
    cap = int(np.count_nonzero(sig_long | sig_short)) + 1
    sa = np.ascontiguousarray(stop_arr, dtype=np.float64) if stop_mode else _EMPTY
    ta = np.ascontiguousarray(tgt_arr, dtype=np.float64) if tgt_mode else _EMPTY
    out = _backtest(np.asarray(o, np.float64), np.asarray(h, np.float64), np.asarray(l, np.float64),
                    np.asarray(c, np.float64), np.asarray(tmin, np.int64),
                    np.asarray(entry_ok, np.bool_), np.asarray(flat_bar, np.bool_),
                    sig_long, sig_short, DIR_CODE[direction], int(hold),
                    int(stop_mode), sa, int(tgt_mode), ta, bool(exit_on_opposite),
                    ambiguity == "pessimistic", cap, float(tgt_through))
    tr = Trades(*out)
    if stop_mode:
        tr.initial_risk = np.abs(tr.entry_px - _stop_levels(tr, stop_mode, sa))
    return tr


def _stop_levels(tr: Trades, stop_mode: int, stop_arr: np.ndarray) -> np.ndarray:
    sig_i = tr.entry_idx - 1
    if stop_mode == 1:
        return tr.entry_px - tr.side * stop_arr[sig_i]
    return stop_arr[sig_i]
