"""Trade-level tables and generic metrics.

(Copied from quantlab3/engine/metrics.py. V4 changes: import paths; "stressed" ->
"stress"; the trade table takes `Bars`; trade_table records cost scenario columns
for all four scenarios. No metric definition was changed.)

Win rate and profit factor are first-class. Wins/losses and profit factor are
computed on NET (baseline-cost) trade P&L -- the number you would actually
experience -- with the no-cost profit factor reported alongside.

Profit factor is never capped. With no losing trades it is +inf (shown as
"inf"). R-multiples are reported ONLY when the strategy defines an initial risk
(a stop); time-exit strategies have no R.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from quantlab5.data.sessions import months_of_sday, years_of_sday

_MIN_NS = 60_000_000_000


REASON_NAMES = {1: "stop", 2: "target", 3: "time", 4: "session_end", 5: "opposite_signal",
                6: "breakeven_stop", 7: "trailing_stop"}


def trade_table(tr, view, instrument: str, costs, contracts=None) -> pd.DataFrame:
    """One row per trade (`view` is a Bars). `contracts`: per-trade integer size (default 1)."""
    pv = costs.point_value(instrument)
    ts = np.asarray(view.ts)
    sday = np.asarray(view.sday)
    pts = np.asarray(tr.points, dtype=float)
    q = np.ones(len(pts)) if contracts is None else np.asarray(contracts, dtype=float)
    entry_ts = ts[tr.entry_idx]
    # opposite-signal exits fill at a bar OPEN; all others at/inside the bar -> bar end
    exit_ts = ts[tr.exit_idx] + np.where(tr.reason == 5, 0, _MIN_NS)
    cats = [REASON_NAMES[i] for i in range(1, 8)]
    df = pd.DataFrame({
        "entry_time": pd.to_datetime(entry_ts, utc=True),
        "exit_time": pd.to_datetime(exit_ts, utc=True),
        "side": np.asarray(tr.side).astype(np.int8),
        "entry_px": tr.entry_px,
        "exit_px": tr.exit_px,
        "points": pts,
        "contracts": q,
        "gross_usd": q * pts * pv,
        "net_usd": q * (pts * pv - costs.per_trade(instrument, "baseline")),
        "stress_usd": q * (pts * pv - costs.per_trade(instrument, "stress")),
        "moderate_usd": q * (pts * pv - costs.per_trade(instrument, "moderate")),
        "reason": pd.Categorical.from_codes(np.asarray(tr.reason).astype(int) - 1, cats)
        if len(tr.reason) else pd.Categorical([], categories=cats),
        "ambiguous": tr.ambiguous,
        "mae_pts": tr.mae,
        "mfe_pts": tr.mfe,
        "hold_min": (exit_ts - entry_ts) / _MIN_NS,
        "session": sday[tr.entry_idx].astype(np.int32),
    })
    risk = getattr(tr, "risk", None)
    if risk is None:
        risk = getattr(tr, "initial_risk", None)
    if risk is not None and np.isfinite(np.asarray(risk, dtype=float)).any():
        risk = np.asarray(risk, dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            df["risk_pts"] = risk
            df["r_multiple"] = np.where(risk > 0, (df["net_usd"].to_numpy() / q / pv) / risk, np.nan)
            df["gross_r"] = np.where(risk > 0, pts / risk, np.nan)
    for name in ("pts_leg0", "be_moved", "be_stopped", "be_ambiguous", "fills"):
        if hasattr(tr, name):
            df[name] = getattr(tr, name)
    return df


def max_drawdown(pnl: np.ndarray) -> float:
    """Largest peak-to-trough fall of cumulative P&L, starting from 0 equity."""
    if len(pnl) == 0:
        return 0.0
    eq = np.concatenate([[0.0], np.cumsum(pnl)])
    return float(np.max(np.maximum.accumulate(eq) - eq))


def profit_factor(pnl: np.ndarray) -> float:
    gp = float(pnl[pnl > 0].sum())
    gl = float(-pnl[pnl < 0].sum())
    if gl == 0.0:
        return math.inf if gp > 0 else math.nan
    return gp / gl


def longest_losing_streak(pnl: np.ndarray) -> int:
    best = cur = 0
    for x in pnl:
        if x < 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def period_info(view) -> dict:
    tradable = np.asarray(view.tradable)
    sd = np.asarray(view.sday)[tradable]
    if len(sd) == 0:
        return {"years": 0.0, "tradable_bars": 0, "first_session": None, "last_session": None,
                "calendar_years": []}
    yrs = np.unique(years_of_sday(np.unique(sd)))
    return {"years": float((sd.max() - sd.min() + 1) / 365.25), "tradable_bars": int(tradable.sum()),
            "first_session": int(sd.min()), "last_session": int(sd.max()),
            "calendar_years": [int(y) for y in yrs]}


def summarize(df: pd.DataFrame, period: dict, has_stop: bool, point_value: float) -> dict:
    n = len(df)
    net = df["net_usd"].to_numpy() if n else np.zeros(0)
    gross = df["gross_usd"].to_numpy() if n else np.zeros(0)
    stress = df["stress_usd"].to_numpy() if n else np.zeros(0)
    yrs = max(period.get("years", 0.0), 1e-9)
    wins = int((net > 0).sum())
    losses = int((net < 0).sum())
    gp = float(net[net > 0].sum())
    gl = float(-net[net < 0].sum())
    out = {
        "trades": n,
        "trades_per_year": n / yrs,
        "wins": wins,
        "losses": losses,
        "win_rate": wins / n if n else math.nan,
        "gross_profit": gp,
        "gross_loss": gl,
        "profit_factor": profit_factor(net),
        "profit_factor_gross": profit_factor(gross),
        "profit_factor_stress": profit_factor(stress),
        "gross_pnl": float(gross.sum()),
        "net_pnl": float(net.sum()),
        "stress_net_pnl": float(stress.sum()),
        "moderate_net_pnl": float(df["moderate_usd"].sum()) if n and "moderate_usd" in df else 0.0,
        "total_cost_usd": float((gross - net).sum()),
        "avg_trade": float(net.mean()) if n else math.nan,
        "avg_winner": float(net[net > 0].mean()) if wins else math.nan,
        "avg_loser": float(net[net < 0].mean()) if losses else math.nan,
        "best_trade": float(net.max()) if n else math.nan,
        "worst_trade": float(net.min()) if n else math.nan,
        "annual_net_pnl": float(net.sum()) / yrs,
        "max_dd_usd": max_drawdown(net),
        "longest_losing_streak": longest_losing_streak(net),
    }
    out["win_loss_ratio"] = (out["avg_winner"] / -out["avg_loser"]
                             if wins and losses else (math.inf if wins else math.nan))
    if n:
        net_pts = net / point_value
        out["expectancy_pts"] = float(net_pts.mean())
        out["gross_expectancy_pts"] = float(df["points"].mean())
        out["max_dd_pts"] = max_drawdown(net_pts)
        out["expectancy_usd"] = float(net.mean())
        hold = df["hold_min"].to_numpy()
        out["avg_hold_min"] = float(hold.mean())
        out["median_hold_min"] = float(np.median(hold))
        side = df["side"].to_numpy()
        out["long_trades"] = int((side == 1).sum())
        out["short_trades"] = int((side == -1).sum())
        out["long_pnl"] = float(net[side == 1].sum())
        out["short_pnl"] = float(net[side == -1].sum())
        out["avg_mae_pts"] = float(df["mae_pts"].mean())
        out["avg_mfe_pts"] = float(df["mfe_pts"].mean())
        out["ambiguous_bars"] = int(df["ambiguous"].sum())
        out["exposure"] = float(hold.sum()) / max(period.get("tradable_bars", 0), 1)
        out["breakeven_cost_per_trade"] = float(gross.mean())
        mon = months_of_sday(df["session"].to_numpy())
        yr = years_of_sday(df["session"].to_numpy())
        m_net = pd.Series(net).groupby(mon).sum()
        y_net = pd.Series(net).groupby(yr).sum()
        out["positive_months"] = int((m_net > 0).sum())
        out["negative_months"] = int((m_net < 0).sum())
        out["positive_years"] = int((y_net > 0).sum())
        out["negative_years"] = int((y_net < 0).sum())
        out["best_year_net"] = float(y_net.max())
        out["best_month_net"] = float(m_net.max())
        k = max(1, int(math.ceil(0.01 * n)))
        out["top1pct_trades_pnl"] = float(np.sort(net)[::-1][:k].sum())
        if "risk_pts" in df:
            rk = df["risk_pts"].to_numpy()
            out["avg_risk_pts"] = float(np.nanmean(rk))
            out["median_risk_pts"] = float(np.nanmedian(rk))
            out["avg_risk_usd"] = float(np.nanmean(rk)) * point_value
            out["avg_r"] = float(np.nanmean(df["r_multiple"].to_numpy()))
            gr = df["gross_r"].to_numpy()
            out["avg_winner_r"] = float(np.nanmean(gr[net > 0])) if wins else math.nan
            out["avg_loser_r"] = float(np.nanmean(gr[net < 0])) if losses else math.nan
        else:
            for k_ in ("avg_risk_pts", "median_risk_pts", "avg_risk_usd", "avg_r", "avg_winner_r", "avg_loser_r"):
                out[k_] = math.nan
        if "be_moved" in df:
            out["be_moved_trades"] = int(df["be_moved"].sum())
            out["be_stopped_trades"] = int(df["be_stopped"].sum())
            out["be_ambiguous_trades"] = int(df["be_ambiguous"].sum())
        if "pts_leg0" in df:
            leg0 = df["pts_leg0"].to_numpy() * point_value
            out["first_leg_gross_usd"] = float(leg0.sum())
            out["remainder_gross_usd"] = float(gross.sum() - leg0.sum())
        # breakeven win rate implied by the realised average winner / loser (after costs)
        if wins and losses:
            aw, al = out["avg_winner"], -out["avg_loser"]
            out["observed_breakeven_winrate"] = al / (aw + al)
        else:
            out["observed_breakeven_winrate"] = math.nan
    else:
        for k_ in ("expectancy_pts", "gross_expectancy_pts", "max_dd_pts", "expectancy_usd",
                   "avg_hold_min", "median_hold_min", "avg_mae_pts", "avg_mfe_pts", "exposure",
                   "breakeven_cost_per_trade", "best_year_net", "best_month_net", "top1pct_trades_pnl",
                   "avg_r", "avg_risk_pts", "median_risk_pts", "avg_risk_usd", "avg_winner_r", "avg_loser_r",
                   "observed_breakeven_winrate"):
            out[k_] = math.nan
        for k_ in ("long_trades", "short_trades", "ambiguous_bars", "positive_months", "negative_months",
                   "positive_years", "negative_years"):
            out[k_] = 0
        out["long_pnl"] = out["short_pnl"] = 0.0
    return out


def _group_metrics(df: pd.DataFrame, key: np.ndarray, label: str) -> pd.DataFrame:
    rows = []
    net_all = df["net_usd"].to_numpy()
    gross_all = df["gross_usd"].to_numpy()
    side_all = df["side"].to_numpy()
    for k in np.unique(key):
        m = key == k
        net = net_all[m]
        rows.append({
            label: int(k),
            "trades": int(m.sum()),
            "wins": int((net > 0).sum()),
            "win_rate": float((net > 0).mean()),
            "profit_factor": profit_factor(net),
            "gross_pnl": float(gross_all[m].sum()),
            "net_pnl": float(net.sum()),
            "avg_trade": float(net.mean()),
            "max_dd_usd": max_drawdown(net),
            "long_trades": int((side_all[m] == 1).sum()),
            "short_trades": int((side_all[m] == -1).sum()),
        })
    return pd.DataFrame(rows)


def yearly_table(df: pd.DataFrame, years: list[int] | None = None) -> pd.DataFrame:
    if len(df) == 0:
        base = pd.DataFrame(columns=["year", "trades", "wins", "win_rate", "profit_factor", "gross_pnl",
                                     "net_pnl", "avg_trade", "max_dd_usd", "long_trades", "short_trades"])
    else:
        base = _group_metrics(df, years_of_sday(df["session"].to_numpy()), "year")
    if years:
        missing = [y for y in years if y not in set(base["year"].tolist())]
        if missing:
            fill = pd.DataFrame({"year": missing, "trades": 0, "wins": 0, "win_rate": np.nan,
                                 "profit_factor": np.nan, "gross_pnl": 0.0, "net_pnl": 0.0,
                                 "avg_trade": np.nan, "max_dd_usd": 0.0, "long_trades": 0,
                                 "short_trades": 0})
            base = pd.concat([base, fill], ignore_index=True)
    return base.sort_values("year").reset_index(drop=True)


def monthly_table(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) == 0:
        return pd.DataFrame(columns=["month", "trades", "net_pnl"])
    return _group_metrics(df, months_of_sday(df["session"].to_numpy()), "month")


def rolling_12m(monthly: pd.DataFrame) -> pd.DataFrame:
    """Rolling 12-month net P&L and trade count on a continuous month index."""
    if len(monthly) == 0:
        return pd.DataFrame(columns=["month", "net_12m", "trades_12m"])
    m = monthly.set_index("month")
    first, last = int(m.index.min()), int(m.index.max())
    months = []
    y, mo = divmod(first, 100)
    while y * 100 + mo <= last:
        months.append(y * 100 + mo)
        mo += 1
        if mo > 12:
            y, mo = y + 1, 1
    m = m.reindex(months).fillna({"net_pnl": 0.0, "trades": 0})
    return pd.DataFrame({"month": months,
                         "net_12m": m["net_pnl"].rolling(12, min_periods=1).sum().to_numpy(),
                         "trades_12m": m["trades"].rolling(12, min_periods=1).sum().to_numpy()})
