"""Prop-evaluation simulation for a cohort.

(Ported unchanged from QuantLabV4 quantlab4/v4/propsim.py, where it implemented the V4 preregistration
`prop` section. In V5 the profiles, risk levels and policies come from the future V5 preregistration.)

Trades arrive per strategy with: session day, entry/exit timestamps, net points (NQ, baseline cost),
risk points (frozen stop distance) and MAE points. Steps:
  1. size in MNQ micros with fixed-dollar risk (quantlab5.risk.fixed_dollar, SKIP if one micro exceeds);
     P&L in dollars = contracts x (gross points x $2 - MNQ round-trip cost); MNQ cost from config/costs.yaml
     (commission placeholder, UNVALIDATED -- disclosed)
  2. portfolio cap: a trade is skipped if simultaneous open risk would exceed max_open_risk
  3. account daily policy (none / stop after -$300 / stop after first winner / stop after +-2R)
  4. intraday marks: before each trade closes, equity is marked at its worst adverse excursion
     (MAE, capped at the stop); then at the realised P&L
  5. rolling evaluations starting on EVERY session, capped at max_days, via quantlab5.prop.account
"""
from __future__ import annotations

import numpy as np

from quantlab5.prop.account import Day, PropProfile, simulate_account
from quantlab5.risk.fixed_dollar import ContractSpec, fixed_dollar_size

MNQ = ContractSpec("MNQ", 2.0, 0.25)
NQ_BASE_COST_PTS = 14.0 / 20.0
POLICIES = ("none", "stop_after_daily_loss_300", "stop_after_first_winner", "stop_after_daily_pm_2R")


def mnq_cost_usd(costs_cfg, scenario="baseline"):
    ic = costs_cfg["instruments"]["MNQ"]
    sc = costs_cfg["scenarios"][scenario]
    return (ic["commission_round_trip"] * sc["commission_mult"]
            + 2 * ic["slippage_ticks_per_side"] * ic["tick_size"] * ic["point_value"] * sc["slippage_mult"])


def size_trades(trades_by_strategy: dict, risk_usd: float, costs_cfg, scenario="baseline") -> list[dict]:
    cost = mnq_cost_usd(costs_cfg, scenario)
    out = []
    for sid, tr in trades_by_strategy.items():
        for k in range(len(tr["net"])):
            r = float(tr["risk"][k])
            if not np.isfinite(r) or r <= 0:
                continue
            sz = fixed_dollar_size(risk_usd, r, MNQ, policy="SKIP", cost_per_contract_usd=0.0)
            if sz.decision != "TRADE":
                continue
            q = sz.contracts
            gross_pts = float(tr["net"][k]) + NQ_BASE_COST_PTS
            out.append({"sid": sid, "sday": int(tr["sday"][k]), "t0": int(tr["ts_entry"][k]), "t1": int(tr["ts_exit"][k]),
                        "q": q, "pnl": q * (gross_pts * MNQ.point_value - cost),
                        "risk": q * np.ceil(r / 0.25) * 0.25 * MNQ.point_value,
                        "mae": q * min(float(tr["mae"][k]), r) * MNQ.point_value})
    out.sort(key=lambda x: (x["t0"], x["sid"]))
    return out


def cap_open_risk(trades: list[dict], max_open_risk: float | None) -> list[dict]:
    if max_open_risk is None:
        return trades
    kept, open_ = [], []
    for t in trades:
        open_ = [o for o in open_ if o["t1"] > t["t0"]]
        if sum(o["risk"] for o in open_) + t["risk"] <= max_open_risk + 1e-9:
            kept.append(t)
            open_.append(t)
    return kept


