"""Candidate-level analysis: reconstruct trades of any candidate, daily P&L, clustering, neighbourhood
robustness, representatives. (Ported unchanged from QuantLabV4 quantlab4/v4/analysis.py, where it implemented
the V4 preregistration clustering/robustness sections. V5 rule: clustering may only ANNOTATE duplicates;
it must never remove a qualifying candidate -- enforced on freeze contents by the stage gate.)

A candidate address:
  ("RULE", ti, ci, vi, ei)   trigger index, filter-combo index, variant index, exit index
  ("SYM", set_name, code, side_idx, sym_exit_idx)
  ("ML", ml_index, ei)
"""
from __future__ import annotations

import numpy as np
from numba import njit

from quantlab5.search.reference_grammar import SYM_EXITS, combo_masks, filter_combos

VAR_DIR = {0: (1, None), 1: (-1, None), 2: (1, 1), 3: (1, -1), 4: (-1, -1), 5: (-1, 1)}   # (mult, required sign)


@njit(cache=True)
def _greedy_trades(sel, dsel, dec_bar, pnl_e, xbar_e, cost):
    n = len(sel)
    take = np.zeros(n, np.bool_)
    net = np.zeros(n)
    last = -1
    for j in range(n):
        p = sel[j]
        t = dec_bar[p]
        if t < last:
            continue
        g = pnl_e[p, dsel[j]]
        if g != g:
            continue
        take[j] = True
        net[j] = g - cost
        last = xbar_e[p, dsel[j]]
    return take, net


def events_for(addr, W, ml_events=None):
    """(positions, direction index 0=long/1=short) of the candidate's candidate events, in time order."""
    kind = addr[0]
    if kind == "RULE":
        _, ti, ci, vi, ei = addr
        t = W.triggers[ti]
        combos = filter_combos(W.filters)
        cm = combo_masks(combos)[ci]
        mult, req = VAR_DIR[vi]
        sgn = t.sign.astype(np.int64)
        ok = np.ones(len(sgn), bool) if req is None else (sgn == req)
        d = sgn * mult
        bl = (W.bits_long[t.pos] & cm) == cm
        bs = (W.bits_short[t.pos] & cm) == cm
        ok &= np.where(d == 1, bl, bs)
        return t.pos[ok].astype(np.int64), np.where(d[ok] == 1, 0, 1).astype(np.int64), ei
    if kind == "SYM":
        _, name, code, side, sei = addr
        pos = np.nonzero(W.sym[name] == code)[0].astype(np.int64)
        return pos, np.full(len(pos), side, np.int64), SYM_EXITS[sei]
    if kind == "ML":
        _, mi, ei = addr
        _ss, pos, sg = ml_events[mi]
        return pos.astype(np.int64), np.where(sg == 1, 0, 1).astype(np.int64), ei
    raise ValueError(kind)


def trades(addr, m, W, pnl, xbar, cost, ml_events=None):
    """Trades of a candidate: net points (baseline cost), risk = frozen stop distance (points), MAE (points)."""
    from quantlab5.engine.outcomes import EXITS, stop_distances
    pos, d, ei = events_for(addr, W, ml_events)
    take, net = _greedy_trades(pos, d, m.dec.astype(np.int64), pnl[ei], xbar[ei], cost)
    p = pos[take]
    dd = d[take]
    entry = m.dec[p] + 1
    exit_bar = xbar[ei][p, dd]
    risk = stop_distances(W.stop_scale, m.dec, EXITS[ei]["stop_mult"])[p]
    mae = _mae(np.asarray(m.nq.o), np.asarray(m.nq.h), np.asarray(m.nq.l), entry.astype(np.int64),
               exit_bar.astype(np.int64), np.where(dd == 0, 1, -1).astype(np.int64))
    return {"pos": p, "dir": dd, "net": net[take], "bar": m.dec[p], "entry_bar": entry, "exit_bar": exit_bar,
            "sday": np.asarray(m.nq.sday)[m.dec[p]], "risk": risk, "mae": np.minimum(mae, risk),
            "ts_entry": np.asarray(m.nq.ts)[entry], "ts_exit": np.asarray(m.nq.ts)[exit_bar]}


@njit(cache=True)
def _mae(o, h, l, entry, exit_bar, dirn):
    """Worst adverse excursion (points, >= 0) from the entry price over bars entry..exit (bounded later by the stop)."""
    out = np.zeros(len(entry))
    for k in range(len(entry)):
        ep = o[entry[k]]
        w = 0.0
        for i in range(entry[k], exit_bar[k] + 1):
            adv = (ep - l[i]) if dirn[k] == 1 else (h[i] - ep)
            if adv > w:
                w = adv
        out[k] = w
    return out


