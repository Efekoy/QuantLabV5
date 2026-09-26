import json

import numpy as np
import pandas as pd

from quantlab5.util.hashing import file_sha256
from quantlab5.v5_3.range_null import RangeSeparatedNull


def _fixture(tmp_path, *, extra_wick=0, future_body_change=0):
    ts = pd.date_range("2020-01-02", periods=500, freq="min", tz="UTC").as_unit("ns").asi8
    tape = {}
    for prefix in ("nq", "es"):
        body = np.full(len(ts), 3, np.int32)
        body[300:] += future_body_change
        tape.update({f"{prefix}_ts": ts,
                     f"{prefix}_segment": np.ones(len(ts), np.int32),
                     f"{prefix}_gap_ticks": np.zeros(len(ts), np.int32),
                     f"{prefix}_body_ticks": body,
                     f"{prefix}_up_wick_ticks": np.full(len(ts), 2+extra_wick, np.int32),
                     f"{prefix}_down_wick_ticks": np.full(len(ts), 2+extra_wick, np.int32),
                     f"{prefix}_volume": np.full(len(ts), 100, np.int32),
                     f"{prefix}_gap_body_relation": np.zeros(len(ts), np.int8)})
    path = tmp_path / f"tape_{extra_wick}_{future_body_change}.npz"
    np.savez_compressed(path, **tape)
    artifact = tmp_path / f"artifact_{extra_wick}_{future_body_change}.json"
    artifact.write_text(json.dumps({"kind": "V5_1_DISCOVERY_NUISANCE_CALIBRATION",
                                    "tape_sha256": file_sha256(path),
                                    "median_price": {"NQ": 10000, "ES": 5000},
                                    "joint_sign": {"same_sign_fraction": .8}}))
    return RangeSeparatedNull(artifact, path)


def test_wick_state_changes_range_without_changing_causal_close(tmp_path):
    base = _fixture(tmp_path).generate_seed(42)
    wider = _fixture(tmp_path, extra_wick=3).generate_seed(42)
    for inst in ("NQ", "ES"):
        a, b = base[inst], wider[inst]
        assert np.array_equal(a.o, b.o)
        assert np.array_equal(a.c, b.c)
        assert np.all(b.h-b.l > a.h-a.l)
        assert np.all(b.l > 0)


def test_future_nuisance_change_cannot_change_past_world(tmp_path):
    base = _fixture(tmp_path).generate_seed(91)
    changed = _fixture(tmp_path, future_body_change=4).generate_seed(91)
    for inst in ("NQ", "ES"):
        a, b = base[inst], changed[inst]
        for field in ("o", "h", "l", "c", "v"):
            assert np.array_equal(getattr(a, field)[:300], getattr(b, field)[:300])
        assert np.all(a.l > 0) and np.all(b.l > 0)


def test_body_signs_preserve_valid_ohlc_across_seeds(tmp_path):
    gen = _fixture(tmp_path)
    for seed in range(10):
        for bars in gen.generate_seed(seed).values():
            assert np.isfinite(bars.o).all()
            assert np.isfinite(bars.h).all()
            assert np.isfinite(bars.l).all()
            assert np.isfinite(bars.c).all()
            assert np.all(bars.h >= np.maximum(bars.o, bars.c))
            assert np.all(bars.l <= np.minimum(bars.o, bars.c))
            assert np.all(bars.l > 0)
