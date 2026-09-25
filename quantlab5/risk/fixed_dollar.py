"""Fixed-dollar risk sizing -- deterministic integer contracts, never above budget.

Inputs: desired dollar risk, stop distance (points), the contract's point value and
minimum tick, optional per-contract cost to include in risk, an optional contract
cap, and optionally a micro contract to fill the remainder.

Arithmetic is exact (Decimal -> integer cents), so results never depend on float
rounding:
  stop_ticks          = ceil(stop_distance / tick)          (a stop between ticks is
                        rounded AWAY from entry: the conservative direction)
  risk_per_contract   = stop_ticks * tick_value + cost_per_contract
  contracts           = floor(risk_budget / risk_per_contract), then capped

If even ONE contract exceeds the budget the policy decides:
  SKIP     (default) -> 0 contracts, decision SKIP. Risk is never silently exceeded.
  MIN_ONE  (explicit opt-in) -> 1 contract, flagged exceeds_budget=True.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_HALF_EVEN, Decimal


@dataclass(frozen=True)
class ContractSpec:
    symbol: str
    point_value: float
    tick_size: float

    @property
    def tick_value_cents(self) -> int:
        tv = Decimal(str(self.tick_size)) * Decimal(str(self.point_value)) * 100
        if tv != tv.to_integral_value():
            raise ValueError(f"{self.symbol}: tick value is not a whole number of cents")
        return int(tv)


@dataclass(frozen=True)
class SizeResult:
    decision: str                 # TRADE | SKIP
    contracts: int                # standard (or the only) contract
    micro_contracts: int
    stop_ticks: int
    risk_per_contract_usd: float
    total_risk_usd: float
    budget_usd: float
    exceeds_budget: bool
    reason: str


def _cents(x) -> int:
    return int((Decimal(str(x)) * 100).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def stop_ticks(stop_distance_points: float, tick_size: float) -> int:
    if not stop_distance_points > 0:
        raise ValueError("stop distance must be > 0")
    t = (Decimal(str(stop_distance_points)) / Decimal(str(tick_size))).to_integral_value(rounding=ROUND_CEILING)
    return int(t)


def fixed_dollar_size(risk_usd: float, stop_distance_points: float, spec: ContractSpec,
                      max_contracts: int | None = None, policy: str = "SKIP",
                      cost_per_contract_usd: float = 0.0) -> SizeResult:
    if not risk_usd > 0:
        raise ValueError("risk budget must be > 0")
    if policy not in ("SKIP", "MIN_ONE"):
        raise ValueError(f"unknown policy {policy}")
    if max_contracts is not None and max_contracts < 0:
        raise ValueError("max_contracts must be >= 0")
    ticks = stop_ticks(stop_distance_points, spec.tick_size)
    per = ticks * spec.tick_value_cents + _cents(cost_per_contract_usd)
    budget = _cents(risk_usd)
    n = budget // per
    reason = "sized to budget"
    exceeds = False
    if max_contracts is not None and n > max_contracts:
        n = max_contracts
        reason = f"capped at max_contracts={max_contracts}"
    if n == 0:
        if max_contracts == 0:
            return SizeResult("SKIP", 0, 0, ticks, per / 100, 0.0, budget / 100, False, "max_contracts is 0")
        if policy == "SKIP":
            return SizeResult("SKIP", 0, 0, ticks, per / 100, 0.0, budget / 100, False,
                              "one contract would exceed the risk budget")
        n, exceeds, reason = 1, True, "MIN_ONE policy: one contract exceeds the budget"
    return SizeResult("TRADE", int(n), 0, ticks, per / 100, n * per / 100, budget / 100, exceeds, reason)


def fixed_dollar_size_mixed(risk_usd: float, stop_distance_points: float, standard: ContractSpec,
                            micro: ContractSpec, max_standard: int | None = None, max_micro: int | None = None,
                            cost_standard_usd: float = 0.0, cost_micro_usd: float = 0.0) -> SizeResult:
    """Standard contracts first, then micros for the remaining budget. Never above budget; SKIP if nothing fits."""
    if not risk_usd > 0:
        raise ValueError("risk budget must be > 0")
    ticks_s = stop_ticks(stop_distance_points, standard.tick_size)
    ticks_m = stop_ticks(stop_distance_points, micro.tick_size)
    per_s = ticks_s * standard.tick_value_cents + _cents(cost_standard_usd)
    per_m = ticks_m * micro.tick_value_cents + _cents(cost_micro_usd)
    budget = _cents(risk_usd)
    n_s = budget // per_s
    if max_standard is not None:
        n_s = min(n_s, max_standard)
    rem = budget - n_s * per_s
    n_m = rem // per_m
    if max_micro is not None:
        n_m = min(n_m, max_micro)
    total = n_s * per_s + n_m * per_m
    if n_s == 0 and n_m == 0:
        return SizeResult("SKIP", 0, 0, ticks_s, per_s / 100, 0.0, budget / 100, False,
                          "one micro contract would exceed the risk budget")
    return SizeResult("TRADE", int(n_s), int(n_m), ticks_s, per_s / 100, total / 100, budget / 100, False,
                      "standard contracts first, micros for the remainder")
