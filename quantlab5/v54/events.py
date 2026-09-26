"""Cache original V5 family states and V5.4 causal filters before management.

An event is an executable bar open, not a filled trade. Management may suppress
later events while a position is open. Entry and every stop are computed from
information available no later than the entry open.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from quantlab5.engine.execution import get_window, window_arrays
from quantlab5.features import ops as O
from quantlab5.project import default_project
from quantlab5.v5.signals import SignalContext
from quantlab5.v54.universe import CORE, DIRECTIONS, ENTRIES, SESSIONS, STOPS, filters_for


@dataclass(frozen=True)
class Events:
    entry_idx: np.ndarray
    side: np.ndarray
    stop_dist: np.ndarray
    flat_bar: np.ndarray
    family: str
    signal_config: dict
    mechanism_state: np.ndarray | None = None
    years: np.ndarray | None = None


@dataclass(frozen=True)
class PreparedSignal:
    signal_bar_idx: np.ndarray
    entry_idx: np.ndarray
    side: np.ndarray
    flat_bar: np.ndarray
    state: np.ndarray
    config: dict


class EventCache:
    def __init__(self, market, sessions_cfg=None):
        self.market = market
        self.context = SignalContext(market)
        self.years = np.asarray(self.context.calendar_years, np.int32)
        self.sessions_cfg = sessions_cfg or default_project().sessions
        self._filters: dict[str, np.ndarray] = {}
        self._windows: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        self._stops: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    def window(self, name):
        if name not in self._windows:
            self._windows[name] = window_arrays(
                self.market.nq, get_window(self.sessions_cfg, name))
        return self._windows[name]

    def filter(self, name: str) -> np.ndarray:
        if name not in self._filters:
            self._filters[name] = self._make_filter(name)
        return self._filters[name]

    def _make_filter(self, name):
        c = self.context
        m = self.market
        g = m.gid
        if name in ("vol_high", "vol_low"):
            short = O.rmean(np.abs(c.r), 20, g)
            long = O.rmean(np.abs(c.r), 120, g)
            ratio = np.divide(short, long, out=np.full(m.n, np.nan), where=long > 0)
            return (ratio >= 1.25) if name == "vol_high" else (ratio <= .8)
        if name == "volume_high":
            prior = O.lag(O.rmean(np.asarray(m.nq.v, float), 60, g), 1, g)
            return np.asarray(m.nq.v) >= 1.5 * prior
        if name == "eff_high":
            close = np.asarray(m.nq.c, float)
            path = O.rsum(np.abs(np.diff(close, prepend=np.nan)), 15, g)
            displacement = np.abs(close - O.lag(close, 15, g))
            return np.divide(displacement, path, out=np.zeros(m.n), where=path > 0) >= .55
        if name in ("es_agree", "es_disagree"):
            # Signed filters are completed in apply_filters against the signal side.
            return np.asarray(m.evalid, bool) & ~np.asarray(m.es_rw, bool)
        if name == "relative_vol_high":
            nq = O.rmean(np.abs(c.r), 30, g)
            es = O.rmean(np.abs(c.er), 30, g)
            return np.isfinite(nq) & np.isfinite(es) & (nq >= 1.5 * es)
        if name in ("trend_young", "trend_old"):
            trend = np.sign(O.ewm(c.r, 30, g))
            changed = trend != O.lag(trend, 1, g)
            age = O.bars_since(changed, g)
            return (age <= 30) if name == "trend_young" else (age >= 60)
        raise ValueError(f"unknown V5.4 filter {name}")

    def apply_filters(self, state: np.ndarray, filters) -> np.ndarray:
        mask = state != 0
        for name in filters:
            mask &= self.filter(name)
            if name == "es_agree":
                mask &= np.sign(self.context.es_ret15) == state
            elif name == "es_disagree":
                mask &= np.sign(self.context.es_ret15) == -state
        return mask

    def stop_arrays(self, name):
        if name not in STOPS:
            raise ValueError(f"unknown V5.4 stop {name}")
        if name not in self._stops:
            b = self.market.nq
            g = self.market.gid
            if name.startswith("atr_"):
                # Both arrays hold the same distance, sampled from the signal bar.
                distance = self.context.stop * float(name.split("_")[1])
                self._stops[name] = (distance, distance)
            else:
                if name == "signal_bar":
                    low, high = np.asarray(b.l, float), np.asarray(b.h, float)
                else:
                    n = int(name.split("_")[1])
                    low = O.rmin(b.l, n, g)
                    high = O.rmax(b.h, n, g)
                self._stops[name] = (low, high)
        return self._stops[name]

    def signal_events(self, config: dict) -> PreparedSignal:
        family = config["family"]
        if (family not in CORE or config["lookback"] not in CORE[family][0]
                or config["threshold"] not in CORE[family][1]
                or config["direction"] not in DIRECTIONS
                or config["session"] not in SESSIONS
                or config["entry"] not in ENTRIES
                or tuple(config["filters"]) not in filters_for(family)):
            raise ValueError("event request is outside frozen V5.4 signal grammar")
        m, ctx = self.market, self.context
        state = ctx.direction(family, config["lookback"], config["threshold"])
        wanted = config["direction"]
        valid = self.apply_filters(state, config["filters"])
        if wanted == "long":
            valid &= state == 1
        elif wanted == "short":
            valid &= state == -1
        entry_ok, flat = self.window(config["session"])
        delay = 1 if config["entry"] == "next_open" else 2
        candidates = np.flatnonzero(valid)
        candidates = candidates[candidates + delay < m.n]
        entries = candidates + delay
        same = m.gid[candidates] == m.gid[entries]
        # A delayed entry must also remain inside the registered entry window.
        good = same & entry_ok[entries] & ~m.rw[entries]
        candidates, entries = candidates[good], entries[good]
        sides = state[candidates].astype(np.int8)
        return PreparedSignal(candidates.astype(np.int32), entries.astype(np.int32),
                              sides, flat, state, config)

    def events(self, config: dict, stop: str,
               prepared: PreparedSignal | None = None) -> Events:
        prepared = self.signal_events(config) if prepared is None else prepared
        if prepared.config != config:
            raise ValueError("prepared signal belongs to a different configuration")
        candidates, entries, sides = (prepared.signal_bar_idx,
                                      prepared.entry_idx, prepared.side)
        low, high = self.stop_arrays(stop)
        if stop.startswith("atr_"):
            distance = np.asarray(low[candidates], float)
        else:
            open_px = np.asarray(self.market.nq.o)[entries]
            distance = np.where(sides == 1, open_px-low[candidates], high[candidates]-open_px)
        feasible = np.isfinite(distance) & (distance >= .25)
        return Events(entries[feasible].astype(np.int32), sides[feasible],
                      distance[feasible].astype(float), prepared.flat_bar,
                      config["family"], config, prepared.state, self.years)
