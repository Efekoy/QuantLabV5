import json

import numpy as np
import pandas as pd

from quantlab5.util.hashing import file_sha256
from quantlab5.v5_1.paired_null import MODES, PairedNuisanceNull
from research.check_v5_1_nuisance import diagnose


def test_modes_preserve_unsigned_bar_components_and_zero_sign_memory(tmp_path):
    ts = pd.date_range("2020-01-02 00:00", periods=1600, freq="min", tz="UTC").as_unit("ns").asi8
    rng = np.random.default_rng(19)
    payload = {}
    for prefix in ("nq", "es"):
        n = len(ts)
        body = rng.integers(1, 6, n, dtype=np.int32)
        gap = rng.integers(0, 3, n, dtype=np.int32)
        relation = rng.choice(np.array([-1, 1], np.int8), n)
        relation[gap == 0] = 0
        payload.update({f"{prefix}_ts": ts,
                        f"{prefix}_segment": np.ones(n, np.int32),
                        f"{prefix}_gap_ticks": gap,
                        f"{prefix}_body_ticks": body,
                        f"{prefix}_up_wick_ticks": rng.integers(0, 4, n, dtype=np.int32),
                        f"{prefix}_down_wick_ticks": rng.integers(0, 4, n, dtype=np.int32),
                        f"{prefix}_volume": rng.integers(100, 500, n, dtype=np.int32),
                        f"{prefix}_gap_body_relation": relation})
    tape = tmp_path / "tape.npz"
    np.savez_compressed(tape, **payload)
    artifact = tmp_path / "artifact.json"
    artifact.write_text(json.dumps({"kind": "V5_1_DISCOVERY_NUISANCE_CALIBRATION",
                                    "tape_sha256": file_sha256(tape),
                                    "median_price": {"NQ": 10000, "ES": 5000},
                                    "joint_sign": {"same_sign_fraction": .7,
                                                   "same_sign_by_joint_magnitude_quartile": [.7]*4,
                                                   "joint_magnitude_quartile_cuts": [1, 2, 3]}}))
    for mode in MODES:
        generator = PairedNuisanceNull(artifact, tape, mode)
        bars = generator.generate_seed(1234)
        for inst, prefix in (("NQ", "nq"), ("ES", "es")):
            b = bars[inst]
            assert np.array_equal(b.ts, ts)
            assert np.array_equal(b.seg, payload[f"{prefix}_segment"]-1)
            assert np.all(np.asarray(b.h) >= np.maximum(b.o, b.c))
            assert np.all(np.asarray(b.l) <= np.minimum(b.o, b.c))
            assert np.all(np.asarray(b.l) > 0)
            if mode != "paired_day_resample":
                assert np.array_equal(np.abs(b.c-b.o)/.25, payload[f"{prefix}_body_ticks"])
                assert np.array_equal(b.v, payload[f"{prefix}_volume"])
        assert np.array_equal(bars["NQ"].ts, bars["ES"].ts)
        if mode == "paired_sign":
            report = diagnose(generator, 1234)
            assert report["nuisance_pass"]
            assert max(report["joint_nuisance_error"].values()) < 1e-3
