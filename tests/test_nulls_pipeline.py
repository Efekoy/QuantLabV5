"""Null worlds are ordinary Bars and go through the SAME evaluation pipeline as real data."""
from datetime import date

import numpy as np
import pytest

from quantlab5.engine.costs import CostModel
from quantlab5.nulls import evaluator as null_eval
from quantlab5.nulls.base import BlockSignFlipNull, SessionPermutationNull
from quantlab5.search import pipeline
from quantlab5.search.generator import enumerate_candidates
from quantlab5.search.grammar import Dimension, Grammar
from quantlab5.synthetic import markets as M

SESS = M.weekdays(date(2020, 10, 5), date(2020, 10, 16))     # 10 sessions


def _market():
    nq, es = M.correlated_pair(SESS, missing_every=10**9)
    return {"NQ": nq, "ES": es}


def dummy_builder(spec, market):
    """SYNTHETIC dummy signal builder: momentum over `n` bars (test only, not a strategy)."""
    b = market[spec["instrument"]]
    c = np.asarray(b.c)
    n = spec["n"]
    up = np.zeros(b.n, bool)
    dn = np.zeros(b.n, bool)
    up[n:] = c[n:] - c[:-n] > spec["thr"]
    dn[n:] = c[:-n] - c[n:] > spec["thr"]
    return pipeline.SignalSet(spec["instrument"], up, dn, window="globex", hold=spec["hold"])


def _ctx(costs_cfg, sessions_cfg):
    return pipeline.EvalContext(CostModel(costs_cfg, "t"), sessions_cfg)


def _cands():
    g = Grammar("dummy", "1", [Dimension("instrument", ("NQ", "ES")), Dimension("n", (5, 15)),
                               Dimension("thr", (2.0,)), Dimension("hold", (10,))])
    return list(enumerate_candidates(g))


@pytest.mark.parametrize("gen", [BlockSignFlipNull(30, joint=True), BlockSignFlipNull(15, joint=False),
                                 SessionPermutationNull(joint=True), SessionPermutationNull(replace=True)])
def test_null_generators_keep_structure_and_are_deterministic(gen):
    m = _market()
    w1, w2, w3 = gen.generate(m, 1), gen.generate(m, 1), gen.generate(m, 2)
    for k in m:
        assert np.array_equal(w1[k].ts, m[k].ts) and np.array_equal(w1[k].seg, m[k].seg)
        assert np.array_equal(w1[k].sday, m[k].sday)
        assert w1[k].content_hash() == w2[k].content_hash()
        assert w1[k].source.startswith("null:")
        prices = np.r_[w1[k].o, w1[k].h, w1[k].l, w1[k].c]
        assert np.allclose(prices / 0.25, np.round(prices / 0.25))       # tick grid preserved
    assert any(w1[k].content_hash() != w3[k].content_hash() for k in m)
    assert all(w1[k].content_hash() != m[k].content_hash() for k in m)
    assert all(np.array_equal(m[k].c, _market()[k].c) for k in m)       # input untouched


def test_sign_flip_preserves_absolute_moves_and_joint_flips_are_shared():
    m = _market()
    w = BlockSignFlipNull(30, joint=True).generate(m, 5)
    for k in m:
        assert np.allclose(np.abs(np.diff(w[k].c)), np.abs(np.diff(m[k].c)))
        assert np.allclose(w[k].h - w[k].l, m[k].h - m[k].l)            # bar ranges preserved
        assert np.array_equal(w[k].v, m[k].v)
    s_nq = np.sign(np.diff(w["NQ"].c)) * np.sign(np.diff(m["NQ"].c))
    s_es = np.sign(np.diff(w["ES"].c)) * np.sign(np.diff(m["ES"].c))
    both = (s_nq != 0) & (s_es != 0)
    assert np.array_equal(s_nq[both], s_es[both])                        # same flip at the same minute