def apply_policy(trades: list[dict], policy: str, risk_usd: float) -> list[dict]:
    if policy == "none":
        return trades
    out, day, cum, stopped = [], None, 0.0, False
    for t in trades:                      # trades sorted by entry time
        if t["sday"] != day:
            day, cum, stopped = t["sday"], 0.0, False
        if stopped:
            continue
        out.append(t)
        cum += t["pnl"]
        if policy == "stop_after_daily_loss_300" and cum <= -300:
            stopped = True
        elif policy == "stop_after_first_winner" and t["pnl"] > 0:
            stopped = True
        elif policy == "stop_after_daily_pm_2R" and abs(cum) >= 2 * risk_usd:
            stopped = True
        else:
            raise_if_unknown(policy)
    return out


def raise_if_unknown(policy):
    if policy not in POLICIES:
        raise ValueError(policy)


def days_from_trades(trades: list[dict], sessions) -> list[Day]:
    by = {}
    for t in sorted(trades, key=lambda x: x["t1"]):
        by.setdefault(t["sday"], []).append(t)
    days = []
    for s in sessions:
        marks, cum = [], 0.0
        for t in by.get(int(s), []):
            marks.append(cum - t["mae"])
            cum += t["pnl"]
            marks.append(cum)
        q = max((t["q"] for t in by.get(int(s), [])), default=0)
        days.append(Day(str(np.datetime64(int(s), "D")), marks, {"MNQ": q} if q else {}))
    return days


def rolling(profile: PropProfile, days: list[Day], max_days: int = 120, every: int = 1, after_pass_days: int = 60):
    res = []
    for s in range(0, len(days), every):
        win = days[s:s + max_days]
        if len(win) < max_days:
            break                          # a start that cannot run the full window is not counted
        r = simulate_account(profile, win)
        surv = None
        if r.status == "PASS":
            post = days[s + r.day_index + 1: s + r.day_index + 1 + after_pass_days]
            # funded-account survival: same drawdown rules, no target, starting from a fresh balance
            p2 = PropProfile(profile.name + "_funded", profile.start_balance, 10 ** 9, profile.max_loss,
                             profile.drawdown_mode, profile.trail_lock_offset, profile.daily_loss_limit,
                             profile.daily_loss_action, None, 1, profile.max_contracts)
            surv = simulate_account(p2, post).status != "FAIL" if len(post) == after_pass_days else None
        res.append({"start": s, "status": r.status, "day_index": r.day_index, "reason": r.reason,
                    "survived_after_pass": surv, "min_headroom": _min_headroom(r)})
    return res


def _min_headroom(r):
    if not r.balances:
        return None
    return float(min(b - t for b, t in zip(r.balances, r.thresholds)))


def summarize(res: list[dict]) -> dict:
    n = len(res)
    if n == 0:
        return {"n_starts": 0}
    st = np.array([r["status"] for r in res])
    dtp = np.array([r["day_index"] + 1 for r in res if r["status"] == "PASS"], float)
    surv = [r["survived_after_pass"] for r in res if r["survived_after_pass"] is not None]
    return {"n_starts": n, "p_pass": float((st == "PASS").mean()), "p_fail": float((st == "FAIL").mean()),
            "p_incomplete": float((st == "INCOMPLETE").mean()),
            "median_days_to_pass": float(np.median(dtp)) if len(dtp) else None,
            "p90_days_to_pass": float(np.quantile(dtp, 0.9)) if len(dtp) else None,
            "fail_reasons": {k: int(v) for k, v in zip(*np.unique([r["reason"] for r in res if r["status"] == "FAIL"],
                                                                  return_counts=True))} if (st == "FAIL").any() else {},
            "funded_survival_60d": float(np.mean(surv)) if surv else None}


def profiles_from_prereg(pr: dict) -> dict:
    out = {}
    for name, p in pr["prop"]["profiles"].items():
        out[name] = PropProfile(name, p["start"], p["target"], p["max_loss"], p["mode"], p["trail_lock_offset"],
                                p["daily_loss"], p["daily_action"], p["consistency"], p["min_days"],
                                {"MNQ": 50})
    return out
