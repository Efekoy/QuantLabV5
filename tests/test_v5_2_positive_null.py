import numpy as np

from quantlab5.project import ROOT
from quantlab5.v5_2.positive_null import PositivePairedNull


def test_original_failing_seed_1002_is_structurally_valid():
    generator = PositivePairedNull(
        ROOT / "V5_1_DISCOVERY_NUISANCE_CALIBRATION.json",
        ROOT / "reports/V5_1_NUISANCE_TAPE.npz")
    bars = generator.generate_seed(1002)
    for inst in ("NQ", "ES"):
        b = bars[inst]
        for values in (b.o, b.h, b.l, b.c, b.v):
            assert np.isfinite(values).all()
        assert min(np.min(b.o), np.min(b.h), np.min(b.l), np.min(b.c)) > 0
        assert np.all(b.h >= np.maximum(b.o, b.c))
        assert np.all(b.l <= np.minimum(b.o, b.c))
        assert np.all(b.h >= b.l)
        assert np.all(b.v >= 0)
        assert np.all(np.diff(b.ts) > 0)
    assert np.intersect1d(bars["NQ"].ts, bars["ES"].ts).size > 1_000_000
