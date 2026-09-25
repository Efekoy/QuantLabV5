"""Consistency rule: no single day may contribute more than a fraction of total profit."""
from __future__ import annotations


def consistency_ok(day_pnls: list[float], total_profit: float, max_day_fraction: float | None) -> bool:
    if max_day_fraction is None:
        return True
    if total_profit <= 0:
        return False
    best = max([p for p in day_pnls if p > 0], default=0.0)
    return best <= max_day_fraction * total_profit + 1e-9
