import numpy as np
import pytest

from quantlab5.v5.duplicate_accounting import (behavioral_duplicate_map,
                                                exact_duplicate_map, pairwise_duplicate_analysis,
                                                signal_fingerprint)
from types import SimpleNamespace


def test_exact_duplicate_map_keeps_all_ids_and_marks_first():
    a = np.array([0, 1, 0, 1], bool)
    z = np.zeros(4, bool)
    rows = [("A", a, z, "stop1_exit60"), ("B", a.copy(), z.copy(), "stop1_exit60"),
            ("C", a, z, "stop2_exit60"), ("D", z, a, "stop1_exit60")]
    assert exact_duplicate_map(rows) == {"A": "A", "B": "A", "C": "C", "D": "D"}
    assert signal_fingerprint(a, z, "x") == signal_fingerprint(a.copy(), z.copy(), "x")


def test_duplicate_accounting_rejects_ambiguous_ids():
    a = np.array([True])
    with pytest.raises(ValueError, match="duplicate candidate ID"):
        exact_duplicate_map([("A", a, a, "x"), ("A", a, a, "x")])


def test_behavioral_duplicates_annotate_without_dropping_any_id():
    rng = np.random.default_rng(43)
    a = rng.normal(size=80)
    b = a + .01 * rng.normal(size=80)
    c = rng.normal(size=80)
    ids = ("A", "B", "C", "D", "E")
    paths = np.column_stack((a, b, c, np.zeros(80), np.zeros(80)))
    assert behavioral_duplicate_map(ids, paths) == {
        "A": "A", "B": "A", "C": "C", "D": "D", "E": "D"}


def test_pairwise_analysis_measures_entries_overlap_and_daily_behavior():
    x = np.arange(20, dtype=float)
    rows = [SimpleNamespace(candidate_id="A", signal_hash="h", entry_indices=np.array([2, 5]),
                            trade_sides=np.array([1, 1]), daily_r=x),
            SimpleNamespace(candidate_id="B", signal_hash="h", entry_indices=np.array([2, 5]),
                            trade_sides=np.array([1, 1]), daily_r=x+.01),
            SimpleNamespace(candidate_id="C", signal_hash="other", entry_indices=np.array([2, 8]),
                            trade_sides=np.array([-1, 1]), daily_r=-x)]
    result = pairwise_duplicate_analysis(rows)
    ab = next(r for r in result if (r.left_id, r.right_id) == ("A", "B"))
    assert ab.exact_signals and ab.exact_entries
    assert ab.same_direction_entry_jaccard == ab.trade_stream_overlap == 1
    assert ab.highly_overlapping and ab.behaviorally_similar
    assert len(rows) == 3  # scientific records are not filtered


def test_position_overlap_is_recorded_without_matching_entries():
    x = np.arange(20, dtype=float)
    rows = [SimpleNamespace(candidate_id="A", signal_hash="a", entry_indices=np.array([2]),
                            exit_indices=np.array([8]), trade_sides=np.array([1]), daily_r=x),
            SimpleNamespace(candidate_id="B", signal_hash="b", entry_indices=np.array([5]),
                            exit_indices=np.array([10]), trade_sides=np.array([-1]), daily_r=-x)]
    pair, = pairwise_duplicate_analysis(rows)
    assert pair.trade_stream_overlap == 0
    assert pair.simultaneous_position_overlap == 4 / 6
