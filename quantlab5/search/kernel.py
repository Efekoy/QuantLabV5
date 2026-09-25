"""Search kernels (numba). They turn precomputed outcomes + events + filter bits into per-candidate stats.

Direction variants (per trigger event of sign s):
  0 cont_both  trade s            1 rev_both  trade -s
  2 cont_long  trade s, only s=+1  3 cont_short trade s, only s=-1
  4 rev_long   trade -s, only s=-1 5 rev_short trade -s, only s=+1
Stats layout per candidate (float64): see STAT_NAMES. Net P&L per trade = gross points - cost points.
"""
from __future__ import annotations

import numpy as np
from numba import njit, prange

VARIANTS = ("cont_both", "rev_both", "cont_long", "cont_short", "rev_long", "rev_short")
N_YEARS = 9                      # DISCOVERY 2010..2018; year index = year - first_year (clipped)
STAT_NAMES = (["n", "sum", "sumsq", "wins", "sumpos", "sumneg", "maxdd"]
              + [f"ysum{k}" for k in range(N_YEARS)] + [f"yn{k}" for k in range(N_YEARS)])
NSTAT = len(STAT_NAMES)


@njit(cache=True)
def _greedy(sel, nsel, dec_bar, yidx, pnl_e, xbar_e, dsel, cost, out):
    """Greedy one-position-at-a-time pass over selected events for one exit. Fills out[:NSTAT]."""
    for k in range(out.shape[0]):
        out[k] = 0.0
    last = -1
    cum = 0.0
    peak = 0.0
    mdd = 0.0
    for j in range(nsel):
        p = sel[j]
        t = dec_bar[p]
        if t < last:
            continue
        di = dsel[j]
        g = pnl_e[p, di]
        if g != g:
            continue
        x = g - cost
        out[0] += 1.0
        out[1] += x
        out[2] += x * x
        if x > 0:
            out[3] += 1.0
            out[4] += x
        else:
            out[5] += x
        cum += x
        if cum > peak:
            peak = cum
        if peak - cum > mdd:
            mdd = peak - cum
        y = yidx[p]
        out[7 + y] += x
        out[7 + 9 + y] += 1.0
        last = xbar_e[p, di]
    out[6] = mdd


@njit(cache=True)
def _greedy_fast(tsel, sel, nsel, yidx, pnl_e, xbar_e, dsel, cost, out):
    """Same result as _greedy: after a trade exits at bar X, jump (binary search on the strictly increasing
    signal bars tsel) to the first selected event with signal bar >= X instead of scanning the skipped ones.
    Trades taken, their order and all arithmetic are identical."""
    for k in range(out.shape[0]):
        out[k] = 0.0
    cum = 0.0
    peak = 0.0
    mdd = 0.0
    j = 0
    while j < nsel:
        p = sel[j]
        di = dsel[j]
        g = pnl_e[p, di]
        if g != g:
            j += 1
            continue
        x = g - cost
        out[0] += 1.0
        out[1] += x
        out[2] += x * x
        if x > 0:
            out[3] += 1.0
            out[4] += x
        else:
            out[5] += x
        cum += x
        if cum > peak:
            peak = cum
        if peak - cum > mdd:
            mdd = peak - cum
        y = yidx[p]
        out[7 + y] += x
        out[7 + 9 + y] += 1.0
        last = xbar_e[p, di]
        # galloping search for the first index > j with tsel >= last: O(1) when the next event is already
        # after the exit (sparse triggers), O(log skip) when many events are skipped (dense triggers)
        k = j + 1
        if k < nsel and tsel[k] < last:
            step = 1
            lo = k
            hi = k + 1
            while hi < nsel and tsel[hi] < last:
                lo = hi
                step *= 2
                hi = hi + step
            if hi > nsel:
                hi = nsel
            while lo < hi:
                mid = (lo + hi) >> 1
                if tsel[mid] < last:
                    lo = mid + 1
                else:
                    hi = mid
            k = lo
        j = k
    out[6] = mdd


