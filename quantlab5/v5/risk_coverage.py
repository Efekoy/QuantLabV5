"""Prospective per-candidate MNQ sizing and coverage at four fixed budgets."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from quantlab5.engine.execution import ExecutionPolicy, get_window, run_signals, window_arrays
from quantlab5.risk.fixed_dollar import ContractSpec, fixed_dollar_size

BUDGETS = (250, 300, 350, 400)
MNQ = ContractSpec("MNQ", point_value=2.0, tick_size=0.25)


@dataclass(frozen=True)
class BudgetCoverage:
    budget: int
    signals: int
    valid_signals: int
    one_mnq_floor_skips: int
    executable_signals: int
    executed_trades: int
    coverage: float
    integer_contracts: tuple[int, ...]
    baseline_net_usd: float
    stress_net_usd: float


def evaluate_mnq_budgets(bars, sig_long, sig_short, stop_dist, sessions_cfg, costs,
                         *, hold: int = 60, window_name: str = "rth",
                         policy: ExecutionPolicy = ExecutionPolicy()) -> dict[int, BudgetCoverage]:
    """Re-run engine separately at each budget: SKIP changes later entry availability."""
    n = bars.n
    long = np.asarray(sig_long, bool)
    short = np.asarray(sig_short, bool)
    stop = np.broadcast_to(np.asarray(stop_dist, float), (n,))
    if len(long) != n or len(short) != n:
        raise ValueError("signal length mismatch")
    window = get_window(sessions_cfg, window_name)
    entry_ok, _ = window_arrays(bars, window)
    signalled = long | short
    valid = np.zeros(n, bool)
    if n > 1:
        valid[:-1] = signalled[:-1] & entry_ok[1:] & np.isfinite(stop[:-1]) & (stop[:-1] > 0)
    indices = np.flatnonzero(valid)
    out = {}
    baseline_friction = costs.per_trade("MNQ", "baseline")
    stress_friction = costs.per_trade("MNQ", "stress")
    for budget in BUDGETS:
        sizes = np.zeros(n, dtype=np.int64)
        floor_skips = 0
        for i in indices:
            result = fixed_dollar_size(budget, float(stop[i]), MNQ,
                                       cost_per_contract_usd=baseline_friction)
            if result.decision == "SKIP":
                floor_skips += 1
            else:
                sizes[i] = result.contracts
        tradable = np.ones(n, bool)
        tradable[indices + 1] = sizes[indices] > 0
        tr = run_signals(bars, long, short, window, "both", hold, stop, None,
                         False, policy, MNQ.tick_size, tradable)
        executed_sizes = sizes[np.asarray(tr.entry_idx, int) - 1]
        if len(executed_sizes) and np.any(executed_sizes < 1):
            raise AssertionError("engine executed a floor-skipped signal")
        points = np.asarray(tr.points, float)
        baseline = float(np.sum(executed_sizes * (points * MNQ.point_value - baseline_friction)))
        stress = float(np.sum(executed_sizes * (points * MNQ.point_value - stress_friction)))
        out[budget] = BudgetCoverage(
            budget=budget, signals=int(signalled.sum()), valid_signals=len(indices),
            one_mnq_floor_skips=floor_skips, executable_signals=len(indices) - floor_skips,
            executed_trades=int(tr.n), coverage=float(tr.n / len(indices)) if len(indices) else 0.0,
            integer_contracts=tuple(int(x) for x in executed_sizes),
            baseline_net_usd=baseline, stress_net_usd=stress)
    return out
