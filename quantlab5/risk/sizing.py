"""Sizing rules as data (hashable into a frozen cohort) plus an open-risk guard."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from quantlab5.risk.fixed_contract import fixed_contract_size
from quantlab5.risk.fixed_dollar import ContractSpec, SizeResult, fixed_dollar_size, fixed_dollar_size_mixed


@dataclass(frozen=True)
class SizingRule:
    kind: str                       # fixed_dollar | fixed_dollar_mixed | fixed_contract
    risk_usd: float = 0.0
    contracts: int = 1
    max_contracts: int | None = None
    max_micro: int | None = None
    policy: str = "SKIP"
    include_costs_in_risk: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


def contract_spec(costs_cfg: dict, symbol: str) -> ContractSpec:
    ic = costs_cfg["instruments"][symbol]
    return ContractSpec(symbol, float(ic["point_value"]), float(ic["tick_size"]))


def size_trade(rule: SizingRule, stop_distance_points: float | None, costs_cfg: dict, symbol: str,
               cost_per_contract_usd: float = 0.0) -> SizeResult:
    if rule.kind == "fixed_contract":
        return fixed_contract_size(rule.contracts, rule.max_contracts)
    if stop_distance_points is None:
        raise ValueError("fixed-dollar sizing requires a stop distance")
    cost = cost_per_contract_usd if rule.include_costs_in_risk else 0.0
    spec = contract_spec(costs_cfg, symbol)
    if rule.kind == "fixed_dollar":
        return fixed_dollar_size(rule.risk_usd, stop_distance_points, spec, rule.max_contracts, rule.policy, cost)
    if rule.kind == "fixed_dollar_mixed":
        micro = costs_cfg["micro_of"][symbol]["micro"]
        return fixed_dollar_size_mixed(rule.risk_usd, stop_distance_points, spec, contract_spec(costs_cfg, micro),
                                       rule.max_contracts, rule.max_micro, cost, 0.0)
    raise ValueError(f"unknown sizing kind {rule.kind}")


def open_risk_allows(current_open_risk_usd: float, new_trade_risk_usd: float, max_open_risk_usd: float | None) -> bool:
    """True if adding the new trade keeps total open risk within the limit (limit None = unlimited)."""
    if max_open_risk_usd is None:
        return True
    return current_open_risk_usd + new_trade_risk_usd <= max_open_risk_usd + 1e-9
