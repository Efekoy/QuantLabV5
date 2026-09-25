"""Regression tests for the 2026-09-24 performance optimisations: every optimised routine must reproduce its
reference implementation EXACTLY (bit-identical arrays)."""
from datetime import date

import numpy as np
import pytest

from quantlab5.search import kernel as K
from quantlab5.features import ops as O


def _brute_ext(x, n, gid, mx):
    gs = O.group_start(gid)
    out = np.full(len(x), np.nan)
    for i in range(len(x)):
        lo = i - n + 1
        if lo < gs[i]:
            continue
        w = x[lo:i + 1]
        w = w[np.isfinite(w)]
        if len(w):
            out[i] = w.max() if mx else w.min()
    return out


@pytest.mark.parametrize("n", [1, 2, 5, 30, 120])
def test_deque_rolling_extrema_equal_brute_force(n):
    rng = np.random.default_rng(n)
    x = np.round(rng.standard_normal(6000), 1)
    x[rng.random(6000) < 0.15] = np.nan
    gid = np.cumsum(rng.random(6000) < 0.02)
    assert np.array_equal(O.rmax(x, n, gid), _brute_ext(x, n, gid, True), equal_nan=True)
    assert np.array_equal(O.rmin(x, n, gid), _brute_ext(x, n, gid, False), equal_nan=True)


def test_lag_and_memoised_group_start_equal_reference():
    rng = np.random.default_rng(3)
    gid = np.cumsum(rng.random(5000) < 0.03)
    x = rng.standard_normal(5000)
    for n in (1, 3, 17, 200):
        ref = np.full(5000, np.nan)
        ok = gid[n:] == gid[:-n]
        ref[n:] = np.where(ok, x[:-n], np.nan)
        assert np.array_equal(O.lag(x, n, gid), ref, equal_nan=True)
    first = np.r_[True, gid[1:] != gid[:-1]]
    ref_gs = np.maximum.accumulate(np.where(first, np.arange(5000), 0))
    assert np.array_equal(O.group_start(gid), ref_gs) and O.group_start(gid) is O.group_start(gid)
    gid2 = gid.copy()
    assert np.array_equal(O.group_start(gid2), ref_gs)          # different object: recomputed, same values


@pytest.fixture(scope="module")
def world():
    from quantlab5.features.library import compute_world
    from quantlab5.engine.outcomes import compute_outcomes
    from quantlab5.synthetic.market_builders import synthetic_market
    m = synthetic_market(date(2012, 1, 2), date(2012, 6, 29), seed=11)
    W = compute_world(m)
    pnl, xbar = compute_outcomes(m, W.stop_scale)
    return m, W, pnl, xbar


def test_optimised_rule_kernel_equals_reference(world):
    from quantlab5.search.reference_grammar import combo_masks, filter_combos
    m, W, pnl, xbar = world
    combos = filter_combos(W.filters)
    cm = combo_masks(combos)
    y = (np.arange(len(m.dec)) % 9).astype(np.int64)
    for tr in sorted(W.triggers, key=lambda t: -len(t.pos))[:10] + W.triggers[::40]:
        a = np.zeros((len(cm), 6, 14, K.NSTAT))
        b = np.zeros_like(a)
        args = (tr.pos.astype(np.int64), tr.sign.astype(np.int64), W.bits_long, W.bits_short, m.dec.astype(np.int64),
                y, cm, cm, pnl, xbar, 0.7)
        K.eval_trigger_v1(*args, a)
        K.eval_trigger(*args, b, combos=combos)
        assert np.array_equal(a, b), tr.tid


def test_optimised_symbol_kernel_equals_reference(world):
    m, W, pnl, xbar = world
    codes = W.sym["A9_L3"]
    pos = np.nonzero(codes >= 0)[0]
    cv = codes[pos]
    o = np.lexsort((pos, cv))
    pos, cv = pos[o], cv[o]
    u, st = np.unique(cv, return_index=True)
    st = np.r_[st, len(cv)].astype(np.int64)
    ex = np.array([0, 1, 2, 4], np.int64)
    y = np.zeros(len(m.dec), np.int64)
    a = np.zeros((len(u), 2, 4, K.NSTAT))
    b = np.zeros_like(a)
    K.eval_codes_v1(pos.astype(np.int64), st, m.dec.astype(np.int64), y, pnl, xbar, ex, 0.7, a)
    K.eval_codes(pos.astype(np.int64), st, m.dec.astype(np.int64), y, pnl, xbar, ex, 0.7, b)
    assert np.array_equal(a, b)


def test_galloping_greedy_on_dense_and_sparse_events():
    """Adversarial: exits that skip 0, 1, many and all later events."""
    rng = np.random.default_rng(5)
    n = 3000
    dec_bar = np.cumsum(rng.integers(1, 4, n)).astype(np.int64)
    pnl = rng.standard_normal((n, 2)).astype(np.float32)
    pnl[rng.random((n, 2)) < 0.05] = np.nan
    xbar = (dec_bar[:, None] + rng.choice([1, 2, 50, 400, 10 ** 6], size=(n, 2))).astype(np.int32)
    sel = np.sort(rng.choice(n, 1500, replace=False)).astype(np.int64)
    dsel = rng.integers(0, 2, len(sel)).astype(np.int64)
    y = np.zeros(n, np.int64)
    a = np.zeros(K.NSTAT)
    b = np.zeros(K.NSTAT)
    K._greedy(sel, len(sel), dec_bar, y, pnl, xbar, dsel, 0.7, a)
    K._greedy_fast(dec_bar[sel], sel, len(sel), y, pnl, xbar, dsel, 0.7, b)
    assert np.array_equal(a, b)
