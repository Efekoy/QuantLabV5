"""Synthetic engineering checks before any direct-null structure access."""
import numpy as np

from quantlab5.data.schema import bars_from_arrays
from quantlab5.direct_null.methods import METHODS, transform


def _source():
    ts = np.array([1525089600000000000, 1525089660000000000,
                   1525089720000000000, 1525089780000000000], np.int64)
    out = {}
    for inst, base in (("NQ", 7000.), ("ES", 2700.)):
        o = base + np.array([0., 1., 2., 1.])
        c = o + np.array([1., -1., 2., -1.])
        h = np.maximum(o, c)+.5
        l = np.minimum(o, c)-.75
        out[inst] = bars_from_arrays(inst, ts, o, h, l, c,
                                     np.array([100, 200, 150, 125]),
                                     np.array([inst+"M8"]*4), source="test-source")
    return out


def test_reflections_preserve_paired_structure_and_valid_ohlc():
    source = _source()
    for method in METHODS:
        world = transform(source, method, 9101)
        for inst in ("NQ", "ES"):
            a, b = source[inst], world[inst]
            assert np.array_equal(a.ts, b.ts)
            assert np.array_equal(a.v, b.v)
            assert np.allclose(a.h-a.l, b.h-b.l)
            assert np.allclose(abs(a.c-a.o), abs(b.c-b.o))
            assert np.all(b.l > 0)
            assert np.all(b.h >= np.maximum(b.o, b.c))
            assert np.all(b.l <= np.minimum(b.o, b.c))
        nq_ratio = np.sign(world["NQ"].c-world["NQ"].o)/np.sign(source["NQ"].c-source["NQ"].o)
        es_ratio = np.sign(world["ES"].c-world["ES"].o)/np.sign(source["ES"].c-source["ES"].o)
        assert np.array_equal(nq_ratio, es_ratio)


def test_fixed_seed_reproduces_world():
    source = _source()
    for method in METHODS:
        a, b = transform(source, method, 5), transform(source, method, 5)
        assert all(a[k].content_hash() == b[k].content_hash() for k in source)
