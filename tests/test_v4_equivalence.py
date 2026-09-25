"""V5 regression guard: the ported engine is BEHAVIOURALLY IDENTICAL to the proven V4 engine.

Every test builds the same synthetic input, runs it through QuantLabV4's `quantlab4` (imported read-only
from the V4 project on disk) and through V5's `quantlab5`, and requires bit-identical outputs:
bars/sessions, resampling, next-bar execution, costs, outcome tables, the search kernel and a complete
search world, null generators, fixed-dollar sizing and the prop-account simulator.

The ONLY intended behavioural difference is the candidate-ID namespace/prefix (Q5/quantlab5 instead of
Q4/quantlab4), tested explicitly below. Skipped if QuantLabV4 is not present next to QuantLabV5.
Synthetic data only.
"""
from __future__ import annotations

import importlib
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pytest

V4_ROOT = Path(__file__).resolve().parents[2] / "QuantLabV4"
pytestmark = pytest.mark.skipif(not (V4_ROOT / "quantlab4" / "__init__.py").is_file(),
                                reason="QuantLabV4 not present; equivalence cannot be checked")


@pytest.fixture(scope="module")
def v4():
    if str(V4_ROOT) not in sys.path:
        sys.path.append(str(V4_ROOT))          # appended: quantlab5 always resolves to V5 first
    import quantlab5
    q4 = importlib.import_module("quantlab4")
    assert Path(q4.__file__).resolve().parents[1] == V4_ROOT.resolve()        # really the V4 code
    assert Path(quantlab5.__file__).resolve().parents[1] == Path(__file__).resolve().parents[1]
    return lambda name: importlib.import_module(name)


