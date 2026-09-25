"""Generic prop-evaluation account logic on synthetic P&L sequences."""
import pytest
import yaml

from conftest import PROJECT
from quantlab5.prop.account import Day, PropProfile, days_from_trade_pnls, simulate_account
from quantlab5.prop.consistency import consistency_ok
from quantlab5.prop.eod_drawdown import EodTrailing, StaticDrawdown
from quantlab5.prop.intraday_drawdown import IntradayTrailing
from quantlab5.prop.rolling_evaluations import rolling_evaluations, start_indices


def P(**kw):
    base = dict(name="t", start_balance=50_000, profit_target=3_000, max_loss=2_000, drawdown_mode="static",
                min_trading_days=1)
    base.update(kw)
    return PropProfile(**base)


def D(*marks, s="d", contracts=None):
    return Day(s, list(marks), contracts or {})


def test_passes_exactly_at_profit_target():
    r = simulate_account(P(), [D(1000), D(2000)])
    assert r.status == "PASS" and r.day_index == 1 and r.balance == 53_000
    assert simulate_account(P(), [D(1000), D(1999.99)]).status == "INCOMPLETE"


def test_fails_exactly_at_max_loss_threshold():
    r = simulate_account(P(), [D(-500), D(-1500)])
    assert r.status == "FAIL" and r.day_index == 1
    assert simulate_account(P(), [D(-500), D(-1499.99)]).status == "INCOMPLETE"


def test_intraday_mark_breach_fails_even_if_day_recovers():
    assert simulate_account(P(), [D(-2000, 500)]).status == "FAIL"


def test_eod_trailing_rises_with_eod_highs_and_never_moves_back():
    t = EodTrailing(50_000, 2_000)
    seen = []
    for bal in (50_500, 51_000, 50_200, 52_000, 49_000):
        t.on_eod(bal)
        seen.append(t.threshold)
    assert seen == [48_500, 49_000, 49_000, 50_000, 50_000]
    assert all(b >= a for a, b in zip(seen, seen[1:]))


def test_intraday_trailing_follows_intraday_peaks_and_never_moves_back():
    t = IntradayTrailing(50_000, 2_000)
    for eq in (50_300, 51_200, 50_100, 50_900):
        t.on_mark(eq)
    assert t.threshold == 49_200
    t.on_mark(40_000)
    assert t.threshold == 49_200


def test_trail_lock_stops_at_start_plus_offset():
    t = EodTrailing(50_000, 2_000, lock_offset=100)
    t.on_eod(55_000)
    assert t.threshold == 50_100
    assert StaticDrawdown(50_000, 2_000).threshold == 48_000


def test_eod_and_intraday_trailing_produce_different_outcomes():
    # day 1 runs up +1500 intraday, closes +200; day 2 dips to -1000 intraday
    days = [D(1500, 200), D(-1000, 0)]
    eod = simulate_account(P(drawdown_mode="eod"), days)
    intra = simulate_account(P(drawdown_mode="intraday"), days)
    # EOD: threshold after day 1 = 50200 - 2000 = 48200; day 2 low = 49200 -> survives
    assert eod.status == "INCOMPLETE" and eod.thresholds == [48_200, 48_200]
    # intraday: peak 51500 -> threshold 49500; day 2 low 49200 <= 49500 -> FAIL
    assert intra.status == "FAIL" and intra.day_index == 1


def test_consistency_rule_blocks_pass_until_satisfied():
    prof = P(consistency_max_day_fraction=0.5)
    r = simulate_account(prof, [D(2500), D(600)])          # 3100 total, best day 2500 > 50%
    assert r.status == "INCOMPLETE"
    r = simulate_account(prof, [D(2500), D(600), D(1000), D(1000)])   # 5100 total, 2500 <= 2550
    assert r.status == "PASS" and r.day_index == 3
    assert consistency_ok([100], 0, 0.5) is False and consistency_ok([100], 100, None) is True


def test_min_trading_days_and_non_trading_days():
    prof = P(min_trading_days=3)
    r = simulate_account(prof, [D(3500), D(), D(10)])
    assert r.status == "INCOMPLETE" and r.trading_days == 2
    r = simulate_account(prof, [D(3500), D(), D(10), D(10)])
    assert r.status == "PASS" and r.trading_days == 3


def test_daily_loss_limit_halt_or_fail():
    halt = simulate_account(P(daily_loss_limit=500, daily_loss_action="halt_day"), [D(-200, -500, -1500)])
    assert halt.status == "INCOMPLETE" and halt.balance == 49_500
    fail = simulate_account(P(daily_loss_limit=500, daily_loss_action="fail"), [D(-200, -500)])
    assert fail.status == "FAIL" and fail.reason == "daily loss limit"


def test_max_contracts_violation_fails():
    r = simulate_account(P(max_contracts={"NQ": 2}), [D(100, contracts={"NQ": 3})])
    assert r.status == "FAIL" and "max contracts" in r.reason


def test_fixed_dollar_sized_pnl_feeds_the_account(costs_cfg):
    from quantlab5.risk.sizing import SizingRule, size_trade
    rule = SizingRule("fixed_dollar", risk_usd=400)
    size = size_trade(rule, 10.0, costs_cfg, "NQ")           # $200/contract -> 2 contracts
    assert size.contracts == 2
    pv = costs_cfg["instruments"]["NQ"]["point_value"]
    trade_points = [[-10.0], [15.0, 15.0], [30.0, 30.0]]      # stop-outs lose exactly the budget
    pnls = [[p * pv * size.contracts for p in day] for day in trade_points]
    days = days_from_trade_pnls(["d1", "d2", "d3"], pnls)
    assert days[0].marks == [-400.0]
    r = simulate_account(P(), days)
    assert r.status == "PASS" and r.balance == 50_000 - 400 + 1200 + 2400


def test_rolling_start_logic():
    assert start_indices(10, every=3, min_days_remaining=2) == [0, 3, 6]
    assert start_indices(10, every=3, min_days_remaining=5) == [0, 3]
    days = [D(1000, s=f"d{i}") for i in range(6)]
    res = rolling_evaluations(P(), days, every=1, max_days=3, min_days_remaining=1)
    assert [s for s, _sess, _r in res] == [0, 1, 2, 3, 4, 5]
    assert [r.status for _s, _sess, r in res] == ["PASS", "PASS", "PASS", "PASS", "INCOMPLETE", "INCOMPLETE"]
    assert res[2][2].session == "d4"                          # third day of the window starting at d2


def test_generic_profiles_load_from_config():
    cfg = yaml.safe_load((PROJECT / "config" / "prop_profiles.yaml").read_text())
    for name in cfg["profiles"]:
        prof = PropProfile.from_config(cfg, name)
        assert prof.drawdown_mode in ("static", "eod", "intraday")
    with pytest.raises(ValueError):
        simulate_account(P(drawdown_mode="weird"), [D(1)])