def test_sign_flip_keeps_roll_gaps():
    b = M.roll_boundary_market()
    w = BlockSignFlipNull(30).generate({"SYN": b}, 3)["SYN"]
    r = int(np.nonzero(np.diff(b.seg))[0][0] + 1)
    assert w.o[r] - w.c[r - 1] == b.o[r] - b.c[r - 1]


def test_session_permutation_moves_whole_session_paths():
    m = _market()
    w = SessionPermutationNull(joint=True).generate(m, 4)
    for k in m:
        for d in np.unique(m[k].sday):
            sel = m[k].sday == d
            shape_new = np.asarray(w[k].c)[sel] - np.asarray(w[k].o)[sel][0]
            shapes = [np.asarray(m[k].c)[m[k].sday == e] - np.asarray(m[k].o)[m[k].sday == e][0]
                      for e in np.unique(m[k].sday)]
            assert any(np.allclose(shape_new, s) for s in shapes)


def test_null_runner_uses_the_same_evaluator_function(costs_cfg, sessions_cfg, monkeypatch):
    calls = []
    real_fn = pipeline.evaluate_candidates

    def spy(*a, **k):
        calls.append(a[0])
        return real_fn(*a, **k)

    monkeypatch.setattr(pipeline, "evaluate_candidates", spy)
    m = _market()
    worlds = null_eval.run_null_worlds(m, _cands(), dummy_builder, _ctx(costs_cfg, sessions_cfg),
                                       BlockSignFlipNull(30), seeds=[1, 2])
    assert len(calls) == 2 and all(isinstance(w["results"], list) for w in worlds)
    assert all(b.source.startswith("null:") for world in calls for b in world.values())


def test_null_and_real_paths_give_identical_results_on_identical_bars(costs_cfg, sessions_cfg):
    """Feeding a null world through the null runner == feeding the same Bars to the pipeline directly."""
    m = _market()
    ctx = _ctx(costs_cfg, sessions_cfg)
    gen = SessionPermutationNull()
    via_runner = null_eval.run_null_worlds(m, _cands(), dummy_builder, ctx, gen, seeds=[9])[0]["results"]
    direct = pipeline.evaluate_candidates(gen.generate(m, 9), _cands(), dummy_builder, ctx)
    assert [r.summary() for r in via_runner] == [r.summary() for r in direct]
    real = pipeline.evaluate_candidates(m, _cands(), dummy_builder, ctx)
    assert [r.candidate_id for r in real] == [r.candidate_id for r in direct]
    assert any(a.trades_sha256 != b.trades_sha256 for a, b in zip(real, direct))


def test_planted_edge_is_found_on_real_and_destroyed_by_sign_flip(costs_cfg, sessions_cfg):
    b = M.planted_edge_market(SESS)
    ctx = _ctx(costs_cfg, sessions_cfg)

    def builder(spec, market):
        bb = market["NQ"]
        return pipeline.SignalSet("NQ", M.planted_edge_signal(bb), np.zeros(bb.n, bool), "globex",
                                  "long", M.PLANT_BARS)

    g = Grammar("plant", "1", [Dimension("x", (1,))])
    real = pipeline.evaluate_candidates({"NQ": b}, enumerate_candidates(g), builder, ctx)[0]
    assert np.allclose(real.points, M.PLANT_BARS * M.PLANT_DRIFT)
    nulls = null_eval.run_null_worlds({"NQ": b}, enumerate_candidates(g), builder, ctx,
                                      BlockSignFlipNull(5, joint=False), seeds=range(5))
    assert all(not np.allclose(w["results"][0].points, M.PLANT_BARS * M.PLANT_DRIFT) for w in nulls)


def test_there_is_no_separate_null_evaluator_in_the_source():
    import inspect
    src = inspect.getsource(null_eval)
    assert "pipeline.evaluate_candidates(" in src
    for forbidden in ("run_signals", "run_backtest", "per_trade"):
        assert forbidden not in src