@njit(parallel=True, cache=True)
def eval_trigger_bits(pos, sign, bits_l, bits_s, dec_bar, yidx, cb1, cb2, pnl, xbar, cost, out):
    """Optimised kernel. Filter combination ci = bits (cb1[ci], cb2[ci]) (-1 = unused; the grammar uses the same
    bits for long and short trades, and each event's direction-specific filter state is looked up once).
    Per variant, per-filter event lists (CSR) are built once; a 1-filter combo uses its list, a 2-filter combo
    walks the shorter list and tests the other bit. Event order is preserved, trades and arithmetic identical
    to eval_trigger_v1 (regression-tested). out: [n_combo, 6, n_exit, NSTAT]"""
    ncombo = cb1.shape[0]
    nexit = pnl.shape[0]
    E = len(pos)
    NB = 64
    vcnt = np.zeros(6, np.int64)
    vpos = np.empty((6, E), np.int64)
    vdi = np.empty((6, E), np.int64)
    vbits = np.empty((6, E), np.uint64)
    bstart = np.zeros((6, NB + 1), np.int64)
    bidx = np.empty((6, E * 40 + 1), np.int64)
    for v in range(6):
        k = 0
        for j in range(E):
            s = sign[j]
            if v == 2 and s != 1:
                continue
            if v == 3 and s != -1:
                continue
            if v == 4 and s != -1:
                continue
            if v == 5 and s != 1:
                continue
            d = s if (v == 0 or v == 2 or v == 3) else -s
            p = pos[j]
            vpos[v, k] = p
            if d == 1:
                vdi[v, k] = 0
                vbits[v, k] = bits_l[p]
            else:
                vdi[v, k] = 1
                vbits[v, k] = bits_s[p]
            k += 1
        vcnt[v] = k
        # CSR lists of event indices per filter bit (increasing k => time order preserved)
        cnt = np.zeros(NB, np.int64)
        for k2 in range(k):
            b = vbits[v, k2]
            for bb in range(NB):
                if (b >> np.uint64(bb)) & np.uint64(1):
                    cnt[bb] += 1
        acc = 0
        for bb in range(NB):
            bstart[v, bb] = acc
            acc += cnt[bb]
        bstart[v, NB] = acc
        if acc > bidx.shape[1]:
            raise ValueError("filter-list buffer too small")
        fill = bstart[v, :NB].copy()
        for k2 in range(k):
            b = vbits[v, k2]
            for bb in range(NB):
                if (b >> np.uint64(bb)) & np.uint64(1):
                    bidx[v, fill[bb]] = k2
                    fill[bb] += 1
    for ci in prange(ncombo):
        sel = np.empty(E, np.int64)
        dsel = np.empty(E, np.int64)
        tsel = np.empty(E, np.int64)
        tmp = np.empty(out.shape[3], np.float64)
        b1 = cb1[ci]
        b2 = cb2[ci]
        for v in range(6):
            nsel = 0
            if b1 < 0:
                for k in range(vcnt[v]):
                    sel[nsel] = vpos[v, k]
                    dsel[nsel] = vdi[v, k]
                    tsel[nsel] = dec_bar[vpos[v, k]]
                    nsel += 1
            else:
                a0, a1 = bstart[v, b1], bstart[v, b1 + 1]
                other = b2
                if b2 >= 0 and (bstart[v, b2 + 1] - bstart[v, b2]) < (a1 - a0):
                    a0, a1 = bstart[v, b2], bstart[v, b2 + 1]
                    other = b1
                om = np.uint64(1) << np.uint64(other if other >= 0 else 0)
                for q in range(a0, a1):
                    k = bidx[v, q]
                    if other >= 0 and (vbits[v, k] & om) == np.uint64(0):
                        continue
                    sel[nsel] = vpos[v, k]
                    dsel[nsel] = vdi[v, k]
                    tsel[nsel] = dec_bar[vpos[v, k]]
                    nsel += 1
            for e in range(nexit):
                _greedy_fast(tsel, sel, nsel, yidx, pnl[e], xbar[e], dsel, cost, tmp)
                for k in range(out.shape[3]):
                    out[ci, v, e, k] = tmp[k]


def combo_bits(combos):
    """(cb1, cb2) arrays for eval_trigger_bits from grammar filter combos (tuples of <= 2 bits)."""
    cb1 = np.full(len(combos), -1, np.int64)
    cb2 = np.full(len(combos), -1, np.int64)
    for i, c in enumerate(combos):
        if len(c) > 2:
            raise ValueError("at most two filters per combo")
        if len(c) >= 1:
            cb1[i] = c[0]
        if len(c) == 2:
            cb2[i] = c[1]
    return cb1, cb2


def eval_trigger(pos, sign, bits_l, bits_s, dec_bar, yidx, cm_l, cm_s, pnl, xbar, cost, out, combos=None):
    """Dispatcher kept for API compatibility: uses the optimised bit-list kernel when the combos are known
    (all production calls), else the reference kernel."""
    if combos is not None and np.array_equal(cm_l, cm_s):
        cb1, cb2 = combo_bits(combos)
        eval_trigger_bits(pos, sign, bits_l, bits_s, dec_bar, yidx, cb1, cb2, pnl, xbar, cost, out)
    else:
        eval_trigger_v1(pos, sign, bits_l, bits_s, dec_bar, yidx, cm_l, cm_s, pnl, xbar, cost, out)


