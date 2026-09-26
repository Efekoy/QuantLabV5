from quantlab5.search.candidate_id import candidate_id
import pytest

from quantlab5.v5.candidate_inventory import (MECHANISMS, activated_inventory, inventory,
                                              stage_a_expansion_gate, stage_c_spec,
                                              variants)


def test_inventory_counts_and_unique_ids():
    x = inventory()
    assert x["counts"] == {"A": 60, "B_max": 214, "C_max": 57,
                           "B_C_max": 271, "total_max": 331,
                           "C_conditional_id_universe": 436, "total_id_universe": 710}
    ids = [candidate_id(s) for s in x["stage_a"] + x["stage_b"] + x["stage_c_universe"]]
    assert len(ids) == len(set(ids))
    assert len({s["family"] for s in x["stage_a"]}) == 30


def test_b_variants_change_only_one_axis_and_omit_inapplicable_axes():
    for m in MECHANISMS:
        vv = variants(m)
        base = vv[0]
        for v in vv[1:]:
            assert sum(v[k] != base[k] for k in ("lookback", "threshold")) == 1
        if m.lookback is None:
            assert not any(v["variant"].startswith("lookback") for v in vv)
        if m.threshold is None:
            assert not any(v["variant"].startswith("threshold") for v in vv)
        if m.code == "E12":
            assert not any(v["variant"] == "threshold_high" for v in vv)


def test_stage_c_occupation_duplicate_is_excluded():
    x = inventory()
    assert not any(s["family"] in {"E07", "E22"} and s["interaction"] == "occupation"
                   for s in x["stage_c_max_slots"])


def test_c15_interaction_applies_only_to_standalone_events():
    x = inventory()
    assert {s["family"] for s in x["stage_c_max_slots"] if s["interaction"] == "c15"} == {"E02", "E13"}
    parent = next(s for s in x["stage_b"] if s["family"] == "E02")
    child = stage_c_spec(parent, "c15")
    assert child["parent_id"] == candidate_id(parent) and child["stage"] == "C"
    with pytest.raises(ValueError):
        stage_c_spec(parent, "invalid")
    with pytest.raises(ValueError):
        stage_c_spec(x["stage_a"][0], "c15")


def test_expansion_gate_is_conjunction_without_family_count_cap():
    kw = dict(adjusted_family_p=.099, trades=120, active_years=6,
              stress_net=.01, matched_excess=.01)
    assert all(stage_a_expansion_gate(**kw) for _ in range(1000))
    for name, value in (("adjusted_family_p", .101), ("trades", 119),
                        ("active_years", 5), ("stress_net", 0), ("matched_excess", 0)):
        assert not stage_a_expansion_gate(**{**kw, name: value})


def test_all_eligible_families_expand_without_rank_cap_and_c_is_conditional():
    x = inventory()
    winners = {m.code: next(s for s in x["stage_b"] if s["family"] == m.code)
               for m in MECHANISMS if len(variants(m)) > 1}
    full = activated_inventory((m.code for m in MECHANISMS), winners)
    assert len(full["stage_b"]) == 214
    assert len(full["stage_c"]) == 57
    assert len(activated_inventory((), {})["stage_b"]) == 0
    one = activated_inventory(("E02",), {"E02": winners["E02"]})
    assert len(one["stage_b"]) == 8 and len(one["stage_c"]) == 3
    with pytest.raises(ValueError):
        activated_inventory(("E01",), {"E02": winners["E02"]})