def _eq(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.dtype.kind == "f":
        return a.shape == b.shape and np.array_equal(a, b, equal_nan=True)
    return a.shape == b.shape and np.array_equal(a, b)


def _bars_eq(x, y):
    return all(_eq(getattr(x, k), getattr(y, k)) for k in ("ts", "o", "h", "l", "c", "v", "seg", "sday", "sm"))


@pytest.fixture(scope="module")
def markets(v4):
    from quantlab5.synthetic.market_builders import synthetic_market
    m4 = v4("quantlab4.v4.synth").synthetic_market(date(2012, 1, 2), date(2012, 2, 28), seed=4)
    m5 = synthetic_market(date(2012, 1, 2), date(2012, 2, 28), seed=4)
    return m4, m5


def test_synthetic_markets_sessions_and_alignment_identical(markets):
    m4, m5 = markets
    assert _bars_eq(m4.nq, m5.nq) and _bars_eq(m4.es, m5.es)
    for k in ("gid", "rw", "es_rw", "eo", "eh", "el", "ec", "ev", "evalid", "es_seg", "dec"):
        assert _eq(getattr(m4, k), getattr(m5, k)), k


def test_session_fields_and_resampling_identical(v4, markets):
    from quantlab5.data.resample import htf_for_bars
    from quantlab5.data.sessions import session_fields
    m4, m5 = markets
    ts = np.asarray(m5.nq.ts)
    for a, b in zip(v4("quantlab4.data.sessions").session_fields(ts), session_fields(ts)):
        assert _eq(a, b)
    for k in (3, 5, 15, 60):
        h4, h5 = v4("quantlab4.data.resample").htf_for_bars(m4.nq, k), htf_for_bars(m5.nq, k)
        for f in h5.__dataclass_fields__:
            assert _eq(getattr(h4, f), getattr(h5, f)), (k, f)


@pytest.mark.parametrize("direction,hold", [("both", 15), ("long", "eod"), ("short", 60)])
def test_next_bar_execution_engine_identical(v4, markets, sessions_cfg, direction, hold):
    from quantlab5.engine.execution import ExecutionPolicy, get_window, run_signals
    E4 = v4("quantlab4.engine.execution")
    m4, m5 = markets
    rng = np.random.default_rng(7)
    sl, ss = rng.random(m5.n) < 0.02, rng.random(m5.n) < 0.02
    stop = np.where(rng.random(m5.n) < 0.5, np.round(rng.uniform(2, 20, m5.n) * 4) / 4, np.nan)
    tgt = np.where(np.isfinite(stop), 2 * stop, np.nan)
    t5 = run_signals(m5.nq, sl, ss, get_window(sessions_cfg, "rth"), direction, hold, stop, tgt,
                     policy=ExecutionPolicy("pessimistic", 1.0))
    t4 = E4.run_signals(m4.nq, sl, ss, E4.get_window(sessions_cfg, "rth"), direction, hold, stop, tgt,
                        policy=E4.ExecutionPolicy("pessimistic", 1.0))
    assert t5.n == t4.n and t5.n > 10
    for f in t5.__dataclass_fields__:
        assert _eq(getattr(t4, f), getattr(t5, f)), f


def test_costs_identical(v4, costs_cfg):
    from quantlab5.engine.costs import CostModel
    c4, c5 = v4("quantlab4.engine.costs").CostModel(costs_cfg, "x"), CostModel(costs_cfg, "x")
    for inst in ("NQ", "ES", "MNQ", "MES"):
        for sc in costs_cfg["scenarios"]:
            assert c4.per_trade(inst, sc) == c5.per_trade(inst, sc)
            assert c4.trade_cost(inst, sc, (0.5, 0.25, 0.25)) == c5.trade_cost(inst, sc, (0.5, 0.25, 0.25))
    assert c5.per_trade("NQ", "baseline") == 14.0 and c5.per_trade("ES", "baseline") == 29.0


def test_feature_library_outcomes_and_kernel_identical(v4, markets):
    from quantlab5.engine.outcomes import compute_outcomes
    from quantlab5.features.library import compute_world
    m4, m5 = markets
    W4, W5 = v4("quantlab4.v4.featurelib").compute_world(m4), compute_world(m5)
    assert sorted(W4.F) == sorted(W5.F) and all(_eq(W4.F[k], W5.F[k]) for k in W5.F)
    assert [t.tid for t in W4.triggers] == [t.tid for t in W5.triggers]
    assert all(_eq(a.pos, b.pos) and _eq(a.sign, b.sign) for a, b in zip(W4.triggers, W5.triggers))
    assert _eq(W4.bits_long, W5.bits_long) and _eq(W4.bits_short, W5.bits_short) and _eq(W4.stop_scale, W5.stop_scale)
    assert all(_eq(W4.sym[k], W5.sym[k]) for k in W5.sym)
    p4, x4 = v4("quantlab4.v4.outcomes").compute_outcomes(m4, W4.stop_scale)
    p5, x5 = compute_outcomes(m5, W5.stop_scale)
    assert _eq(p4, p5) and _eq(x4, x5)


def test_complete_search_world_identical(v4, markets, tmp_path):
    """The whole V4 search (every RULE + SYM candidate, screen, family statistics) on one world."""
    from quantlab5.search.world import run_world
    m4, m5 = markets
    s4 = v4("quantlab4.v4.world").run_world(m4, first_year=2012, ml_folds=(), save_dir=tmp_path / "v4")
    s5 = run_world(m5, first_year=2012, ml_folds=(), save_dir=tmp_path / "v5")
    for d in (s4, s5):
        d.pop("timing_s", None)
    assert s4 == s5
    f4 = sorted(p.name for p in (tmp_path / "v4").iterdir())
    assert f4 == sorted(p.name for p in (tmp_path / "v5").iterdir()) and f4
    for name in f4:
        if name.endswith(".npy"):
            assert _eq(np.load(tmp_path / "v4" / name), np.load(tmp_path / "v5" / name)), name


@pytest.mark.parametrize("cls,kw", [("MinuteSignFlipNull", {"joint": True}), ("MinuteSignFlipNull", {"joint": False}),
                                    ("TodBlockResampleNull", {"block_minutes": 30, "joint": True}),
                                    ("BlockSignFlipNull", {"block_minutes": 30, "joint": True}),
                                    ("SessionPermutationNull", {"joint": True})])
def test_null_generators_identical(v4, markets, cls, kw):
    import quantlab5.nulls.base as N5
    N4 = v4("quantlab4.nulls.base")
    m4, m5 = markets
    w4 = getattr(N4, cls)(**kw).generate({"NQ": m4.nq, "ES": m4.es}, 123)
    w5 = getattr(N5, cls)(**kw).generate({"NQ": m5.nq, "ES": m5.es}, 123)
    assert _bars_eq(w4["NQ"], w5["NQ"]) and _bars_eq(w4["ES"], w5["ES"])


def test_fixed_dollar_sizing_identical(v4):
    from quantlab5.risk.fixed_dollar import ContractSpec, fixed_dollar_size
    F4 = v4("quantlab4.risk.fixed_dollar")
    for risk in (50, 100, 150, 200, 250, 333.33, 1000):
        for stop in (0.25, 1.0, 3.3, 7.75, 10.0, 25.0, 60.0, 151.0):
            a = F4.fixed_dollar_size(risk, stop, F4.ContractSpec("MNQ", 2.0, 0.25))
            b = fixed_dollar_size(risk, stop, ContractSpec("MNQ", 2.0, 0.25))
            assert a.__dict__ == b.__dict__, (risk, stop)


def test_prop_account_simulator_identical(v4):
    from quantlab5.prop.account import Day, PropProfile, simulate_account
    A4 = v4("quantlab4.prop.account")
    rng = np.random.default_rng(11)
    for mode, lock, dl, act, cons in (("eod", 0, 1000, "halt_day", 0.5), ("intraday", 100, None, "halt_day", None),
                                      ("static", None, 2000, "fail", None)):
        args = ("P", 50000, 3000, 2000, mode, lock, dl, act, cons, 3, {"MNQ": 50})
        for _ in range(30):
            days = [(f"2020-01-{i + 1:02d}", [float(x) for x in rng.normal(60, 400, rng.integers(0, 4))])
                    for i in range(25)]
            r4 = A4.simulate_account(A4.PropProfile(*args), [A4.Day(d, m) for d, m in days])
            r5 = simulate_account(PropProfile(*args), [Day(d, m) for d, m in days])
            assert r4.__dict__ == r5.__dict__


def test_candidate_ids_differ_only_by_the_intended_v5_namespace(v4):
    from quantlab5.search.candidate_id import IdScheme, candidate_id
    I4 = v4("quantlab4.search.candidate_id")
    spec = {"family": "X", "params": {"n": 5, "k": 1.5}, "exit": "T30"}
    assert candidate_id(spec).startswith("Q5-") and I4.candidate_id(spec).startswith("Q4-")
    assert candidate_id(spec) != I4.candidate_id(spec)                         # V5 IDs never collide with V4
    assert candidate_id(spec, IdScheme("Q4", 24, "quantlab4")) == I4.candidate_id(spec)   # same function
