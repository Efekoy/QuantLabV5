"""Rolling evaluation starts: run an independent account from many start days.

Start logic (deterministic):
  * candidate starts are day indices 0, every, 2*every, ... ;
  * a start is used only if at least `min_days_remaining` days remain after it
    (an evaluation that cannot possibly finish is not counted as a failure);
  * each evaluation sees only days[start : start + max_days] (max_days None = to the end);
  * evaluations are independent -- no state carries over between starts.
"""
from __future__ import annotations

from quantlab5.prop.account import AccountResult, Day, PropProfile, simulate_account


def start_indices(n_days: int, every: int = 1, min_days_remaining: int = 1) -> list[int]:
    if every < 1 or min_days_remaining < 1:
        raise ValueError("every and min_days_remaining must be >= 1")
    return [s for s in range(0, n_days, every) if n_days - s >= min_days_remaining]


def rolling_evaluations(profile: PropProfile, days: list[Day], every: int = 1, max_days: int | None = None,
                        min_days_remaining: int = 1) -> list[tuple[int, str, AccountResult]]:
    out = []
    for s in start_indices(len(days), every, min_days_remaining):
        window = days[s:] if max_days is None else days[s:s + max_days]
        out.append((s, days[s].session, simulate_account(profile, window)))
    return out
