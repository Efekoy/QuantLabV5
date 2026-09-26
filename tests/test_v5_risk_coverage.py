import numpy as np

from quantlab5.engine.costs import CostModel
from quantlab5.synthetic.markets import rising_market
from quantlab5.v5.risk_coverage import BUDGETS, evaluate_mnq_budgets


def test_four_budget_floor_skips_and_integer_sizing(costs_cfg, sessions_cfg):
    b = rising_market(n=390, step=1.0)
    long = np.zeros(b.n, bool)
    long[[50, 150, 250]] = True
    stop = np.full(b.n, 100.0)
    stop[150] = 180.0  # one MNQ needs more than $350, but fits $400
    x = evaluate_mnq_budgets(b, long, np.zeros(b.n, bool), stop, sessions_cfg,
                             CostModel(costs_cfg, "test"), hold=10)
    assert set(x) == set(BUDGETS)
    assert all(v.signals == 3 and v.valid_signals == 3 for v in x.values())
    assert x[250].one_mnq_floor_skips == 1
    assert x[300].one_mnq_floor_skips == 1
    assert x[350].one_mnq_floor_skips == 1
    assert x[400].one_mnq_floor_skips == 0
    assert x[400].executed_trades == 3
    assert len(x[400].integer_contracts) == 3
    assert all(isinstance(q, int) and q > 0 for q in x[400].integer_contracts)
    assert all(v.baseline_net_usd >= v.stress_net_usd for v in x.values())
