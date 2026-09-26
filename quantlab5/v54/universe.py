"""Outcome-blind, lazy and exactly countable V5.4 strategy grammar.

Every family uses its original V5 SignalContext.direction implementation. The
lookback/threshold surfaces broaden the same executable parameters; E11/E22
have no exposed numeric core axis and therefore have one core variant each.
The 15-bar continuation event inside SignalContext is intentionally fixed:
changing it would require a separate mechanism implementation, not a grid key.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from quantlab5.search.candidate_id import IdScheme, candidate_id
from quantlab5.v5.candidate_inventory import MECHANISMS


# Values are finite, causal, and retain the units in the original family code.
# Thresholds for probability, occupation, ratios, durations and counts have
# distinct ranges; no generic multiplier is spread over incompatible families.
CORE = {
    "E01": ((10, 15, 20, 30, 45, 60), (2, 3, 4, 5, 6)),
    "E02": ((15, 30, 45, 60, 90, 120), (0.75, 1, 1.25, 1.5, 2, 2.5)),
    "E03": ((10, 15, 20, 30, 45, 60, 90), (0.75, 1, 1.25, 1.5, 2, 2.5)),
    "E04": ((None,), (2, 3, 4, 5, 6)),
    "E05": ((10, 15, 20, 30, 45, 60), (5, 10, 15, 20, 30, 45)),
    "E06": ((10, 15, 20, 30, 45, 60), (5, 10, 15, 20, 30)),
    "E07": ((10, 15, 20, 30, 45, 60, 90), (0.6, 0.7, 0.8, 0.9)),
    "E08": ((5, 10, 15, 20, 30), (0.25, 0.4, 0.5, 0.65, 0.8)),
    "E09": ((10, 15, 20, 30, 45, 60), (0.3, 0.45, 0.6, 0.75, 0.9)),
    "E10": ((10, 15, 20, 30, 45, 60), (0.6, 0.7, 0.8, 0.9)),
    "E11": ((None,), (None,)),
    "E12": ((5, 10, 15, 20, 30, 45), (0.6, 0.7, 0.8, 0.9, 0.95)),
    "E13": ((10, 15, 20, 30, 45, 60), (1, 1.5, 2, 2.5, 3)),
    "E14": ((10, 15, 20, 30, 45, 60), (4, 6, 8, 10, 15, 20)),
    "E15": ((None,), (5, 10, 15, 20, 30, 45)),
    "E16": ((30, 45, 60, 90, 120, 180), (1.1, 1.25, 1.5, 1.75, 2)),
    "E17": ((15, 30, 45, 60, 90, 120), (1.1, 1.25, 1.5, 1.75, 2)),
    "E18": ((20, 30, 45, 60, 90, 120), (0.1, 0.15, 0.2, 0.3, 0.4)),
    "E19": ((20, 30, 45, 60, 90, 120), (0.55, 0.6, 0.65, 0.7, 0.8)),
    "E20": ((20, 30, 45, 60, 90, 120), (0.4, 0.5, 0.6, 0.7, 0.8)),
    "E21": ((20, 30, 45, 60, 90, 120), (0.4, 0.5, 0.6, 0.7, 0.8)),
    "E22": ((None,), (None,)),
    "E23": ((20, 30, 45, 60, 90, 120), (1, 1.5, 2, 2.5, 3)),
    "E24": ((10, 15, 20, 30, 45, 60), (0.05, 0.1, 0.15, 0.2, 0.3)),
    "E25": ((10, 15, 20, 30, 45, 60), (2, 3, 4, 5, 6)),
    "E26": ((10, 15, 20, 30, 45, 60), (0.5, 0.65, 0.8, 1, 1.25)),
    "E27": ((20, 30, 45, 60, 90, 120), (1, 1.25, 1.5, 2, 2.5)),
    "E28": ((20, 30, 45, 60, 90, 120), (0.5, 0.65, 0.8, 0.9)),
    "E29": ((20, 30, 45, 60, 90, 120), (0.5, 0.65, 0.8, 0.9)),
    "E30": ((20, 30, 45, 60, 90, 120), (0.2, 0.3, 0.35, 0.45, 0.6)),
}

# Original SignalContext.base_ok admits signals only for next opens 09:35–15:15.
# Thus the existing "globex" and "rth" windows are exactly equivalent for
# every original family. Keep one canonical representative, not two IDs.
SESSIONS = ("rth", "rth_am", "rth_pm")
DIRECTIONS = ("long", "short", "both")
ENTRIES = ("next_open", "delay_one_bar")

# Semantic applicability. Every family has an unfiltered core, three relevant
# single-state screens, and one prespecified two-filter interaction. Contradictory
# states (such as high and low volatility) are never combined.
FILTER_GROUPS = {
    "path": ("vol_high", "eff_high", "volume_high"),
    "regime": ("vol_low", "trend_young", "es_agree"),
    "cross": ("es_agree", "relative_vol_high", "volume_high"),
    "liquidity": ("volume_high", "eff_high", "vol_high"),
    "reversal": ("vol_high", "es_disagree", "trend_old"),
}
FAMILY_GROUP = {
    **{x: "path" for x in ("E01", "E02", "E03", "E06", "E07", "E08", "E15", "E23", "E26", "E27")},
    **{x: "regime" for x in ("E04", "E05", "E14", "E16", "E17", "E19", "E20", "E21", "E22", "E24")},
    **{x: "cross" for x in ("E12", "E13", "E29")},
    **{x: "liquidity" for x in ("E09", "E10", "E18", "E28")},
    **{x: "reversal" for x in ("E11", "E25", "E30")},
}


def filters_for(family: str) -> tuple[tuple[str, ...], ...]:
    a, b, c = FILTER_GROUPS[FAMILY_GROUP[family]]
    return ((), (a,), (b,), (c,), (a, b))


@dataclass(frozen=True)
class Management:
    template: str
    stop: str
    target_r: float | None = None
    breakeven_r: float | None = None
    partial_r: float | None = None
    partial_fraction: float | None = None
    trail_r: float | None = None
    hold: int | str = 60
    mechanism_exit: bool = False

    def as_dict(self) -> dict:
        return self.__dict__.copy()


STOP_ATR = ("atr_0.75", "atr_1", "atr_1.5")
STOP_STRUCTURE = ("signal_bar", "swing_5", "swing_15")
STOPS = STOP_ATR + STOP_STRUCTURE
TARGETS = (0.75, 1.0, 1.5, 2.0, 3.0, 4.0)
BE_LEVELS = (0.75, 1.25)
PARTIAL_LEVELS = (1.0, 1.5)
TRAIL_LEVELS = (1.0, 1.5)
HOLDS = (15, 30, 60, "eod")


def managements() -> tuple[Management, ...]:
    out: list[Management] = []
    # Templates are disjoint by design; each strategy has one stop and one
    # terminal exit, with at most one nonterminal management action of each type.
    out += [Management("T1_FIXED_TARGET", s, target_r=t) for s in STOP_ATR for t in TARGETS]
    out += [Management("T2_STRUCTURE_STOP_FIXED_TARGET", s, target_r=t) for s in STOP_STRUCTURE for t in TARGETS]
    out += [Management("T3_SESSION_RUNNER", s, hold="eod") for s in STOPS]
    out += [Management("T4_BREAKEVEN_TARGET", s, target_r=t, breakeven_r=b)
            for s in STOPS for b in BE_LEVELS for t in TARGETS if t > b]
    out += [Management("T5_PARTIAL_RUNNER", s, partial_r=p, partial_fraction=.5, hold="eod")
            for s in STOPS for p in PARTIAL_LEVELS]
    out += [Management("T6_PARTIAL_BE_RUNNER", s, breakeven_r=b, partial_r=p,
                       partial_fraction=.5, hold="eod")
            for s in STOPS for b in BE_LEVELS for p in PARTIAL_LEVELS if b <= p]
    out += [Management("T7_TRAIL_RUNNER", s, trail_r=t, hold="eod")
            for s in STOPS for t in TRAIL_LEVELS]
    out += [Management("T8_BE_TRAIL_RUNNER", s, breakeven_r=b, trail_r=t, hold="eod")
            for s in STOPS for b in BE_LEVELS for t in TRAIL_LEVELS if b <= t]
    out += [Management("T9_PARTIAL_TRAIL", s, partial_r=p, partial_fraction=.5,
                       trail_r=t, hold="eod")
            for s in STOPS for p in PARTIAL_LEVELS for t in TRAIL_LEVELS if t <= p]
    out += [Management("T10_TIME_EXIT", s, hold=h)
            for s in STOPS for h in HOLDS[:3]]
    out += [Management("T11_MECHANISM_EXIT", s, hold="eod", mechanism_exit=True)
            for s in STOPS]
    keys = [tuple(sorted(x.as_dict().items())) for x in out]
    if len(keys) != len(set(keys)):
        raise AssertionError("management grammar contains duplicate static templates")
    return tuple(out)


def core_for(family: str):
    looks, thresholds = CORE[family]
    yield from product(looks, thresholds)


def signal_configs(family: str):
    for (lookback, threshold), direction, session, filters, entry in product(
            core_for(family), DIRECTIONS, SESSIONS, filters_for(family), ENTRIES):
        yield {"family": family, "lookback": lookback, "threshold": threshold,
               "direction": direction, "session": session,
               "filters": filters, "entry": entry}


def specifications(family: str | None = None):
    """Stream canonical specs without materializing millions of Python dicts."""
    families = (family,) if family else tuple(m.code for m in MECHANISMS)
    mgmt = managements()
    for f in families:
        for signal in signal_configs(f):
            for management in mgmt:
                yield {"grammar": "V5_4_G1", **signal,
                       "management": management.as_dict()}


def counts() -> dict:
    if set(CORE) != {m.code for m in MECHANISMS} or set(FAMILY_GROUP) != set(CORE):
        raise AssertionError("V5.4 must include exactly the original 30 executable families")
    mgmt = managements()
    by_template = {t: sum(x.template == t for x in mgmt)
                   for t in sorted({x.template for x in mgmt})}
    family_core = {f: len(CORE[f][0]) * len(CORE[f][1]) for f in CORE}
    multiplier = len(DIRECTIONS) * len(SESSIONS) * len(ENTRIES)
    family_signal = {f: n * multiplier * len(filters_for(f)) for f, n in family_core.items()}
    family_total = {f: n * len(mgmt) for f, n in family_signal.items()}
    removed_globex = sum(family_core.values()) * len(DIRECTIONS) * len(filters_for("E01")) * len(ENTRIES) * len(mgmt)
    return {"family_core_variants": family_core,
            "family_signal_configs": family_signal,
            "family_total_specs": family_total,
            "signal_configs": sum(family_signal.values()),
            "management_variants": len(mgmt),
            "by_template_per_signal": by_template,
            "by_template_total": {t: n * sum(family_signal.values())
                                  for t, n in by_template.items()},
            "total_specs": sum(family_total.values()),
            "pre_dedup_rth_plus_globex_specs": sum(family_total.values()) + removed_globex,
            "semantic_static_duplicates_removed": removed_globex,
            "static_duplicate_specs": 0,
            "static_duplicate_proof": "unique core tuples, filter tuples, session/direction/entry axes, and disjoint management tuples; canonical Cartesian product"}


def id_for(spec: dict) -> str:
    return candidate_id(spec, IdScheme("Q54", 24, "quantlab5.v54.broad_discovery"))


def spec_at(index: int) -> dict:
    """Recover any canonical specification by row number without an index file."""
    if index < 0 or index >= counts()["total_specs"]:
        raise IndexError(index)
    mgmt = managements()
    for f in CORE:
        family_count = len(CORE[f][0])*len(CORE[f][1])*len(DIRECTIONS)*len(SESSIONS)*len(filters_for(f))*len(ENTRIES)*len(mgmt)
        if index >= family_count:
            index -= family_count
            continue
        signal_index, management_index = divmod(index, len(mgmt))
        entry_index = signal_index % len(ENTRIES)
        signal_index //= len(ENTRIES)
        filter_index = signal_index % len(filters_for(f))
        signal_index //= len(filters_for(f))
        session_index = signal_index % len(SESSIONS)
        signal_index //= len(SESSIONS)
        direction_index = signal_index % len(DIRECTIONS)
        core_index = signal_index // len(DIRECTIONS)
        look_index, threshold_index = divmod(core_index, len(CORE[f][1]))
        return {"grammar": "V5_4_G1", "family": f,
                "lookback": CORE[f][0][look_index],
                "threshold": CORE[f][1][threshold_index],
                "direction": DIRECTIONS[direction_index],
                "session": SESSIONS[session_index],
                "filters": filters_for(f)[filter_index],
                "entry": ENTRIES[entry_index],
                "management": mgmt[management_index].as_dict()}
    raise AssertionError("unreachable row index")


def row_index(spec: dict) -> int:
    """Inverse of spec_at, used for exact local parameter neighbors."""
    f = spec["family"]
    if f not in CORE:
        raise ValueError("unknown family")
    mgmt = managements()
    mgmt_keys = [x.as_dict() for x in mgmt]
    offset = sum(counts()["family_total_specs"][k] for k in CORE if list(CORE).index(k) < list(CORE).index(f))
    look_index = CORE[f][0].index(spec["lookback"])
    threshold_index = CORE[f][1].index(spec["threshold"])
    core_index = look_index*len(CORE[f][1])+threshold_index
    signal_index = (((core_index*len(DIRECTIONS)+DIRECTIONS.index(spec["direction"]))
                    *len(SESSIONS)+SESSIONS.index(spec["session"]))
                    *len(filters_for(f))+filters_for(f).index(tuple(spec["filters"])))
    signal_index = signal_index*len(ENTRIES)+ENTRIES.index(spec["entry"])
    return offset+signal_index*len(mgmt)+mgmt_keys.index(spec["management"])


def core_neighbor_indices(spec: dict) -> tuple[int, ...]:
    """Adjacent lookback or threshold, all other choices exactly held fixed."""
    f = spec["family"]
    looks, thresholds = CORE[f]
    li, ti = looks.index(spec["lookback"]), thresholds.index(spec["threshold"])
    out = []
    for axis, value in (("lookback", looks[li-1] if li > 0 else None),
                        ("lookback", looks[li+1] if li+1 < len(looks) else None),
                        ("threshold", thresholds[ti-1] if ti > 0 else None),
                        ("threshold", thresholds[ti+1] if ti+1 < len(thresholds) else None)):
        if value is not None:
            neighbor = dict(spec)
            neighbor[axis] = value
            out.append(row_index(neighbor))
    return tuple(out)