def daily_pnl(tr, days):
    """Net P&L per session aligned to `days` (sorted session-day ints); sessions without trades = 0."""
    out = np.zeros(len(days))
    idx = np.searchsorted(days, tr["sday"])
    np.add.at(out, idx, tr["net"])
    return out


def cluster(order_ids, streams, threshold=0.60):
    """Greedy clustering in the given order (descending t). Returns {rep_id: [member ids]} (first = seed)."""
    reps, clusters = [], {}
    for cid in order_ids:
        x = streams[cid]
        placed = False
        if x.std() > 0:
            for r in reps:
                y = streams[r]
                if y.std() > 0 and np.corrcoef(x, y)[0, 1] >= threshold:
                    clusters[r].append(cid)
                    placed = True
                    break
        if not placed:
            reps.append(cid)
            clusters[cid] = [cid]
    return clusters


def rule_neighbours(addr, W):
    """Neighbours per preregistration: adjacent trigger parameter (same trigger name/family), adjacent exit
    (same stop, adjacent hold rule; or same hold rule, other stop), or one filter removed."""
    _, ti, ci, vi, ei = addr
    out = []
    t = W.triggers[ti]
    name = t.params.get("name")
    base = {k: v for k, v in t.params.items() if k != "name"}
    for tj, u in enumerate(W.triggers):
        if tj == ti or u.family != t.family or u.params.get("name") != name:
            continue
        pu = {k: v for k, v in u.params.items() if k != "name"}
        if set(pu) != set(base):
            continue
        diff = [k for k in base if pu[k] != base[k]]
        if len(diff) == 1 and all(isinstance(x, (int, float)) and not isinstance(x, bool)
                                  for x in (base[diff[0]], pu[diff[0]])):
            # only NUMERIC parameters have an order ("adjacent value"); categorical ones have no neighbours
            vals = sorted({x.params[diff[0]] for x in W.triggers if x.params.get("name") == name
                           and all(x.params.get(k) == base[k] for k in base if k != diff[0])
                           and isinstance(x.params[diff[0]], (int, float))}, key=float)
            a, b = vals.index(base[diff[0]]), vals.index(pu[diff[0]])
            if abs(a - b) == 1:
                out.append(("RULE", tj, ci, vi, ei))
    hold_seq = 7                                     # per stop: T15,T30,T60,T120,EOD,R2,R3
    stop_i, h = divmod(ei, hold_seq)
    for hh in (h - 1, h + 1):
        if 0 <= hh < 5 and h < 5:
            out.append(("RULE", ti, ci, vi, stop_i * hold_seq + hh))
    if h == 5:
        out.append(("RULE", ti, ci, vi, stop_i * hold_seq + 6))
    if h == 6:
        out.append(("RULE", ti, ci, vi, stop_i * hold_seq + 5))
    out.append(("RULE", ti, ci, vi, (1 - stop_i) * hold_seq + h))
    combos = filter_combos(W.filters)
    cb = combos[ci]
    if len(cb) >= 1:
        for drop in cb:
            rest = tuple(b for b in cb if b != drop)
            out.append(("RULE", ti, combos.index(rest), vi, ei))
    return out


def drift_baseline(m, pnl, cost, ei_of_trades, tr, period_mask_dec=None):
    """POST-HOC control (not part of any selection rule). For each trade: the mean NET outcome of the same exit
    and direction entered at the SAME session minute on every session of the period (unconditional entry).
    Captures long-run drift and time-of-day directional bias. Excess = trade net - baseline."""
    sm = np.asarray(m.nq.sm)[m.dec].astype(np.int64)
    ok = np.ones(len(m.dec), bool) if period_mask_dec is None else np.asarray(period_mask_dec, bool)
    base = np.full(len(tr["net"]), np.nan)
    table = {}
    for k in range(len(tr["net"])):
        key = (int(sm[tr["pos"][k]]), int(tr["dir"][k]), int(ei_of_trades))
        if key not in table:
            sel = ok & (sm == key[0])
            x = pnl[key[2]][sel, key[1]]
            x = x[np.isfinite(x)]
            table[key] = float(x.mean() - cost) if len(x) else np.nan
        base[k] = table[key]
    return base