@njit(parallel=True, cache=True)
def eval_trigger_v1(pos, sign, bits_l, bits_s, dec_bar, yidx, cm_l, cm_s, pnl, xbar, cost, out):
    """REFERENCE (pre-optimisation) kernel, kept for regression tests. out: [n_combo, 6, n_exit, NSTAT]"""
    ncombo = cm_l.shape[0]
    nexit = pnl.shape[0]
    E = len(pos)
    for ci in prange(ncombo):
        sel = np.empty(E, np.int64)
        dsel = np.empty(E, np.int64)
        tmp = np.empty(out.shape[3], np.float64)
        for v in range(6):
            nsel = 0
            for j in range(E):
                s = sign[j]
                if v == 2 and s != 1:
                    continue
                if v == 3 and s != -1:
                    continue
                if v == 4 and s != -1:
                    continue
                if v == 5 and s != 1:
                    continue
                d = s if (v == 0 or v == 2 or v == 3) else -s
                p = pos[j]
                if d == 1:
                    if (bits_l[p] & cm_l[ci]) != cm_l[ci]:
                        continue
                    dsel[nsel] = 0
                else:
                    if (bits_s[p] & cm_s[ci]) != cm_s[ci]:
                        continue
                    dsel[nsel] = 1
                sel[nsel] = p
                nsel += 1
            for e in range(nexit):
                _greedy(sel, nsel, dec_bar, yidx, pnl[e], xbar[e], dsel, cost, tmp)
                for k in range(out.shape[3]):
                    out[ci, v, e, k] = tmp[k]


@njit(parallel=True, cache=True)
def eval_codes(code_pos, code_start, dec_bar, yidx, pnl, xbar, exits, cost, out):
    """Symbolic sequences. code_pos: positions sorted by (code, pos); code_start[i]..code_start[i+1]
    delimit code i. out: [n_codes, 2 (long, short), len(exits), NSTAT]."""
    ncode = len(code_start) - 1
    for ci in prange(ncode):
        a, b = code_start[ci], code_start[ci + 1]
        m = b - a
        sel = np.empty(m, np.int64)
        dsel = np.empty(m, np.int64)
        tsel = np.empty(m, np.int64)
        tmp = np.empty(out.shape[3], np.float64)
        for j in range(m):
            sel[j] = code_pos[a + j]
            tsel[j] = dec_bar[sel[j]]
        for di in range(2):
            for j in range(m):
                dsel[j] = di
            for ei in range(len(exits)):
                e = exits[ei]
                _greedy_fast(tsel, sel, m, yidx, pnl[e], xbar[e], dsel, cost, tmp)
                for k in range(out.shape[3]):
                    out[ci, di, ei, k] = tmp[k]


@njit(parallel=True, cache=True)
def eval_codes_v1(code_pos, code_start, dec_bar, yidx, pnl, xbar, exits, cost, out):
    """Symbolic sequences. code_pos: positions sorted by (code, pos); code_start[i]..code_start[i+1]
    delimit code i. out: [n_codes, 2 (long, short), len(exits), NSTAT]."""
    ncode = len(code_start) - 1
    for ci in prange(ncode):
        a, b = code_start[ci], code_start[ci + 1]
        m = b - a
        sel = np.empty(m, np.int64)
        dsel = np.empty(m, np.int64)
        tmp = np.empty(out.shape[3], np.float64)
        for j in range(m):
            sel[j] = code_pos[a + j]
        for di in range(2):
            for j in range(m):
                dsel[j] = di
            for ei in range(len(exits)):
                e = exits[ei]
                _greedy(sel, m, dec_bar, yidx, pnl[e], xbar[e], dsel, cost, tmp)
                for k in range(out.shape[3]):
                    out[ci, di, ei, k] = tmp[k]


def stats_to_metrics(st: np.ndarray) -> dict:
    """Vectorised metrics from stat arrays [..., NSTAT] (net points)."""
    n = st[..., 0]
    s = st[..., 1]
    ss = st[..., 2]
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = s / n
        var = (ss - s * s / n) / (n - 1)
        t = mean / np.sqrt(var) * np.sqrt(n)
        pf = st[..., 4] / -st[..., 5]
    ys = st[..., 7:7 + N_YEARS]
    yn = st[..., 7 + N_YEARS:7 + 2 * N_YEARS]
    years_pos = ((ys > 0) & (yn > 0)).sum(-1)
    years_active = (yn > 0).sum(-1)
    first_half = ys[..., :5].sum(-1)
    second_half = ys[..., 5:].sum(-1)
    return {"n": n, "mean": mean, "t": np.where(np.isfinite(t), t, np.nan), "pf": pf, "sum": s,
            "wins": st[..., 3], "maxdd": st[..., 6], "years_pos": years_pos, "years_active": years_active,
            "h1": first_half, "h2": second_half}
