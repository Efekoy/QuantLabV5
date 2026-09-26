"""Outcome-blind, deterministic V5 A/B/C search-space accounting.

This module enumerates specifications. It does not claim their market signals
are implemented; the inventory is a necessary prerequisite for that work.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from quantlab5.search.candidate_id import candidate_id


@dataclass(frozen=True)
class Mechanism:
    code: str
    lookback: int | None
    threshold: float | None
    requires_c15: bool
    already_occupation: bool = False
    c15_interaction: bool = False


# One primary lookback and one primary magnitude threshold per mechanism.
# None is an inapplicable B axis, not an invitation to tune another parameter.
MECHANISMS = (
    Mechanism("E01", 20, 3, True),
    Mechanism("E02", 60, 1.5, False, c15_interaction=True),
    Mechanism("E03", 20, 1.5, True),
    Mechanism("E04", None, 4, True),
    Mechanism("E05", 30, 20, True),
    Mechanism("E06", 30, 15, True),
    Mechanism("E07", 30, 0.8, True, True),
    Mechanism("E08", 10, 0.5, False),
    Mechanism("E09", 30, 0.6, True),
    Mechanism("E10", 15, 0.8, True),
    Mechanism("E11", None, None, True),
    Mechanism("E12", 15, 0.9, True),
    Mechanism("E13", 20, 2, False, c15_interaction=True),
    Mechanism("E14", 30, 10, True),
    Mechanism("E15", None, 20, True),
    Mechanism("E16", 120, 1.5, True),
    Mechanism("E17", 60, 1.5, True),
    Mechanism("E18", 60, 0.2, True),
    Mechanism("E19", 60, 0.65, True),
    Mechanism("E20", 60, 0.6, True),
    Mechanism("E21", 60, 0.6, True),
    Mechanism("E22", None, None, True, True),
    Mechanism("E23", 60, 2, True),
    Mechanism("E24", 30, 0.15, True),
    Mechanism("E25", 20, 3, True),
    Mechanism("E26", 30, 0.8, True),
    Mechanism("E27", 60, 1.5, True),
    Mechanism("E28", 60, 0.8, True),
    Mechanism("E29", 60, 0.8, True),
    Mechanism("E30", 60, 0.35, False),
)


def variants(m: Mechanism) -> tuple[dict, ...]:
    """Baseline plus one-factor half/double or 0.75/1.25 adjustments."""
    out = [dict(variant="base", lookback=m.lookback, threshold=m.threshold)]
    if m.lookback is not None:
        # Bar/session lookbacks are integers; half of 15 is rounded up to 8.
        out += [dict(variant="lookback_half", lookback=(m.lookback + 1) // 2, threshold=m.threshold),
                dict(variant="lookback_double", lookback=m.lookback * 2, threshold=m.threshold)]
    if m.threshold is not None:
        out.append(dict(variant="threshold_low", lookback=m.lookback, threshold=m.threshold * .75))
        high = m.threshold * 1.25
        if m.code not in {"E10", "E12", "E18", "E28", "E29"} or high <= 1:
            out.append(dict(variant="threshold_high", lookback=m.lookback, threshold=high))
    return tuple(out)


def specification(m: Mechanism, side: str, variant: dict, *, stage: str,
                  interaction: str | None = None) -> dict:
    if side not in ("long", "short") or stage not in ("A", "B", "C"):
        raise ValueError("bad side or stage")
    return {"grammar": "V5G1_REVIEW", "family": m.code, "side": side,
            "stage": stage, "variant": variant["variant"],
            "lookback": variant["lookback"], "threshold": variant["threshold"],
            "interaction": interaction, "entry": "next_bar_open",
            "exit": "60m_or_1555", "stop": "prior_completed_15m_atr"}


def stage_c_interactions(m: Mechanism) -> tuple[str, ...]:
    """Only the preregistered conditional interactions, in canonical order."""
    out = ["previous_rth_open"]
    if not m.already_occupation:
        out.append("occupation")
    if m.c15_interaction:
        out.append("c15")
    return tuple(out)


def stage_c_spec(winner: dict, interaction: str) -> dict:
    """Bind one conditional C child to an actual B winner, never a placeholder."""
    if winner.get("stage") != "B":
        raise ValueError("Stage C parent must be a Stage B winner")
    m = next((x for x in MECHANISMS if x.code == winner.get("family")), None)
    if m is None or interaction not in stage_c_interactions(m):
        raise ValueError("interaction is not preregistered for this family")
    allowed = (specification(m, side, v, stage="B")
               for side in ("long", "short") for v in variants(m)[1:])
    if winner not in allowed:
        raise ValueError("parent is not in the frozen Stage B inventory")
    child = dict(winner)
    child.update(stage="C", interaction=interaction, parent_id=candidate_id(winner))
    return child


def stage_a_expansion_gate(*, adjusted_family_p: float, trades: int,
                           active_years: int, stress_net: float,
                           matched_excess: float) -> bool:
    """The only Stage A to B activation rule; no count or rank cap."""
    return bool(0 <= adjusted_family_p <= .10 and trades >= 120
                and active_years >= 6 and stress_net > 0 and matched_excess > 0)


def activated_inventory(eligible_families, b_winners: dict[str, dict]) -> dict:
    """Materialize every conditional B/C member for a frozen A gate outcome.

    Evidence calculation is the caller's responsibility. This pure transition
    never truncates eligible families or B members by score or rank. C has at
    most one preregistered B parent per family; every B member remains recorded.
    """
    eligible = frozenset(eligible_families)
    known = {m.code for m in MECHANISMS}
    if not eligible <= known or not set(b_winners) <= eligible:
        raise ValueError("unknown or ineligible family")
    full = inventory()
    b = tuple(s for s in full["stage_b"] if s["family"] in eligible)
    c = []
    for family in sorted(b_winners):
        winner = b_winners[family]
        if winner.get("family") != family or winner not in b:
            raise ValueError("winner must be an activated Stage B member of its family")
        mechanism = next(m for m in MECHANISMS if m.code == family)
        c.extend(stage_c_spec(winner, interaction) for interaction in stage_c_interactions(mechanism))
    ids = [candidate_id(s) for s in b + tuple(c)]
    if len(ids) != len(set(ids)):
        raise ValueError("conditional inventory contains duplicate IDs")
    return {"stage_b": b, "stage_c": tuple(c)}


def inventory() -> dict:
    if len(MECHANISMS) != 30 or len({m.code for m in MECHANISMS}) != 30:
        raise ValueError("expected 30 unique mechanisms")
    stage_a = []
    stage_b = []
    # C is a conditional maximum: one actual B winner per family may generate
    # these children after discovery scoring. E08/E30 already depend on an
    # earlier C15 recovery; adding C15 again at recovery is not a new rule.
    stage_c_max = []
    for m in MECHANISMS:
        vv = variants(m)
        if len({(v["lookback"], v["threshold"]) for v in vv}) != len(vv):
            raise ValueError(f"duplicate B parameters: {m.code}")
        for side in ("long", "short"):
            stage_a.append(specification(m, side, vv[0], stage="A"))
            for v in vv[1:]:
                stage_b.append(specification(m, side, v, stage="B"))
        for interaction in stage_c_interactions(m) if len(vv) > 1 else ():
            # The winner is selected from all A/B directions and variants.
            # This placeholder is an inventory slot, not a generated rule.
            stage_c_max.append({"family": m.code, "interaction": interaction})
    stage_c_universe = [stage_c_spec(s, interaction)
                        for s in stage_b
                        for interaction in stage_c_interactions(
                            next(m for m in MECHANISMS if m.code == s["family"]))]
    ids = [candidate_id(s) for s in stage_a + stage_b + stage_c_universe]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate A/B/C candidate ID")
    h = sha256("\n".join(ids[:len(stage_a) + len(stage_b)]).encode()).hexdigest()
    return {"stage_a": stage_a, "stage_b": stage_b,
            "stage_c_max_slots": stage_c_max, "stage_c_universe": stage_c_universe,
            "counts": {"A": len(stage_a), "B_max": len(stage_b),
                       "C_max": len(stage_c_max),
                       "B_C_max": len(stage_b) + len(stage_c_max),
                       "total_max": len(stage_a) + len(stage_b) + len(stage_c_max),
                       "C_conditional_id_universe": len(stage_c_universe),
                       "total_id_universe": len(ids)},
            "ab_ordered_id_sha256": h}
