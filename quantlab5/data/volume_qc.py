"""Structural volume quality checks (NOT the volume research audit).

These checks answer only "is the volume column usable?":
  exists, parses, sensible dtype, no negatives, missingness measurable, zero-volume
  rows identifiable, schema consistent across instruments.

They deliberately compute NO distributional statistics (no means, quantiles,
time-of-day profiles, correlations with price). The later, stage-gated volume audit
will study time-of-day normalisation, roll effects, outliers and quality.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def volume_structure(df: pd.DataFrame) -> dict:
    out: dict = {"column_present": "volume" in df.columns}
    if not out["column_present"]:
        return out
    col = df["volume"]
    out["dtype"] = str(col.dtype)
    out["integer_dtype"] = bool(pd.api.types.is_integer_dtype(col.dtype))
    out["rows"] = int(len(col))
    num = pd.to_numeric(col, errors="coerce")
    out["unparseable"] = int(num.isna().sum() - col.isna().sum())
    out["missing"] = int(col.isna().sum())
    out["missing_fraction"] = float(col.isna().mean()) if len(col) else 0.0
    vals = num.to_numpy(dtype="float64", na_value=np.nan)
    fin = np.isfinite(vals)
    out["negative"] = int((vals[fin] < 0).sum())
    out["non_integral"] = int((np.floor(vals[fin]) != vals[fin]).sum())
    out["zero_volume_rows"] = int((vals[fin] == 0).sum())
    out["passes"] = bool(out["integer_dtype"] and out["unparseable"] == 0 and out["negative"] == 0
                         and out["non_integral"] == 0)
    return out


def zero_volume_mask(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype="float64")
    return np.isfinite(v) & (v == 0)


def missing_volume_mask(v: np.ndarray) -> np.ndarray:
    return ~np.isfinite(np.asarray(v, dtype="float64"))


def schemas_consistent(schemas: dict[str, dict[str, str]]) -> tuple[bool, list[str]]:
    """schemas: instrument -> {column: dtype}. All instruments must have identical columns and dtypes."""
    items = list(schemas.items())
    problems = []
    if not items:
        return True, problems
    ref_name, ref = items[0]
    for name, sch in items[1:]:
        if sch != ref:
            diff = sorted(set(sch.items()) ^ set(ref.items()))
            problems.append(f"{name} vs {ref_name}: {diff}")
    return not problems, problems
