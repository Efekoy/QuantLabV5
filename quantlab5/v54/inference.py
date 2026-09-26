"""Frozen, scalable V5.4 discovery and exact-candidate validation decisions."""
from __future__ import annotations

import numpy as np
from scipy.stats import norm

from quantlab5.v5.holdout_confirmation import hac_mean_se


DISCOVERY_TRADES_MIN = 120
DISCOVERY_ACTIVE_YEARS_MIN = 6
VALIDATION_TRADES_MIN = 40
VALIDATION_ACTIVE_YEARS_MIN = 2
ALPHA = .05
HAC_LAGS = 20


def discovery_qualifies(*, trades: int, active_years: int, net_r: float,
                        stress_net_r: float, matched_excess_r: float) -> bool:
    """Reuse the five exact economic V5 qualifier gates, without Stage A kill."""
    return bool(trades >= DISCOVERY_TRADES_MIN
                and active_years >= DISCOVERY_ACTIVE_YEARS_MIN
                and net_r > 0 and stress_net_r > 0 and matched_excess_r > 0)


def holm_adjust(one_sided_p: np.ndarray) -> np.ndarray:
    """Holm FWER correction valid under arbitrary cross-candidate dependence."""
    p = np.asarray(one_sided_p, float)
    if p.ndim != 1 or np.any(~np.isfinite(p)) or np.any((p < 0) | (p > 1)):
        raise ValueError("Holm requires finite one-sided p-values in [0,1]")
    m = len(p)
    order = np.argsort(p, kind="stable")
    adjusted = np.empty(m, float)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m-rank)*p[i]))
        adjusted[i] = running
    return adjusted


def validation_evidence(daily_net_r: np.ndarray) -> dict:
    """One candidate's day-clustered primary statistic, including zero-trade days."""
    daily = np.asarray(daily_net_r, float)
    if daily.ndim != 1 or len(daily) < 3 or not np.all(np.isfinite(daily)):
        raise ValueError("validation requires a complete finite session-day stream")
    mean, se = hac_mean_se(daily)
    t = mean/se if se > 0 else (np.inf if mean > 0 else -np.inf if mean < 0 else 0.0)
    return {"mean_daily_net_r": float(mean), "hac_se": float(se),
            "unadjusted_one_sided_p": float(norm.sf(t)),
            "upper95_mean_daily_net_r": float(mean+norm.ppf(.95)*se)}


def validation_label(*, adjusted_p: float, trades: int, active_years: int,
                     mean_daily_net_r: float, stress_net_r: float,
                     matched_excess_r: float, upper95_mean_daily_net_r: float) -> str:
    if (adjusted_p <= ALPHA and trades >= VALIDATION_TRADES_MIN
            and active_years >= VALIDATION_ACTIVE_YEARS_MIN
            and mean_daily_net_r > 0 and stress_net_r > 0
            and matched_excess_r > 0):
        return "SUPPORTED"
    if upper95_mean_daily_net_r < 0:
        return "REJECTED"
    return "INCONCLUSIVE / UNDERPOWERED"
