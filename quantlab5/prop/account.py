"""Generic prop-evaluation account simulator (no firm is hard-coded).

Profiles come from config/prop_profiles.yaml. Input is a sequence of trading days,
each with a path of intraday equity MARKS (cumulative day P&L in dollars, including
open-trade P&L, in time order) and the contracts used. The last mark is the day's
realised P&L (positions are flat at session end).

Rules, in order, at each mark:
  1. trailing threshold update (intraday mode only; the threshold never falls)
  2. breach: equity <= threshold -> FAIL (a touch of the threshold fails)
  3. daily loss limit: day P&L <= -limit -> FAIL, or halt the day at that mark
At end of day:
  4. EOD trailing update; trading-day count; day P&L recorded
  5. PASS if balance >= start + target (a touch passes) AND trading days >= minimum
     AND the consistency rule holds; otherwise continue.
A day using more contracts than allowed FAILS. Risk per trade and open risk are
checked by quantlab5.risk before trades reach the account.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from quantlab5.prop.consistency import consistency_ok
from quantlab5.prop.intraday_drawdown import make_tracker


@dataclass(frozen=True)
class PropProfile:
    name: str
    start_balance: float
    profit_target: float
    max_loss: float
    drawdown_mode: str
    trail_lock_offset: float | None = None
    daily_loss_limit: float | None = None
    daily_loss_action: str = "halt_day"
    consistency_max_day_fraction: float | None = None
    min_trading_days: int = 1
    max_contracts: dict = field(default_factory=dict)
    max_open_risk_usd: float | None = None
    risk_per_trade_usd: float | None = None

    @classmethod
    def from_config(cls, cfg: dict, name: str) -> "PropProfile":
        p = dict(cfg["profiles"][name])
        return cls(name=name, **p)


@dataclass
class Day:
    session: str
    marks: list[float]                  # cumulative intraday P&L marks (USD)
    contracts: dict = field(default_factory=dict)   # symbol -> max contracts used that day

    @property
    def traded(self) -> bool:
        return len(self.marks) > 0


@dataclass
class AccountResult:
    status: str                         # PASS | FAIL | INCOMPLETE
    reason: str
    day_index: int | None
    session: str | None
    balance: float
    trading_days: int
    thresholds: list[float]             # threshold after each day
    balances: list[float]


def simulate_account(profile: PropProfile, days: list[Day]) -> AccountResult:
    start = float(profile.start_balance)
    tr = make_tracker(profile.drawdown_mode, start, profile.max_loss, profile.trail_lock_offset)
    balance = start
    trading_days = 0
    day_pnls: list[float] = []
    thresholds, balances = [], []

    def done(status, reason, i, sess):
        return AccountResult(status, reason, i, sess, balance, trading_days, thresholds, balances)

    for i, d in enumerate(days):
        for sym, n in (d.contracts or {}).items():
            cap = (profile.max_contracts or {}).get(sym)
            if cap is not None and n > cap:
                return done("FAIL", f"max contracts exceeded ({sym} {n} > {cap})", i, d.session)
        realised = 0.0
        for m in d.marks:
            eq = balance + m
            tr.on_mark(eq)
            if tr.breached(eq):
                balance = eq
                return done("FAIL", f"drawdown threshold {tr.threshold:.2f} breached", i, d.session)
            if profile.daily_loss_limit is not None and m <= -float(profile.daily_loss_limit) + 1e-9:
                if profile.daily_loss_action == "fail":
                    balance = eq
                    return done("FAIL", "daily loss limit", i, d.session)
                realised = m
                break
            realised = m
        balance += realised
        if d.traded:
            trading_days += 1
            day_pnls.append(realised)
        tr.on_eod(balance)
        if tr.breached(balance):
            return done("FAIL", f"drawdown threshold {tr.threshold:.2f} breached at end of day", i, d.session)
        thresholds.append(tr.threshold)
        balances.append(balance)
        if (balance >= start + profile.profit_target - 1e-9 and trading_days >= profile.min_trading_days
                and consistency_ok(day_pnls, balance - start, profile.consistency_max_day_fraction)):
            return done("PASS", "profit target reached", i, d.session)
    return done("INCOMPLETE", "ran out of days", None, None)


def days_from_trade_pnls(sessions: list[str], trade_pnls: list[list[float]]) -> list[Day]:
    """Build Day paths from closed-trade P&L only (no open-trade marks): the mark after each trade."""
    out = []
    for s, pnls in zip(sessions, trade_pnls):
        marks, cum = [], 0.0
        for p in pnls:
            cum += float(p)
            marks.append(cum)
        out.append(Day(s, marks))
    return out
