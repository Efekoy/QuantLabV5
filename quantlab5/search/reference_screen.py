"""REFERENCE ONLY: the V4 campaign-1 discovery screen, ported for the inherited world runner and its tests.
The V5 screen thresholds will be set by the V5 preregistration, not here.

(V4 docstring follows.) Discovery screen (frozen with the V4 preregistration). All P&L is NET of baseline costs, in NQ points.

A candidate is ELIGIBLE when:
  n_trades >= MIN_TRADES
  active years >= MIN_ACTIVE_YEARS, and positive in >= 2/3 of its active years
  both halves of its active years are net positive
  PF >= MIN_PF
  still net positive under the STRESS cost scenario
A candidate PASSES when it is eligible AND t_net >= T_PASS.
The research statistic of a family (and of the whole search) is the MAX t_net over ELIGIBLE candidates,
and the number of PASSING candidates. Null worlds compute exactly the same quantities.
"""
from __future__ import annotations

import numpy as np

from quantlab5.search.kernel import N_YEARS, stats_to_metrics

MIN_TRADES = 200
MIN_ACTIVE_YEARS = 6
YEAR_POS_FRAC = 2.0 / 3.0
MIN_PF = 1.10
T_PASS = 3.0
COST_PTS = {"gross": 0.0, "moderate": 9.0 / 20.0, "baseline": 14.0 / 20.0, "stress": 26.0 / 20.0}


def evaluate(st: np.ndarray) -> dict:
    """st: [..., NSTAT] net-of-baseline stats -> metrics + eligible/pass masks."""
    met = stats_to_metrics(st)
    ys = st[..., 7:7 + N_YEARS]
    yn = st[..., 7 + N_YEARS:7 + 2 * N_YEARS]
    active = yn > 0
    k = active.sum(-1)
    cum = np.cumsum(active, axis=-1)
    first = active & (cum <= (k // 2)[..., None])
    second = active & ~first
    h1 = np.where(first, ys, 0).sum(-1)
    h2 = np.where(second, ys, 0).sum(-1)
    stress_sum = met["sum"] - met["n"] * (COST_PTS["stress"] - COST_PTS["baseline"])
    with np.errstate(invalid="ignore"):
        elig = ((met["n"] >= MIN_TRADES) & (k >= MIN_ACTIVE_YEARS) & (met["years_pos"] >= np.ceil(YEAR_POS_FRAC * k))
                & (h1 > 0) & (h2 > 0) & (met["pf"] >= MIN_PF) & (stress_sum > 0) & np.isfinite(met["t"]))
        passed = elig & (met["t"] >= T_PASS)
    met.update({"eligible": elig, "passed": passed, "h1": h1, "h2": h2, "stress_sum": stress_sum})
    return met
