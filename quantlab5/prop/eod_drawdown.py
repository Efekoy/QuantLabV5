"""Drawdown threshold trackers. A threshold only ever RISES (never moves backwards).

  StaticDrawdown    threshold = start - max_loss, fixed
  EodTrailing       threshold follows the highest END-OF-DAY balance (updated at EOD only)
  IntradayTrailing  threshold follows the highest intraday equity mark (updated every mark)

Optional lock: once the trailing threshold would pass `start + lock_offset`, it stays
there (common "trail stops at starting balance" style rule). Breach = equity <= threshold.
"""
from __future__ import annotations


class _Tracker:
    def __init__(self, start: float, max_loss: float, lock_offset: float | None = None):
        if max_loss <= 0:
            raise ValueError("max_loss must be > 0")
        self.start = float(start)
        self.max_loss = float(max_loss)
        self.lock_level = None if lock_offset is None else self.start + float(lock_offset)
        self.threshold = self.start - self.max_loss
        self.peak = self.start

    def _raise_to(self, candidate: float) -> None:
        if self.lock_level is not None:
            candidate = min(candidate, self.lock_level)
        if candidate > self.threshold:          # monotone: never lowers
            self.threshold = candidate

    def on_mark(self, equity: float) -> None:
        pass

    def on_eod(self, balance: float) -> None:
        pass

    def breached(self, equity: float) -> bool:
        return equity <= self.threshold + 1e-9


class StaticDrawdown(_Tracker):
    def __init__(self, start: float, max_loss: float, lock_offset: float | None = None):
        super().__init__(start, max_loss, None)


class EodTrailing(_Tracker):
    def on_eod(self, balance: float) -> None:
        if balance > self.peak:
            self.peak = balance
        self._raise_to(self.peak - self.max_loss)
