"""Sparse, shared-bar management evaluator for the frozen V5.4 grammar.

The kernel scans only bars after eligible signal events. Stops are active from
the entry bar. A bar that touches both a stop and any favorable order takes the
stop first. Break-even and trailing changes are calculated after a completed
bar and become active on the next bar. Partials always close one of two integer
MNQ contracts; no fractional contract is booked.
"""
from __future__ import annotations

import numpy as np
from numba import njit
from functools import lru_cache

from quantlab5.v54.universe import managements


@njit(cache=True)
def _sparse(o, h, l, c, tmin, sm, flat, entry, side, risk, years, mechanism_state,
            target_r, be_r, partial_r, trail_r, hold,
            mechanism_exit, baseline_cost_points, stress_cost_points, shadow, capture):
    capacity = len(entry) if capture else 1
    trades_entry = np.empty(capacity, np.int32)
    trades_exit = np.empty(capacity, np.int32)
    trades_r = np.empty(capacity, np.float64)
    ntrades = 0
    net_sum = 0.0
    stress_sum = 0.0
    matched_excess_sum = 0.0
    wins = 0.0
    losses = 0.0
    equity = 0.0
    highwater = 0.0
    maxdd = 0.0
    active_mask = np.int64(0)
    periods = np.zeros(3, np.float64)
    period_counts = np.zeros(3, np.int64)
    last_exit = -1

    for j in range(len(entry)):
        ei = int(entry[j])
        if ei <= last_exit or ei < 1 or ei >= len(o):
            continue
        s = int(side[j])
        r = risk[j]
        if not np.isfinite(r) or r < .25:
            continue
        ep = o[ei]
        if not np.isfinite(ep):
            continue
        partial = partial_r > 0
        units = 2 if partial else 1
        live = units
        stop_px = ep - s * r
        target_px = ep + s * target_r * r if target_r > 0 else np.nan
        partial_px = ep + s * partial_r * r if partial else np.nan
        trail_on = False
        done_partial = False
        favorable = ep
        sum_points = 0.0
        xi = ei

        for i in range(ei, len(o)):
            xi = i
            if mechanism_exit and i > ei and mechanism_state[i-1] != s:
                sum_points += live * s * (o[i]-ep)
                live = 0
                break
            # A stop gap fills at the worse open. Favorable gaps never improve a
            # resting target or partial limit fill.
            open_stop = (o[i] <= stop_px) if s == 1 else (o[i] >= stop_px)
            stop_hit = (l[i] <= stop_px) if s == 1 else (h[i] >= stop_px)
            if i > ei and open_stop:
                sum_points += live * s * (o[i]-ep)
                live = 0
                break
            if i > ei and target_r > 0:
                open_target = (o[i] >= target_px+.25) if s == 1 else (o[i] <= target_px-.25)
                if open_target:
                    if partial and not done_partial:
                        sum_points += s * (partial_px-ep)
                        live -= 1
                        done_partial = True
                    sum_points += live * s * (target_px-ep)
                    live = 0
                    break
            if i > ei and partial and not done_partial:
                open_partial = (o[i] >= partial_px+.25) if s == 1 else (o[i] <= partial_px-.25)
                if open_partial:
                    sum_points += s * (partial_px-ep)
                    live -= 1
                    done_partial = True
            if stop_hit:
                sum_points += live * s * (stop_px-ep)
                live = 0
                break
            target_hit = False
            if target_r > 0:
                # One tick of trade-through for a target limit order.
                target_hit = (h[i] >= target_px+.25) if s == 1 else (l[i] <= target_px-.25)
            if partial and not done_partial:
                part_hit = (h[i] >= partial_px+.25) if s == 1 else (l[i] <= partial_px-.25)
                if part_hit:
                    sum_points += s * (partial_px-ep)
                    live -= 1
                    done_partial = True
            if target_hit:
                sum_points += live * s * (target_px-ep)
                live = 0
                break
            scheduled = hold > 0 and tmin[i]-tmin[ei] >= hold-1
            if flat[i] or scheduled or i == len(o)-1:
                sum_points += live * s * (c[i]-ep)
                live = 0
                break
            # Update resting protective orders from the completed bar for i+1.
            bar_favorable = h[i] if s == 1 else l[i]
            if (s == 1 and bar_favorable > favorable) or (s == -1 and bar_favorable < favorable):
                favorable = bar_favorable
            progress = s * (favorable-ep) / r
            if be_r > 0 and progress >= be_r:
                if s == 1:
                    stop_px = max(stop_px, ep)
                else:
                    stop_px = min(stop_px, ep)
            if trail_r > 0 and progress >= trail_r:
                trail_on = True
            if trail_on:
                trailing = favorable-s*trail_r*r
                if s == 1:
                    stop_px = max(stop_px, trailing)
                else:
                    stop_px = min(stop_px, trailing)

        if live != 0:
            raise AssertionError("unclosed V5.4 position")
        last_exit = xi
        net_r = (sum_points/units - baseline_cost_points)/r
        stress_r = (sum_points/units - stress_cost_points)/r
        net_sum += net_r
        stress_sum += stress_r
        clock = int(sm[ei-1])
        if 0 <= clock < 1440:
            matched_excess_sum += net_r - shadow[0 if s == 1 else 1, clock]
        if net_r > 0:
            wins += net_r
        elif net_r < 0:
            losses -= net_r
        equity += net_r
        if equity > highwater:
            highwater = equity
        maxdd = max(maxdd, highwater-equity)
        year = int(years[ei])
        if 2000 <= year < 2060:
            active_mask |= np.int64(1) << np.int64(year-2000)
        p = 0 if year <= 2012 else (1 if year <= 2015 else 2)
        periods[p] += net_r
        period_counts[p] += 1
        if capture:
            trades_entry[ntrades] = ei
            trades_exit[ntrades] = xi
            trades_r[ntrades] = net_r
        ntrades += 1
    active_years = 0
    while active_mask:
        active_years += int(active_mask & 1)
        active_mask >>= 1
    metrics = np.array((float(ntrades), net_sum, stress_sum,
                        net_sum/ntrades if ntrades else 0.0,
                        wins/losses if losses > 0 else np.nan,
                        maxdd, float(active_years),
                        periods[0], periods[1], periods[2],
                        float(period_counts[0]), float(period_counts[1]), float(period_counts[2]),
                        matched_excess_sum/ntrades if ntrades else 0.0))
    return metrics, trades_entry[:ntrades] if capture else trades_entry[:0], \
        trades_exit[:ntrades] if capture else trades_exit[:0], \
        trades_r[:ntrades] if capture else trades_r[:0]


