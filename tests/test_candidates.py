"""Candidate IDs and deterministic enumeration (synthetic grammar -- NOT a strategy grammar; ported from QuantLabV4)."""
import math

import pytest

from quantlab5.search.candidate_id import IdScheme, candidate_id, serialize_spec
from quantlab5.search.generator import (DuplicateCandidateError, enumerate_candidates, enumeration_fingerprint,
                                        enumeration_order)
from quantlab5.search.grammar import Dimension, Grammar
from quantlab5.search.robustness import neighbours
from quantlab5.util.hashing import CanonicalError


def toy_grammar(with_constraint=True):
    g = Grammar("toy", "1", [Dimension("feature", ("a", "b", "c")), Dimension("lookback", (5, 10, 20, 40)),
                             Dimension("threshold", (0.5, 1.0, 1.5)), Dimension("side", ("long", "short"))],
                constants={"window": "rth"})
    if with_constraint:
        g.constraints["no_c_short"] = lambda s: not (s["feature"] == "c" and s["side"] == "short")
    return g


def test_same_grammar_seed_config_gives_identical_ids_in_identical_order():
    for order in ("lexicographic", "seeded_permutation"):
        a = [c.candidate_id for c in enumerate_candidates(toy_grammar(), order, seed=7)]
        b = [c.candidate_id for c in enumerate_candidates(toy_grammar(), order, seed=7)]
        assert a == b
    p7 = [c.candidate_id for c in enumerate_candidates(toy_grammar(), "seeded_permutation", seed=7)]
    p8 = [c.candidate_id for c in enumerate_candidates(toy_grammar(), "seeded_permutation", seed=8)]
    assert p7 != p8 and sorted(p7) == sorted(p8)


def test_known_enumeration_fingerprint_is_stable():
    fp = enumeration_fingerprint(enumerate_candidates(toy_grammar()))
    assert fp == enumeration_fingerprint(enumerate_candidates(toy_grammar()))
    assert len(list(enumerate_candidates(toy_grammar()))) == 72 - 12


def test_ids_derive_from_content_not_position():
    cands = list(enumerate_candidates(toy_grammar(), "lexicographic"))
    perm = list(enumerate_candidates(toy_grammar(), "seeded_permutation", seed=3))
    by_spec = {serialize_spec(c.spec): c.candidate_id for c in cands}
    assert all(by_spec[serialize_spec(c.spec)] == c.candidate_id for c in perm)
    assert candidate_id(cands[5].spec) == cands[5].candidate_id


def test_no_duplicate_ids_and_different_specs_differ():
    cands = list(enumerate_candidates(toy_grammar()))
    ids = [c.candidate_id for c in cands]
    assert len(ids) == len(set(ids))
    assert candidate_id({"x": 1}) != candidate_id({"x": 2})
    assert candidate_id({"x": 1}) != candidate_id({"x": 1, "y": None})
    assert candidate_id({"x": 1}) != candidate_id({"x": "1"})


def test_duplicate_generation_is_detected():
    g = toy_grammar(False)
    g.spec_at = lambda i: {"always": "same"}          # a broken grammar producing duplicate content
    with pytest.raises(DuplicateCandidateError):
        list(enumerate_candidates(g))


def test_stable_serialisation():
    a = {"b": 1, "a": [1.5, {"z": 0.0, "y": -0.0}], "c": (1, 2)}
    b = {"c": [1, 2], "a": [1.5, {"y": 0.0, "z": 0.0}], "b": 1}
    assert serialize_spec(a) == serialize_spec(b) == '{"a":[1.5,{"y":0.0,"z":0.0}],"b":1,"c":[1,2]}'
    assert candidate_id(a) == candidate_id(b)
    for bad in ({"x": math.nan}, {"x": math.inf}, {"x": {1, 2}}, {"x": object()}, {1: "int key"}):
        with pytest.raises(CanonicalError):
            candidate_id(bad)


def test_namespace_and_scheme_change_ids():
    s = {"x": 1}
    assert candidate_id(s, IdScheme(namespace="quantlab5")) != candidate_id(s, IdScheme(namespace="quantlab3"))
    assert candidate_id(s).startswith("Q5-") and len(candidate_id(s)) == 3 + 24     # V5 prefix (was Q4 in V4)


def test_shards_partition_the_enumeration_exactly():
    g = toy_grammar()
    full = [c.candidate_id for c in enumerate_candidates(g, "seeded_permutation", seed=11)]
    parts = []
    for k in range(4):
        parts += [c.candidate_id for c in enumerate_candidates(g, "seeded_permutation", seed=11, shard=(k, 4))]
    assert parts == full


def test_random_access_matches_enumeration_and_size():
    g = toy_grammar(False)
    assert g.size == 72
    assert [g.spec_at(i) for i in range(g.size)] == [c.spec for c in enumerate_candidates(g)]
    assert sorted(enumeration_order(g, "seeded_permutation", 1).tolist()) == list(range(72))


def test_grammar_rejects_ambiguity():
    with pytest.raises(ValueError):
        Dimension("x", (1, 1))
    with pytest.raises(ValueError):
        Grammar("g", "1", [Dimension("x", (1,)), Dimension("x", (2,))])


def test_neighbours_are_one_step_in_one_dimension():
    g = toy_grammar(False)
    i = 1 * 24 + 1 * 6 + 1 * 2 + 0            # feature b, lookback 10, threshold 1.0, long
    nb = neighbours(g, i)
    base = g.spec_at(i)
    for j in nb:
        s = g.spec_at(j)
        assert sum(s[k] != base[k] for k in ("feature", "lookback", "threshold", "side")) == 1
    assert len(nb) == 2 + 2 + 2 + 1
