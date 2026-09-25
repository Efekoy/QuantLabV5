"""Intraday trailing drawdown: the threshold follows every intraday equity high."""
from __future__ import annotations

from quantlab5.prop.eod_drawdown import EodTrailing, StaticDrawdown, _Tracker


class IntradayTrailing(_Tracker):
    def on_mark(self, equity: float) -> None:
        if equity > self.peak:
            self.peak = equity
        self._raise_to(self.peak - self.max_loss)


def make_tracker(mode: str, start: float, max_loss: float, lock_offset: float | None) -> _Tracker:
    if mode == "static":
        return StaticDrawdown(start, max_loss)
    if mode == "eod":
        return EodTrailing(start, max_loss, lock_offset)
    if mode == "intraday":
        return IntradayTrailing(start, max_loss, lock_offset)
    raise ValueError(f"unknown drawdown mode {mode!r}")
