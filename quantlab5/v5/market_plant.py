"""Predeclared E03 causal-event market plants for executable power calibration.

The plant chooses event bars from a zero-edge synthetic world using only
completed-bar E03 signals, then changes subsequent NQ OHLC by a fixed R-scaled
drift. It never consults realized trade outcomes when choosing events.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from quantlab5.data.market import Market, build_market
from quantlab5.data.schema import bars_from_arrays
from quantlab5.data.sessions import Window
from quantlab5.engine.execution import run_signals
from quantlab5.search.candidate_id import candidate_id
from quantlab5.v5.candidate_inventory import inventory
from quantlab5.v5.signals import SignalContext, signal_for_spec

EFFECTS_R = (0.05, 0.075, 0.10, 0.15)
FREQUENCIES = (100, 250, 500)
SHAPES = ("isolated_needle", "stable_plateau", "heterogeneous_family", "regime_specific")
WINDOW = Window("v5_rth", 935, 1276, 1315)


@dataclass(frozen=True)
class MarketPlant:
    world: Market
    target_ids: tuple[str, ...]
    selected_decision_bars: np.ndarray
    requested_effect_r: float
    requested_trades_per_year: int
    shape: str
    dose_factor: float = 1.0
    realized_effect_r: float = float("nan")


def realized_plant_effect_r(base: Market, planted: MarketPlant,
                            *, stop: np.ndarray | None = None) -> float:
    """Counterfactual executed R shift on the frozen selected-event mask."""
    if base.n != planted.world.n or not np.array_equal(base.nq.ts, planted.world.nq.ts):
        raise ValueError("plant and baseline calendars differ")
    mask = np.zeros(base.n, bool)
    mask[planted.selected_decision_bars] = True
    stop = SignalContext(base).stop if stop is None else stop
    empty = np.zeros(base.n, bool)
    before = run_signals(base.nq, mask, empty, WINDOW, "long", hold=60,
                         stop_dist=stop, tick=.25)
    after = run_signals(planted.world.nq, mask, empty, WINDOW, "long", hold=60,
                        stop_dist=stop, tick=.25)
    if not before.n or not np.array_equal(before.entry_idx, after.entry_idx):
        raise ValueError("planted counterfactual entry paths differ")
    return float(np.mean((np.asarray(after.points)-np.asarray(before.points))
                         / np.asarray(before.initial_risk)))


def plant_e03_long(base: Market, *, effect_r: float, trades_per_year: int,
                   shape: str, seed: int) -> MarketPlant:
    if effect_r not in EFFECTS_R or trades_per_year not in FREQUENCIES or shape not in SHAPES:
        raise ValueError("plant is outside frozen effects, frequencies or shapes")
    specs = [s for s in inventory()["stage_a"] + inventory()["stage_b"]
             if s["family"] == "E03" and s["side"] == "long"]
    specs.sort(key=lambda s: (s["stage"] != "A", s["variant"]))
    base_spec = next(s for s in specs if s["stage"] == "A")
    context = SignalContext(base)
    masks = np.column_stack([signal_for_spec(base, s, context)[0] for s in specs])
    if shape == "isolated_needle":
        eligible = masks[:, specs.index(base_spec)]
        targets = (base_spec,)
    elif shape == "stable_plateau":
        eligible = masks.sum(axis=1) >= 2
        targets = tuple(specs)
    elif shape == "heterogeneous_family":
        eligible = masks.any(axis=1)
        targets = tuple(specs)
    else:
        eligible = masks[:, specs.index(base_spec)] & (np.abs(context.r) <= 2*context.v)
        targets = (base_spec,)
    eligible &= context.base_ok
    candidates = np.flatnonzero(eligible)
    rng = np.random.default_rng(int(seed))
    years = base.years()
    selected = []
    for year in np.unique(years):
        pool = candidates[years[candidates] == year]
        if not len(pool):
            continue
        sessions = np.unique(np.asarray(base.nq.sday)[years == year]).size
        quota = int(round(trades_per_year * sessions / 252))
        # Random priorities, then chronological non-overlap. Signal eligibility
        # never uses future P&L; the random seed is fixed before outcomes.
        priority = rng.permutation(pool)
        chosen = []
        occupied = np.zeros(base.n, bool)
        for t in priority:
            if occupied[t]:
                continue
            chosen.append(int(t))
            occupied[max(0, t-60):min(t+61, base.n)] = True
            if len(chosen) >= quota:
                break
        selected.extend(chosen)
    globally_spaced = []
    for t in sorted(selected):
        if not globally_spaced or t-globally_spaced[-1] > 60:
            globally_spaced.append(t)
    selected = np.array(globally_spaced, np.int64)
    if not len(selected):
        raise ValueError("plant generated no causal E03 events")
    b = base.nq
    n = base.n
    gid = np.asarray(base.gid)
    sm = np.asarray(b.sm)
    event_rows = []
    for t in selected:
        last = int(min(t+60, n-1))
        while last > t and (gid[last] != gid[t] or sm[last] > 1315):
            last -= 1
        if last <= t:
            continue
        strength = 1.0
        if shape == "heterogeneous_family":
            strength = (0.65, 0.85, 1.0, 1.15)[int(t) % 4]
        event_rows.append((t, strength*float(context.stop[t])/.25, rng.random()))
    old_open, old_close = np.asarray(b.o), np.asarray(b.c)
    up_wick = np.asarray(b.h) - np.maximum(old_open, old_close)
    down_wick = np.minimum(old_open, old_close) - np.asarray(b.l)
    target_ids = tuple(candidate_id(s) for s in targets)

    def build(dose: float) -> MarketPlant:
        bar_drift = np.zeros(n)
        for t, risk_ticks, u in event_rows:
            raw_ticks = dose*effect_r*risk_ticks
            ticks = int(raw_ticks) + int(u < raw_ticks-int(raw_ticks))
            bar_drift[t+1] += ticks*.25
        level_after = np.cumsum(bar_drift)
        level_before = level_after-bar_drift
        new_open = old_open + level_before
        new_close = old_close + level_after
        new_high = np.maximum(new_open, new_close) + up_wick
        new_low = np.minimum(new_open, new_close) - down_wick
        if np.min(new_low) <= 0:
            raise ValueError("plant crossed nonpositive prices")
        nq = bars_from_arrays("NQ", b.ts, new_open, new_high, new_low, new_close,
                              b.v, base.nq_symbols, source=f"plant:e03:{shape}:{effect_r}:{seed}")
        world = build_market(nq, base.es, base.nq_symbols, base.es_symbols)
        return MarketPlant(world, target_ids, selected, effect_r,
                           trades_per_year, shape, dose)

    # The frozen global dose search targets the requested *executed* R shift
    # on these synthetic opportunities. It does not change which events were
    # selected and never uses real market strategy outcomes.
    low, high = 0.0, 1.0
    high_plant = build(high)
    high_effect = realized_plant_effect_r(base, high_plant, stop=context.stop)
    while high_effect < effect_r and high < 32:
        low = high
        high *= 2
        high_plant = build(high)
        high_effect = realized_plant_effect_r(base, high_plant, stop=context.stop)
    if high_effect < effect_r:
        raise ValueError("plant cannot reach requested executed R shift")
    best = (abs(high_effect-effect_r), replace(high_plant, realized_effect_r=high_effect))
    for _ in range(8):
        mid = (low+high)/2
        candidate = build(mid)
        observed = realized_plant_effect_r(base, candidate, stop=context.stop)
        if abs(observed-effect_r) < best[0]:
            best = (abs(observed-effect_r), replace(candidate, realized_effect_r=observed))
        if observed < effect_r:
            low = mid
        else:
            high = mid
    return best[1]
