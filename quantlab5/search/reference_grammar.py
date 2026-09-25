"""REFERENCE ONLY: the V4 strategy grammar "V4G1", ported so that the inherited search kernels, world runner
and their regression tests keep working. It is NOT the V5 strategy catalog (none exists at bootstrap); what
V4 searched with it is documented in the V4 reports kept in the prior-lab archive (docs/). V5 change: IDs use the V5 scheme (Q5/quantlab5).

(V4 docstring follows.) The V4 strategy grammar (frozen with the V4 preregistration).

A RULE candidate = (trigger, direction variant, filter combination, exit template):
  trigger     one of the featurelib triggers (family, name, parameters), a signed event at a bar close
  variant     cont_both | rev_both | cont_long | cont_short | rev_long | rev_short
  filters     none, one filter, or two filters from DIFFERENT filter groups
              (three-filter combinations are NOT searched in V4 campaign 1: see preregistration)
  exit        one of 14 canonical exits (stop 1x/2x volatility unit; T15/T30/T60/T120/EOD/2R/3R)
  instrument  NQ (ES is information only); window rth (entries 09:30-15:30, flat 16:00)

A SYM candidate = (alphabet, length, code, side long|short, exit in SYM_EXITS), no filters.
An ML candidate = (model, target, feature set, quantile, exit), see quantlab5/v4/ml.py.

The enumeration order is fixed: rule candidates by (trigger order, combo order, variant, exit);
then SYM by (alphabet, length, code, side, exit); then ML. IDs are content-derived
(quantlab5.search.candidate_id) and do not depend on the order.
"""
from __future__ import annotations

import hashlib

from quantlab5.search.candidate_id import IdScheme, candidate_id
from quantlab5.features.library import SYM_SPECS
from quantlab5.search.kernel import VARIANTS
from quantlab5.engine.outcomes import EXIT_IDS

GRAMMAR_NAME = "V4G1"
SCHEME = IdScheme("Q5", 24, "quantlab5")
SYM_EXITS = (0, 1, 2, 4)            # S1_T15, S1_T30, S1_T60, S1_EOD


def filter_combos(filters) -> list[tuple[int, ...]]:
    """[()] + singles + cross-group pairs, in a fixed order. `filters` = WorldFeatures.filters."""
    out: list[tuple[int, ...]] = [()]
    out += [(f.bit,) for f in filters]
    for i, a in enumerate(filters):
        for b in filters[i + 1:]:
            if a.group != b.group:
                out.append((a.bit, b.bit))
    return out


def combo_masks(combos):
    import numpy as np
    m = np.zeros(len(combos), np.uint64)
    for i, cb in enumerate(combos):
        for bit in cb:
            m[i] |= np.uint64(1) << np.uint64(bit)
    return m


def rule_spec(trigger, variant: str, combo_fids: list[str], exit_id: str) -> dict:
    return {"grammar": GRAMMAR_NAME, "kind": "RULE", "family": trigger.family, "trigger": trigger.tid,
            "variant": variant, "filters": sorted(combo_fids), "exit": exit_id, "instrument": "NQ", "window": "rth"}


def sym_spec(alphabet: str, length: int, code: int, side: str, exit_id: str) -> dict:
    return {"grammar": GRAMMAR_NAME, "kind": "SYM", "family": "SYM", "alphabet": alphabet, "length": int(length),
            "code": int(code), "side": side, "exit": exit_id, "instrument": "NQ", "window": "rth"}


def sym_codes(alphabet: str, length: int) -> int:
    sp = SYM_SPECS[alphabet]
    A = sp["ret_levels"] * sp["vol_levels"] * sp["loc_levels"]
    return A ** length


def counts(triggers, filters) -> dict:
    combos = filter_combos(filters)
    per_family: dict[str, int] = {}
    for t in triggers:
        per_family[t.family] = per_family.get(t.family, 0) + len(combos) * len(VARIANTS) * len(EXIT_IDS)
    sym = sum(sym_codes(a, L) for a, sp in SYM_SPECS.items() for L in sp["lengths"]) * 2 * len(SYM_EXITS)
    per_family["SYM"] = sym
    return {"n_triggers": len(triggers), "n_filters": len(filters), "n_combos": len(combos),
            "n_variants": len(VARIANTS), "n_exits": len(EXIT_IDS), "per_family": per_family,
            "rule_total": sum(v for k, v in per_family.items() if k != "SYM"), "sym_total": sym,
            "total": sum(per_family.values())}


def iter_rule_specs(triggers, filters):
    combos = filter_combos(filters)
    fid = {f.bit: f.fid for f in filters}
    for ti, t in enumerate(triggers):
        for ci, cb in enumerate(combos):
            names = [fid[b] for b in cb]
            for vi, v in enumerate(VARIANTS):
                for ei, e in enumerate(EXIT_IDS):
                    yield (ti, ci, vi, ei), rule_spec(t, v, names, e)


def iter_sym_specs():
    for a, sp in SYM_SPECS.items():
        for L in sp["lengths"]:
            for code in range(sym_codes(a, L)):
                for side in ("long", "short"):
                    for ei in SYM_EXITS:
                        yield (a, L, code, side, ei), sym_spec(a, L, code, side, EXIT_IDS[ei])


def enumeration_fingerprint(triggers, filters, extra_specs=()) -> dict:
    """SHA-256 over the ordered candidate IDs of the whole grammar (streamed), plus the count."""
    h = hashlib.sha256()
    n = 0
    seen_probe = set()
    for gen in (iter_rule_specs(triggers, filters), iter_sym_specs(), ((None, s) for s in extra_specs)):
        for _k, spec in gen:
            cid = candidate_id(spec, SCHEME)
            h.update(cid.encode())
            h.update(b"\n")
            n += 1
            if n % 997 == 0:                      # cheap duplicate probe on a deterministic sample
                if cid in seen_probe:
                    raise ValueError(f"duplicate candidate id {cid}")
                seen_probe.add(cid)
    return {"n_candidates": n, "ordered_id_sha256": h.hexdigest()}
