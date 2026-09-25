"""Canonical schema, timestamps, volume as a first-class field, contract rolls."""
import numpy as np
import pandas as pd
import pyarrow as pa
import pytest

from conftest import RAW_SCHEMA, make_bars
from quantlab5.data.rolls import check_roll_boundary_flags, returns_excluding_rolls, roll_indices
from quantlab5.data.schema import REQUIRED_COLUMNS, SchemaError, bars_from_arrays, bars_from_frame, check_arrow_schema
from quantlab5.data.validation import DataIntegrityError
from quantlab5.data.volume_qc import missing_volume_mask, schemas_consistent, volume_structure, zero_volume_mask
from quantlab5.synthetic.markets import roll_boundary_market, volume_spike_market


def test_volume_is_a_required_column():
    assert "volume" in REQUIRED_COLUMNS
    assert check_arrow_schema(RAW_SCHEMA) == []
    no_vol = pa.schema([f for f in RAW_SCHEMA if f.name != "volume"])
    assert "missing required column volume" in check_arrow_schema(no_vol)
    float_vol = pa.schema([pa.field("volume", pa.float64()) if f.name == "volume" else f for f in RAW_SCHEMA])
    assert any("volume" in x for x in check_arrow_schema(float_vol))
    with pytest.raises(SchemaError):
        bars_from_frame(pd.DataFrame({"ts_event": [], "open": [], "high": [], "low": [], "close": [],
                                      "symbol": []}), "NQ", "t")


def test_timestamps_must_be_sorted_unique_and_minute_aligned():
    ts, o, h, l, c = make_bars([100, 101, 102])
    with pytest.raises(DataIntegrityError, match="duplicate"):
        bars_from_arrays("NQ", np.r_[ts[:2], ts[1]], o, h, l, c, [1, 1, 1])
    with pytest.raises(DataIntegrityError, match="out-of-order"):
        bars_from_arrays("NQ", ts[::-1], o, h, l, c, [1, 1, 1])
    with pytest.raises(DataIntegrityError, match="whole minutes"):
        bars_from_arrays("NQ", ts + 1_000_000_000, o, h, l, c, [1, 1, 1])


@pytest.mark.parametrize("vol,err", [([1, -5, 3], "negative"), ([1, 2.5, 3], "non-integral"),
                                     ([1, np.inf, 3], "infinite")])
def test_impossible_volume_is_rejected(vol, err):
    ts, o, h, l, c = make_bars([100, 101, 102])
    with pytest.raises(DataIntegrityError, match=err):
        bars_from_arrays("NQ", ts, o, h, l, c, vol)


def test_missing_volume_is_nan_never_zero_filled():
    ts, o, h, l, c = make_bars([100, 101, 102])
    b = bars_from_arrays("NQ", ts, o, h, l, c, [1, np.nan, 3])
    assert np.isnan(b.v[1])
    assert missing_volume_mask(b.v).tolist() == [False, True, False]


def test_zero_volume_rows_are_identified_and_spikes_preserved():
    b = volume_spike_market()
    assert np.nonzero(zero_volume_mask(b.v))[0].tolist() == [10]
    assert np.nonzero(b.v == 5000)[0].tolist() == [50, 120, 300]


def test_volume_structure_report_on_a_frame():
    df = pd.DataFrame({"volume": pd.array([5, 0, 7, None], dtype="Int64")})
    rep = volume_structure(df)
    assert rep["column_present"] and rep["integer_dtype"] and rep["missing"] == 1
    assert rep["zero_volume_rows"] == 1 and rep["negative"] == 0 and rep["passes"]
    bad = volume_structure(pd.DataFrame({"volume": [1, -2]}))
    assert bad["negative"] == 1 and not bad["passes"]
    assert volume_structure(pd.DataFrame({"close": [1.0]})) == {"column_present": False}


def test_schema_consistency_across_instruments():
    a = {"volume": "int64", "close": "double"}
    assert schemas_consistent({"NQ": a, "ES": dict(a)})[0]
    ok, probs = schemas_consistent({"NQ": a, "ES": {"volume": "double", "close": "double"}})
    assert not ok and probs


def test_roll_segments_and_flags():
    b = roll_boundary_market()
    idx = roll_indices(b.seg)
    assert len(idx) == 1
    assert b.sday[idx[0]] != b.sday[idx[0] - 1]            # roll happens at the session boundary
    r = returns_excluding_rolls(b.c, b.seg)
    assert np.isnan(r[idx[0]]) and np.isfinite(r[idx[0] + 1])
    flags = np.zeros(b.n, bool)
    flags[idx] = True
    rep = check_roll_boundary_flags(b.seg, flags, b.sday)
    assert rep["flag_matches_derived"] and rep["rolls_only_at_session_start"]