def evaluate(market, events, management: dict, *, baseline_cost_points: float,
             stress_cost_points: float, shadow_baseline=None,
             capture: bool = False):
    """Return compact metrics; rerun with capture=True for exact trade details."""
    if tuple(sorted(management.items())) not in _management_keys():
        raise ValueError("management is outside frozen V5.4 grammar")
    b = market.nq
    hold = management["hold"] if management["hold"] != "eod" else -1
    state = events.mechanism_state
    if state is None:
        state = np.zeros(b.n, np.int8)
    if management["mechanism_exit"] and len(state) != b.n:
        raise ValueError("mechanism exit requires a full aligned state array")
    years = events.years if events.years is not None else market.years()
    shadow = np.zeros((2, 1440), float) if shadow_baseline is None else np.asarray(shadow_baseline, float)
    return _sparse(np.asarray(b.o, float), np.asarray(b.h, float),
                   np.asarray(b.l, float), np.asarray(b.c, float),
                   np.asarray(b.tmin, np.int64),
                   np.asarray(b.sm, np.int16),
                   np.asarray(events.flat_bar, bool), events.entry_idx,
                   events.side, events.stop_dist,
                   np.asarray(years, np.int32), np.asarray(state, np.int8),
                   float(management["target_r"] or 0),
                   float(management["breakeven_r"] or 0),
                   float(management["partial_r"] or 0),
                   float(management["trail_r"] or 0), int(hold),
                   bool(management["mechanism_exit"]),
                   float(baseline_cost_points), float(stress_cost_points), shadow, capture)


@lru_cache(maxsize=1)
def _management_keys():
    return frozenset(tuple(sorted(x.as_dict().items())) for x in managements())
