"""Cohort prop simulation: sizing, open-risk cap, daily policies, marks, rolling starts."""
import numpy as np

from quantlab5.prop import propsim as P

# Test fixture: the generic EOD profile V4 used (values inlined; V4's config/prereg_v4.yaml is NOT part of V5).
PREREG_FIXTURE = {"prop": {"profiles": {"GENERIC_EVAL_EOD": {
    "start": 50000, "target": 3000, "max_loss": 2000, "mode": "eod", "daily_loss": 1000, "daily_action": "halt_day",
    "consistency": 0.5, "min_days": 5, "trail_lock_offset": 0}}}}


def _tr(sdays, nets, risk=10.0, mae=3.0, t0=None):
    n = len(nets)
    t0 = np.arange(n) * 10 if t0 is None else np.asarray(t0)
    return {"sday": np.asarray(sdays), "net": np.asarray(nets, float), "risk": np.full(n, risk), "mae": np.full(n, mae),
            "ts_entry": t0, "ts_exit": t0 + 5, "dir": np.zeros(n)}


def test_mnq_sizing_and_cost(costs_cfg):
    tr = _tr([1, 1], [5.0, -10.7], risk=10.0)
    s = P.size_trades({"a": tr}, 200.0, costs_cfg)
    assert [t["q"] for t in s] == [10, 10]                       # $20 risk per micro at a 10-pt stop
    cost = P.mnq_cost_usd(costs_cfg)
    assert cost == 2.0
    assert abs(s[0]["pnl"] - 10 * ((5.0 + 0.7) * 2 - 2.0)) < 1e-9
    assert P.size_trades({"a": _tr([1], [1.0], risk=150.0)}, 100.0, costs_cfg) == []   # SKIP: 1 micro = $300


def test_open_risk_cap_and_policies(costs_cfg):
    a = _tr([1, 1, 1], [5, -3, 4], t0=[0, 100, 200])
    b = _tr([1], [2], t0=[2])                                   # overlaps a's first trade
    s = P.size_trades({"a": a, "b": b}, 100.0, costs_cfg)
    assert len(P.cap_open_risk(s, 100.0)) == 3 and len(P.cap_open_risk(s, 200.0)) == 4
    fw = P.apply_policy(s, "stop_after_first_winner", 100.0)
    assert len(fw) == 1
    assert len(P.apply_policy(s, "none", 100.0)) == 4


def test_rolling_prop_on_synthetic_edge():
    prof = P.profiles_from_prereg(PREREG_FIXTURE)["GENERIC_EVAL_EOD"]
    sessions = np.arange(18000, 18300)
    good = [{"sid": "x", "sday": int(s), "t0": int(s) * 100, "t1": int(s) * 100 + 5, "q": 5, "pnl": 120.0,
             "risk": 100.0, "mae": 40.0} for s in sessions]
    res = P.rolling(prof, P.days_from_trades(good, sessions), max_days=120)
    sm = P.summarize(res)
    assert sm["p_pass"] == 1.0 and sm["median_days_to_pass"] == 25          # 3000 / 120 = 25 days
    bad = [dict(t, pnl=-120.0) for t in good]
    assert P.summarize(P.rolling(prof, P.days_from_trades(bad, sessions), 120))["p_fail"] == 1.0
