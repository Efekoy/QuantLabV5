"""Fixed-dollar sizing: exact integer contracts, never above budget, SKIP when one contract is too big."""
import pytest

from quantlab5.risk.fixed_contract import fixed_contract_size
from quantlab5.risk.fixed_dollar import ContractSpec, fixed_dollar_size, fixed_dollar_size_mixed, stop_ticks
from quantlab5.risk.sizing import SizingRule, open_risk_allows, size_trade

NQ = ContractSpec("NQ", 20.0, 0.25)     # $5 / tick
MNQ = ContractSpec("MNQ", 2.0, 0.25)    # $0.50 / tick
ES = ContractSpec("ES", 50.0, 0.25)     # $12.50 / tick


@pytest.mark.parametrize("risk,stop,spec,expect", [
    (1000, 10.0, NQ, 5),          # $200/contract -> exactly 5
    (999.99, 10.0, NQ, 4),        # one cent short of 5 -> 4 (never round up)
    (1000, 10.01, NQ, 4),         # stop rounds UP to 10.25 -> $205 -> 4
    (1000, 10.25, NQ, 4),
    (1000, 0.25, NQ, 200),        # 1 tick
    (1250, 5.0, ES, 5),           # $250/contract
    (1249, 5.0, ES, 4),
    (100, 10.0, MNQ, 5),          # $20/micro
])
def test_rounding_is_exact_and_conservative(risk, stop, spec, expect):
    r = fixed_dollar_size(risk, stop, spec)
    assert r.decision == "TRADE" and r.contracts == expect
    assert r.total_risk_usd <= risk + 1e-9


def test_float_edge_cases_do_not_misround():
    # 0.1 + 0.2 style issues: 3 x $0.10-per-point style specs must not lose a contract
    spec = ContractSpec("X", 0.1, 0.1)                      # 1 cent per tick
    assert fixed_dollar_size(0.3, 0.1, spec).contracts == 30
    assert stop_ticks(0.3, 0.1) == 3 and stop_ticks(0.30000000001, 0.1) == 4


def test_skip_when_one_contract_exceeds_budget_and_min_one_is_explicit():
    r = fixed_dollar_size(150, 10.0, NQ)                    # $200 per contract > $150
    assert r.decision == "SKIP" and r.contracts == 0 and r.total_risk_usd == 0
    r = fixed_dollar_size(150, 10.0, NQ, policy="MIN_ONE")
    assert r.decision == "TRADE" and r.contracts == 1 and r.exceeds_budget


def test_cap_and_costs_in_risk():
    assert fixed_dollar_size(10_000, 1.0, NQ, max_contracts=3).contracts == 3
    assert fixed_dollar_size(10_000, 1.0, NQ, max_contracts=0).decision == "SKIP"
    # $4 commission counted in risk: $200 + $4 -> 1000 // 204 = 4
    assert fixed_dollar_size(1000, 10.0, NQ, cost_per_contract_usd=4.0).contracts == 4


def test_mixed_standard_then_micro_never_exceeds_budget():
    r = fixed_dollar_size_mixed(1000, 15.0, NQ, MNQ)        # NQ $300, MNQ $30
    assert (r.contracts, r.micro_contracts) == (3, 3) and r.total_risk_usd == 990.0
    r = fixed_dollar_size_mixed(250, 15.0, NQ, MNQ)
    assert (r.contracts, r.micro_contracts) == (0, 8) and r.total_risk_usd == 240.0
    r = fixed_dollar_size_mixed(20, 15.0, NQ, MNQ)
    assert r.decision == "SKIP"
    r = fixed_dollar_size_mixed(1000, 15.0, NQ, MNQ, max_standard=1, max_micro=5)
    assert (r.contracts, r.micro_contracts) == (1, 5)


def test_invalid_inputs_raise():
    for bad in ((0, 10.0), (-5, 10.0), (100, 0.0), (100, -1.0)):
        with pytest.raises(ValueError):
            fixed_dollar_size(bad[0], bad[1], NQ)


def test_rules_from_config_and_open_risk(costs_cfg):
    r = size_trade(SizingRule("fixed_dollar", risk_usd=500), 10.0, costs_cfg, "NQ")
    assert r.contracts == 2
    r = size_trade(SizingRule("fixed_dollar_mixed", risk_usd=500), 10.0, costs_cfg, "NQ")
    assert (r.contracts, r.micro_contracts) == (2, 5)
    assert size_trade(SizingRule("fixed_contract", contracts=3, max_contracts=2), None, costs_cfg, "NQ").contracts == 2
    with pytest.raises(ValueError):
        size_trade(SizingRule("fixed_dollar", risk_usd=500), None, costs_cfg, "NQ")
    assert fixed_contract_size(0).decision == "SKIP"
    assert open_risk_allows(600, 400, 1000) and not open_risk_allows(600, 400.01, 1000)
    assert open_risk_allows(10**9, 1, None)
