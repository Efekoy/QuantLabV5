"""Fixed-contract sizing (the V2/V3 default: one normalised contract), capped."""
from __future__ import annotations

from quantlab5.risk.fixed_dollar import SizeResult


def fixed_contract_size(contracts: int, max_contracts: int | None = None) -> SizeResult:
    if contracts < 0:
        raise ValueError("contracts must be >= 0")
    n = contracts if max_contracts is None else min(contracts, max_contracts)
    if n == 0:
        return SizeResult("SKIP", 0, 0, 0, 0.0, 0.0, 0.0, False, "zero contracts")
    return SizeResult("TRADE", n, 0, 0, 0.0, 0.0, 0.0, False,
                      "fixed contracts" + ("" if n == contracts else f" capped at {max_contracts}"))
