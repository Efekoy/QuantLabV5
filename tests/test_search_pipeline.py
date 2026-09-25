"""V4 research pipeline: causality of every feature/trigger/filter/symbol, and exact equivalence of the
fast outcome tables + search kernel with the reference engine (engine.backtest.run_backtest)."""
from datetime import date

import numpy as np
import pytest

from quantlab5.diagnostics.lookahead import mutate_after
from quantlab5.engine.execution import ExecutionPolicy, get_window, run_signals
from quantlab5.search import kernel as K
from quantlab5.features.library import compute_world
from quantlab5.data.market import build_market
from quantlab5.engine.outcomes import EXITS, compute_outcomes, stop_distances
from quantlab5.synthetic.market_builders import synthetic_market


@pytest.fixture(scope="module")
def mk():
    return synthetic_market(date(2012, 1, 2), date(2012, 3, 30), seed=3)


@pytest.fixture(scope="module")
def world(mk):
    return compute_world(mk)


def _mutated(m, k, seed):
    nq2 = mutate_after(m.nq, k, seed)
    kes = int(np.searchsorted(m.es.ts, m.nq.ts[k]))
    es2 = mutate_after(m.es, kes, seed + 99)
    return build_market(nq2, es2, m.nq_symbols, m.es_symbols)


def _eq(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.dtype.kind == "f":
        return np.array_equal(a, b, equal_nan=True)
    return np.array_equal(a, b)


@pytest.mark.parametrize("frac", [0.45, 0.8])
def test_every_feature_trigger_filter_and_symbol_is_causal(mk, world, frac):
    k = int(mk.n * frac)
    W2 = compute_world(_mutated(mk, k, 5))
    dk = int(np.searchsorted(mk.dec, k))          # decision bars strictly before the cut
    bad = [nm for nm, arr in world.F.items() if not _eq(arr[:dk], W2.F[nm][:dk])]
    assert bad == [], f"ML features changed before the cut: {bad}"
    for t1, t2 in zip(world.triggers, W2.triggers):
        assert t1.tid == t2.tid
        m1, m2 = t1.pos < dk, t2.pos < dk
        assert _eq(t1.pos[m1], t2.pos[m2]) and _eq(t1.sign[m1], t2.sign[m2]), t1.tid
    assert _eq(world.bits_long[:dk], W2.bits_long[:dk]) and _eq(world.bits_short[:dk], W2.bits_short[:dk])
    for nm in world.sym:
        assert _eq(world.sym[nm][:dk], W2.sym[nm][:dk]), nm
    assert _eq(world.stop_scale[:k], W2.stop_scale[:k])


def test_intentional_lookahead_in_a_trigger_is_detected(mk):
    """Guard: the causality test above really can see a future leak."""
    import quantlab5.features.library as FL
    orig = FL._compute

    def leaky(m):
        W = orig(m)
        c = np.asarray(m.nq.c)
        fut = np.r_[c[5:] - c[:-5], np.zeros(5)][m.dec]      # uses 5 bars of the future
        W.F["retz_1"] = fut.astype(np.float32)
        return W
    FL._compute = leaky
    try:
        k = int(mk.dec[len(mk.dec) // 2]) + 2               # cut inside RTH, right after a decision bar
        a, b = compute_world(mk), compute_world(_mutated(mk, k, 1))
    finally:
        FL._compute = orig
    dk = int(np.searchsorted(mk.dec, k))
    assert not _eq(a.F["retz_1"][:dk], b.F["retz_1"][:dk])


@pytest.mark.parametrize("ei", [0, 3, 4, 5, 8, 13])
def test_outcome_table_equals_reference_engine_single_trades(mk, world, sessions_cfg, ei):
    pnl, xbar = compute_outcomes(mk, world.stop_scale)
    ex = EXITS[ei]
    sd = stop_distances(world.stop_scale, mk.dec, ex["stop_mult"])
    win = get_window(sessions_cfg, "rth")
    rng = np.random.default_rng(ei)
    for p in rng.choice(np.nonzero(np.isfinite(sd))[0], 25, replace=False):
        t = mk.dec[p]
        for di, direction in ((0, "long"), (1, "short")):
            sig = np.zeros(mk.n, bool)
            sig[t] = True
            stop = np.full(mk.n, np.nan)
            stop[t] = sd[p]
            tgt = None
            if ex["target_R"] > 0:
                tgt = np.full(mk.n, np.nan)
                tgt[t] = ex["target_R"] * sd[p]
            hold = ex["hold"] if ex["hold"] > 0 else "eod"
            tr = run_signals(mk.nq, sig if di == 0 else np.zeros(mk.n, bool), sig if di == 1 else np.zeros(mk.n, bool),
                             win, direction, hold, stop, tgt, policy=ExecutionPolicy("pessimistic", 1.0))
            assert tr.n == 1
            assert tr.entry_idx[0] == t + 1
            assert tr.exit_idx[0] == xbar[ei, p, di]
            assert abs(tr.points[0] - pnl[ei, p, di]) < 1e-6


def test_kernel_greedy_equals_reference_engine_on_a_real_trigger(mk, world, sessions_cfg):
    pnl, xbar = compute_outcomes(mk, world.stop_scale)
    trig = max(world.triggers, key=lambda t: len(t.pos))
    ei = 0                                                  # S1_T15
    cm = np.zeros(1, np.uint64)
    out = np.zeros((1, 6, len(EXITS), K.NSTAT))
    yidx = np.zeros(len(mk.dec), np.int64)
    K.eval_trigger(trig.pos.astype(np.int64), trig.sign.astype(np.int64), world.bits_long, world.bits_short,
                   mk.dec, yidx, cm, cm, pnl, xbar, 0.0, out)
    sd = stop_distances(world.stop_scale, mk.dec, 1.0)
    sl = np.zeros(mk.n, bool)
    ss = np.zeros(mk.n, bool)
    t = mk.dec[trig.pos]
    ok = np.isfinite(sd[trig.pos])
    sl[t[(trig.sign == 1) & ok]] = True
    ss[t[(trig.sign == -1) & ok]] = True
    stop = np.full(mk.n, np.nan)
    stop[mk.dec] = sd
    tr = run_signals(mk.nq, sl, ss, get_window(sessions_cfg, "rth"), "both", 15, stop, None,
                     policy=ExecutionPolicy("pessimistic", 1.0))
    assert out[0, 0, ei, 0] == tr.n
    assert abs(out[0, 0, ei, 1] - tr.points.sum()) < 1e-6
    # reversal variant = engine with swapped signals
    tr2 = run_signals(mk.nq, ss, sl, get_window(sessions_cfg, "rth"), "both", 15, stop, None,
                      policy=ExecutionPolicy("pessimistic", 1.0))
    assert out[0, 1, ei, 0] == tr2.n and abs(out[0, 1, ei, 1] - tr2.points.sum()) < 1e-6
    # long-only continuation
    tr3 = run_signals(mk.nq, sl, ss, get_window(sessions_cfg, "rth"), "long", 15, stop, None,
                      policy=ExecutionPolicy("pessimistic", 1.0))
    assert out[0, 2, ei, 0] == tr3.n and abs(out[0, 2, ei, 1] - tr3.points.sum()) < 1e-6


def test_filters_restrict_events_by_direction(mk, world):
    pnl, xbar = compute_outcomes(mk, world.stop_scale)
    trig = max(world.triggers, key=lambda t: len(t.pos))
    f = next(x for x in world.filters if x.directional)
    bit = np.uint64(1) << np.uint64(f.bit)
    cm_l = np.array([0, bit], np.uint64)
    cm_s = np.array([0, bit], np.uint64)
    out = np.zeros((2, 6, len(EXITS), K.NSTAT))
    K.eval_trigger(trig.pos.astype(np.int64), trig.sign.astype(np.int64), world.bits_long, world.bits_short,
                   mk.dec, np.zeros(len(mk.dec), np.int64), cm_l, cm_s, pnl, xbar, 0.0, out)
    # the filtered variant only ever trades events whose directional bit is set
    passed_long = ((world.bits_long[trig.pos] & bit) == bit) & (trig.sign == 1)
    assert out[1, 2, 4, 0] <= passed_long.sum()


def test_chunked_computation_equals_full_computation():
    """Memory-bounded chunking (sessions + 125-session warm-up) must reproduce the full computation."""
    from quantlab5.features.library import _compute
    m = synthetic_market(date(2012, 1, 2), date(2012, 12, 31), seed=9)
    full = _compute(m)
    ch = compute_world(m, chunk_sessions=40, warmup_sessions=125)
    assert [t.tid for t in full.triggers] == [t.tid for t in ch.triggers]
    for a, b in zip(full.triggers, ch.triggers):
        assert np.array_equal(a.pos, b.pos) and np.array_equal(a.sign, b.sign), a.tid
    assert np.array_equal(full.bits_long, ch.bits_long) and np.array_equal(full.bits_short, ch.bits_short)
    for k in full.sym:
        assert np.array_equal(full.sym[k], ch.sym[k]), k
    for k in full.F:
        assert np.allclose(full.F[k], ch.F[k], rtol=1e-6, atol=1e-7, equal_nan=True), k
    ok = np.isfinite(full.stop_scale)
    assert np.allclose(full.stop_scale[ok], ch.stop_scale[ok], rtol=1e-9)


def test_trade_reconstruction_matches_kernel_stats(mk, world):
    from quantlab5.search.analysis import rule_neighbours, trades
    from quantlab5.search.reference_grammar import combo_masks, filter_combos
    pnl, xbar = compute_outcomes(mk, world.stop_scale)
    combos = filter_combos(world.filters)
    cm = combo_masks(combos)
    ti = max(range(len(world.triggers)), key=lambda i: len(world.triggers[i].pos))
    trig = world.triggers[ti]
    out = np.zeros((len(combos), 6, len(EXITS), K.NSTAT))
    K.eval_trigger(trig.pos.astype(np.int64), trig.sign.astype(np.int64), world.bits_long, world.bits_short,
                   mk.dec, np.zeros(len(mk.dec), np.int64), cm, cm, pnl, xbar, 0.7, out)
    for ci in (0, 3, len(combos) - 1):
        for vi in range(6):
            for ei in (0, 4, 12):
                tr = trades(("RULE", ti, ci, vi, ei), mk, world, pnl, xbar, 0.7)
                assert len(tr["net"]) == out[ci, vi, ei, 0]
                assert abs(tr["net"].sum() - out[ci, vi, ei, 1]) < 1e-6
    nb = rule_neighbours(("RULE", ti, 3, 0, 1), world)
    assert ("RULE", ti, 3, 0, 0) in nb and ("RULE", ti, 3, 0, 2) in nb and ("RULE", ti, 3, 0, 8) in nb
    assert ("RULE", ti, 0, 0, 1) in nb


def test_neighbours_skip_categorical_parameters(world):
    """Regression: VWAP 'anchor' (rth/glx) is categorical -> no 'adjacent value' neighbour, no crash."""
    from quantlab5.search.analysis import rule_neighbours
    ti = next(i for i, t in enumerate(world.triggers) if t.params.get("anchor") == "rth" and "thr" in t.params)
    nb = rule_neighbours(("RULE", ti, 0, 0, 0), world)
    trig_nb = {a[1] for a in nb if a[1] != ti}
    assert all(world.triggers[j].params.get("anchor") == "rth" for j in trig_nb)
