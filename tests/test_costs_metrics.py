"""Costs, profit factor, drawdown, streaks: known inputs -> exact outputs.
(Ported from QuantLabV3; "stressed" -> "stress"; trade_table now takes Bars; sizing column added.)"""
import math

import numpy as np
import pandas as pd

from quantlab5.engine.costs import CostModel
from quantlab5.engine.metrics import longest_losing_streak, max_drawdown, profit_factor, summarize

COSTS = {"instruments": {"NQ": {"tick_size": 0.25, "point_value": 20.0, "commission_round_trip": 4.0,
                                "slippage_ticks_per_side": 1.0, "extra_cost_round_trip": 0.0}},
         "scenarios": {"gross": {"commission_mult": 0, "slippage_mult": 0, "extra_mult": 0},
                       "moderate": {"commission_mult": 1, "slippage_mult": 0.5, "extra_mult": 1},
                       "baseline": {"commission_mult": 1, "slippage_mult": 1, "extra_mult": 1},
                       "stress": {"commission_mult": 1.5, "slippage_mult": 2, "extra_mult": 1}}}


def test_cost_per_trade_exact():
    cm = CostModel(COSTS, "t")
    assert cm.per_trade("NQ", "gross") == 0.0
    assert cm.per_trade("NQ", "moderate") == 4.0 + 2 * 0.5 * 0.25 * 20      # 9.00
    assert cm.per_trade("NQ", "baseline") == 4.0 + 2 * 1 * 0.25 * 20        # 14.00
    assert cm.per_trade("NQ", "stress") == 6.0 + 2 * 2 * 0.25 * 20        # 26.00


def test_known_trades_gross_and_net():
    from quantlab5.engine.backtest import Trades
    from quantlab5.engine.metrics import trade_table
    from quantlab5.data.schema import bars_from_arrays
    from conftest import make_bars
    ts, o, h, l, c = make_bars([100] * 10)
    v = bars_from_arrays("NQ", ts, o, h, l, c, np.full(10, 5))
    tr = Trades(np.array([1, 5]), np.array([3, 7]), np.array([1, -1], np.int8), np.array([100.0, 100.0]),
                np.array([110.0, 102.5]), np.array([3, 3], np.int8), np.zeros(2, bool), np.zeros(2), np.zeros(2))
    cm = CostModel(COSTS, "t")
    df = trade_table(tr, v, "NQ", cm)
    assert df["points"].tolist() == [10.0, -2.5]
    assert df["gross_usd"].tolist() == [200.0, -50.0]
    assert df["net_usd"].tolist() == [186.0, -64.0]
    assert df["stress_usd"].tolist() == [174.0, -76.0]
    s = summarize(df, {"years": 1.0, "tradable_bars": 10}, False, 20.0)
    assert s["gross_pnl"] == 150.0 and s["net_pnl"] == 122.0
    assert s["wins"] == 1 and s["losses"] == 1 and s["win_rate"] == 0.5
    assert math.isclose(s["profit_factor"], 186.0 / 64.0)
    assert math.isclose(s["profit_factor_gross"], 200.0 / 50.0)
    assert math.isnan(s["avg_r"])      # time exits: no R is invented
    # integer contracts scale P&L and costs per contract
    df3 = trade_table(tr, v, "NQ", cm, contracts=[3, 2])
    assert df3["net_usd"].tolist() == [3 * 186.0, 2 * -64.0]


def test_profit_factor():
    assert profit_factor(np.array([100.0, -50.0, 200.0, -100.0])) == 2.0
    assert math.isinf(profit_factor(np.array([10.0, 20.0])))          # no losers: inf, never capped
    assert math.isnan(profit_factor(np.array([])))
    assert profit_factor(np.array([-5.0])) == 0.0


def test_drawdown_and_streak():
    pnl = np.array([100.0, -50.0, 200.0, -100.0, -60.0, 30.0])
    # equity 0,100,50,250,150,90,120 -> worst fall 250 -> 90 = 160
    assert max_drawdown(pnl) == 160.0
    assert max_drawdown(np.array([-10.0, -20.0])) == 30.0              # from starting equity 0
    assert longest_losing_streak(np.array([-1, -1, 1, -1, -1, -1, 2.0])) == 3


def test_empty_trades_are_not_profitable():
    df = pd.DataFrame(columns=["net_usd", "gross_usd", "stress_usd", "points", "hold_min", "side", "session",
                               "mae_pts", "mfe_pts", "ambiguous"])
    s = summarize(df, {"years": 1.0}, False, 20.0)
    assert s["trades"] == 0 and s["net_pnl"] == 0.0


def test_project_cost_config_matches_inherited_v3_values(costs_cfg):
    cm = CostModel(costs_cfg, costs_cfg["version"])
    assert cm.per_trade("NQ", "baseline") == 14.0 and cm.per_trade("ES", "baseline") == 29.0
    assert cm.per_trade("NQ", "moderate") == 9.0 and cm.per_trade("ES", "moderate") == 16.5
    assert cm.per_trade("NQ", "stress") == 26.0 and cm.per_trade("ES", "stress") == 56.0
    assert cm.per_trade("NQ", "gross") == 0.0


def test_unvalidated_micro_costs_are_flagged(costs_cfg):
    import pytest
    cm = CostModel(costs_cfg, costs_cfg["version"])
    cm.require_validated("NQ")
    with pytest.raises(ValueError):
        cm.require_validated("MNQ")


def test_partial_exit_cost_equals_one_round_trip():
    cm = CostModel(COSTS, "t")
    assert math.isclose(cm.trade_cost("NQ", "baseline", (0.5, 0.5)), cm.per_trade("NQ", "baseline"))
