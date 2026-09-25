"""Purging, embargo, and chronological DISCOVERY sub-period utilities."""
from datetime import date

import numpy as np
import pandas as pd
import pytest

from quantlab5.validation.embargo import apply_embargo, purge_and_embargo
from quantlab5.validation.purging import leaking, overlaps, purge
from quantlab5.validation.time_splits import (calendar_year_splits, cscv_blocks, cscv_splits, walk_forward_splits,
                                              within_partition)


def _labels(n=100, horizon=5):
    """Observation i uses information from t=i to t=i+horizon (e.g. a forward-return label)."""
    s = np.arange(n)
    return s, s + horizon


def test_forward_return_labels_leak_across_the_boundary_without_purging():
    s, e = _labels()
    train = np.arange(0, 50)
    test = [(50, 69)]
    leak = leaking(train, s, e, test)
    assert leak.tolist() == [45, 46, 47, 48, 49]         # their label horizons reach into the test fold


def test_purging_removes_exactly_the_leaking_observations():
    s, e = _labels()
    train = np.r_[np.arange(0, 50), np.arange(70, 100)]
    kept = purge(train, s, e, [(50, 69)])
    assert set(train) - set(kept) == {45, 46, 47, 48, 49}
    assert not overlaps(s[kept], e[kept], [(50, 69)]).any()
    assert 70 in kept                                      # after the test fold: no overlap, kept by purging


def test_embargo_removes_observations_just_after_the_test_fold():
    s, e = _labels()
    train = np.r_[np.arange(0, 50), np.arange(70, 100)]
    kept = purge_and_embargo(train, s, e, [(50, 69)], embargo=3)
    assert {70, 71, 72}.isdisjoint(kept) and 73 in kept
    assert apply_embargo(train, s, [(50, 69)], 0).tolist() == train.tolist()


def test_touching_intervals_count_as_overlap_and_bad_inputs_fail():
    assert overlaps([10], [20], [(20, 30)]).tolist() == [True]
    assert overlaps([10], [19], [(20, 30)]).tolist() == [False]
    with pytest.raises(ValueError):
        overlaps([10], [5], [(0, 1)])
    with pytest.raises(ValueError):
        apply_embargo([0], [0], [(0, 1)], -1)


DISC = pd.bdate_range("2010-06-08", "2018-12-31").date


def test_calendar_year_splits_cover_each_year_once():
    ys = calendar_year_splits(DISC)
    assert [s.name for s in ys] == [f"Y{y}" for y in range(2010, 2019)]
    assert ys[0].test[0] == date(2010, 6, 8) and ys[-1].test[1] == date(2018, 12, 31)
    assert within_partition(ys, date(2010, 6, 1), date(2018, 12, 31))


@pytest.mark.parametrize("anchored", [False, True])
def test_walk_forward_is_chronological_and_non_overlapping(anchored):
    wf = walk_forward_splits(DISC, 500, 250, anchored=anchored, gap_sessions=5)
    assert len(wf) > 3
    for s in wf:
        assert s.train[1] < s.test[0]                     # test strictly after train
    for a, b in zip(wf, wf[1:]):
        assert a.test[1] < b.test[0]                      # test windows do not overlap
        if anchored:
            assert a.train[0] == b.train[0]
    assert within_partition(wf, date(2010, 6, 1), date(2018, 12, 31))
    assert not within_partition(wf, date(2011, 1, 1), date(2018, 12, 31))


def test_cscv_blocks_and_combinations():
    blocks = cscv_blocks(DISC, 8)
    assert len(blocks) == 8 and blocks[0][0] == date(2010, 6, 8)
    assert all(blocks[i][1] < blocks[i + 1][0] for i in range(7))
    sp = cscv_splits(DISC, 8)
    assert len(sp) == 70 and all(len(tr) == 4 and set(tr).isdisjoint(te) for tr, te in sp)
    with pytest.raises(ValueError):
        cscv_blocks(DISC, 7)
