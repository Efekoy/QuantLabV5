from datetime import date

import numpy as np

from quantlab5.data.market import build_market
from quantlab5.synthetic.markets import correlated_pair, weekdays
from quantlab5.v5.market_plant import plant_e03_long, realized_plant_effect_r


def test_plant_changes_only_future_nq_bars_and_is_deterministic():
    nq, es = correlated_pair(weekdays(date(2020, 1, 2), date(2020, 2, 13)))
    base = build_market(nq, es, np.full(nq.n, "NQZ0"), np.full(es.n, "ESZ0"))
    a = plant_e03_long(base, effect_r=.10, trades_per_year=250,
                       shape="stable_plateau", seed=55)
    b = plant_e03_long(base, effect_r=.10, trades_per_year=250,
                       shape="stable_plateau", seed=55)
    assert len(a.selected_decision_bars) > 0
    first = int(a.selected_decision_bars[0])
    assert np.array_equal(a.world.nq.c[:first+1], base.nq.c[:first+1])
    assert np.array_equal(a.world.nq.c, b.world.nq.c)
    assert np.array_equal(a.world.es.c, base.es.c)
    assert len(a.target_ids) > 1
    assert np.any(a.world.nq.c[first+1:] != base.nq.c[first+1:])
    assert np.isfinite(realized_plant_effect_r(base, a))
    for shape in ("isolated_needle", "heterogeneous_family", "regime_specific"):
        planted = plant_e03_long(base, effect_r=.05, trades_per_year=100,
                                 shape=shape, seed=56)
        assert len(planted.selected_decision_bars) > 0
