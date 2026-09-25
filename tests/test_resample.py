"""Higher-timeframe bars must never appear before they have closed. (Ported from QuantLabV3; V4 additions at the end.)"""
import numpy as np

from quantlab5.data.resample import build_htf, htf_for_bars, htf_value_at_minute


def _bars(n, start_min=28_000_000):
    rng = np.random.default_rng(3)
    c = 100 + np.cumsum(rng.standard_normal(n))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + 0.3
    l = np.minimum(o, c) - 0.3
    tmin = start_min + np.arange(n, dtype=np.int64)
    return tmin, o, h, l, c, np.zeros(n, np.int32), np.zeros(n, np.int32)


def test_htf_available_only_after_close():
    tmin, o, h, l, c, seg, sday = _bars(60, start_min=15 * 2_000_000)   # aligned to a 15-min boundary
    htf = build_htf(tmin, o, h, l, c, seg, sday, 15)
    # bars 0..13 are inside the first bucket: nothing completed yet
    assert (htf.last[:14] == -1).all()
    # bar 14 is the last minute of bucket 0: at its close bucket 0 is complete
    assert htf.last[14] == 0
    assert htf.c[0] == c[14] and htf.o[0] == o[0] and htf.h[0] == h[:15].max()
    assert htf.last[29] == 1 and htf.last[28] == 0


def test_mutating_current_bucket_does_not_change_available_htf():
    tmin, o, h, l, c, seg, sday = _bars(90, start_min=15 * 2_000_000)
    a = build_htf(tmin, o, h, l, c, seg, sday, 15)
    t = 40                                   # inside bucket 2 (bars 30..44)
    h2, l2, c2 = h.copy(), l.copy(), c.copy()
    h2[t + 1:] += 50
    l2[t + 1:] -= 50
    c2[t + 1:] += 7
    b = build_htf(tmin, o, h2, l2, c2, seg, sday, 15)
    j = a.last[t]
    assert j == b.last[t] == 1
    for fa, fb in ((a.o, b.o), (a.h, b.h), (a.l, b.l), (a.c, b.c)):
        assert np.array_equal(fa[: j + 1], fb[: j + 1])


def test_missing_last_minute_still_waits_for_bucket_end():
    tmin, o, h, l, c, seg, sday = _bars(40, start_min=15 * 2_000_000)
    keep = np.ones(40, bool)
    keep[14] = False                          # the bucket's last minute is missing
    htf = build_htf(tmin[keep], o[keep], h[keep], l[keep], c[keep], seg[keep], sday[keep], 15)
    # the bar starting at minute 15 (index 14 after removal) completes nothing until its own close
    assert htf.last[13] == -1                 # minute 13: bucket 0 still open
    assert htf.last[14] == 0                  # minute 15's close: bucket 0 (ended at 15) is complete


# ----------------------------------------------------------------------------- V4 additions

def test_volume_is_summed_and_missing_volume_propagates():
    tmin, o, h, l, c, seg, sday = _bars(30, start_min=15 * 2_000_000)
    v = np.arange(30, dtype=float)
    htf = build_htf(tmin, o, h, l, c, seg, sday, 15, v=v)
    assert htf.v[0] == v[:15].sum() and htf.v[1] == v[15:].sum()
    v2 = v.copy()
    v2[3] = np.nan
    assert np.isnan(build_htf(tmin, o, h, l, c, seg, sday, 15, v=v2).v[0])


def test_mutating_future_volume_does_not_change_available_htf_volume():
    tmin, o, h, l, c, seg, sday = _bars(90, start_min=15 * 2_000_000)
    v = np.full(90, 10.0)
    a = build_htf(tmin, o, h, l, c, seg, sday, 15, v=v)
    v2 = v.copy()
    v2[41:] = 99999
    b = build_htf(tmin, o, h, l, c, seg, sday, 15, v=v2)
    j = a.last[40]
    assert np.array_equal(a.v[: j + 1], b.v[: j + 1])


def test_bucket_straddling_session_or_roll_is_flagged():
    tmin, o, h, l, c, seg, sday = _bars(30, start_min=15 * 2_000_000)
    sday = sday.copy()
    sday[20:] = 1
    seg = seg.copy()
    seg[22:] = 1
    htf = build_htf(tmin, o, h, l, c, seg, sday, 15)
    assert htf.sday[1] == -1 and htf.seg[1] == -1 and htf.sday[0] == 0


def test_broadcast_uses_only_completed_buckets():
    from quantlab5.synthetic.markets import rising_market
    b = rising_market(60)
    htf = htf_for_bars(b, 5)
    close5 = htf_value_at_minute(htf, htf.c)
    for i in range(b.n):
        if np.isfinite(close5[i]):
            # a completed 5-min close available at bar i must equal the close of some bar <= i
            assert close5[i] in set(np.asarray(b.c)[: i + 1].tolist())
    assert np.isnan(close5[:4]).all() and close5[4] == b.c[4]


def test_rejects_unsorted_timestamps():
    tmin, o, h, l, c, seg, sday = _bars(10)
    import pytest
    with pytest.raises(ValueError):
        build_htf(tmin[::-1], o, h, l, c, seg, sday, 5)
