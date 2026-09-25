"""Causal feature framework, lookahead detector, synchronized cross-market access."""
from datetime import date

import numpy as np
import pytest

from quantlab5.data.align import align_other
from quantlab5.data.schema import bars_from_arrays
from quantlab5.features.base import (Feature, FeatureSpec, LogReturn, PairReturnSpread, VolumeRatio, assert_causal,
                                     group_ids, lag_within_group)
from quantlab5.synthetic import markets as M

SESS = [date(2020, 10, 5), date(2020, 10, 6)]


class CenteredMeanBug(Feature):
    """INTENTIONAL LOOKAHEAD FIXTURE: a centred moving average uses 2 future bars."""

    def __init__(self):
        self.spec = FeatureSpec("centered_mean_bug", "1", ("c",), lookback=5, params={"w": 2})

    def _compute(self, bars, other):
        c = np.asarray(bars.c)
        out = np.full(len(c), np.nan)
        for i in range(2, len(c) - 2):
            out[i] = c[i - 2:i + 3].mean()
        return out


class FutureVolumeBug(Feature):
    """INTENTIONAL LOOKAHEAD FIXTURE: next bar's volume."""

    def __init__(self):
        self.spec = FeatureSpec("future_volume_bug", "1", ("v",), lookback=1)

    def _compute(self, bars, other):
        v = np.asarray(bars.v)
        return np.r_[v[1:], np.nan]


class OtherMarketFutureBug(Feature):
    """INTENTIONAL LOOKAHEAD FIXTURE: reads the other market's NEXT-minute close."""

    def __init__(self):
        self.spec = FeatureSpec("other_future_bug", "1", ("c",), "pair", lookback=1)

    def _compute(self, bars, other):
        return np.r_[other.c[1:], np.nan]


def test_trivial_features_are_causal():
    b = M.random_zero_edge_market(SESS)
    for f in (LogReturn(5), LogReturn(30), VolumeRatio(20)):
        assert_causal(f, b)


@pytest.mark.parametrize("bug", [CenteredMeanBug(), FutureVolumeBug()])
def test_lookahead_fixtures_are_caught(bug):
    b = M.random_zero_edge_market(SESS)
    with pytest.raises(AssertionError, match="NOT causal"):
        assert_causal(bug, b)


def test_cross_market_feature_is_causal_and_other_market_lookahead_is_caught():
    nq, es = M.correlated_pair(SESS)
    assert_causal(PairReturnSpread(), nq, other=es)
    with pytest.raises(AssertionError, match="NOT causal"):
        assert_causal(OtherMarketFutureBug(), nq, other=es)


def test_alignment_is_same_minute_only_and_never_forward_filled():
    nq, es = M.correlated_pair(SESS, missing_every=97)
    al = align_other(nq, es)
    missing = np.nonzero(~al.valid)[0]
    assert len(missing) > 0 and np.isnan(al.c[missing]).all()
    ok = np.nonzero(al.valid)[0]
    pos = np.searchsorted(es.ts, nq.ts[ok])
    assert (es.ts[pos] == nq.ts[ok]).all() and np.array_equal(al.c[ok], es.c[pos])
    f = PairReturnSpread().compute(nq, es)
    assert np.isnan(f[missing]).all()           # a missing ES bar gives NaN, not a stale ES value


def test_other_market_jump_is_visible_only_from_its_own_bar():
    nq, es = M.correlated_pair([date(2020, 10, 5)], missing_every=10**9)
    k = 700
    up = np.r_[np.zeros(k), np.full(es.n - k, 50.0)]           # ES jumps +50 from bar k on
    es2 = es.with_prices(o=es.o + up, h=es.h + up, l=es.l + up, c=es.c + up)
    f1 = PairReturnSpread().compute(nq, es)
    f2 = PairReturnSpread().compute(nq, es2)
    diff = np.nonzero(~((f1 == f2) | (np.isnan(f1) & np.isnan(f2))))[0]
    assert diff.min() == int(np.searchsorted(nq.ts, es.ts[k]))   # the NQ bar with the SAME minute as ES bar k


def test_session_reset_lookbacks_never_cross_sessions_or_rolls():
    b = M.roll_boundary_market()
    gid = group_ids(b, session_reset=True)
    lagged = lag_within_group(b.c, 3, gid)
    first_of_second = int(np.nonzero(np.diff(b.sday))[0][0] + 1)
    assert np.isnan(lagged[first_of_second:first_of_second + 3]).all()
    r = LogReturn(3).compute(b)
    assert np.isnan(r[first_of_second:first_of_second + 3]).all()


def test_feature_spec_validation_and_ids():
    a = FeatureSpec("x", "1", ("c", "v"), params={"n": 5})
    b = FeatureSpec("x", "1", ("c", "v"), params={"n": 6})
    assert a.feature_id != b.feature_id and a.feature_id == FeatureSpec("x", "1", ("c", "v"),
                                                                           params={"n": 5}).feature_id
    with pytest.raises(ValueError):
        FeatureSpec("x", "1", ("close",))
    with pytest.raises(ValueError):
        FeatureSpec("x", "1", ("c",), information_time="bar_open")
    with pytest.raises(TypeError):
        FeatureSpec("x", "1", ("c",), params={"bad": {1, 2}})


def test_volume_feature_sees_known_spikes():
    b = M.volume_spike_market()
    vr = VolumeRatio(20).compute(b)
    assert vr[50] == 50.0 and vr[120] == 50.0            # 5000 / 100
    assert np.isfinite(vr[21:]).any() and np.isnan(vr[:20]).all()
