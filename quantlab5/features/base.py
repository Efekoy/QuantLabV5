"""Generic causal feature interface (framework only -- the V4 feature library comes later).

Every feature declares, in a frozen `FeatureSpec`:

    name, version            identity (both enter the feature ID)
    required_columns         subset of o/h/l/c/v (volume is a first-class input)
    instruments              "single" or "pair" (pair = primary + synchronized other market)
    lookback                 bars of history the value depends on
    warmup                   bars before the first valid (non-NaN) value
    session_reset            True = the lookback never crosses a session boundary
    params                   parameter dictionary (canonical JSON; enters the ID)
    information_time         "bar_close": value[i] uses only data known at the CLOSE of bar i

Contract enforced by `compute`:
  * output is a float64 array aligned 1:1 with the primary bars;
  * value[i] may use bars <= i only (checked by `assert_causal`, which rewrites the
    future and requires the past to be bit-identical);
  * for pair features the other market must be passed through `align_other`, which
    exposes only the SAME-minute bar (no forward fill; missing -> NaN).

Two trivial features exist solely to prove the framework (`LogReturn`, `VolumeRatio`,
and the pair feature `PairReturnSpread`). They are not research features.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np

from quantlab5.data.align import AlignedOther, align_other
from quantlab5.data.schema import Bars
from quantlab5.diagnostics.lookahead import check_causality
from quantlab5.util.hashing import canonical_json, sha256_text

VALID_COLUMNS = ("o", "h", "l", "c", "v")


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    version: str
    required_columns: tuple[str, ...]
    instruments: str = "single"
    lookback: int = 1
    warmup: int = 0
    session_reset: bool = True
    params: dict = field(default_factory=dict)
    information_time: str = "bar_close"

    def __post_init__(self):
        if not self.name or not self.version:
            raise ValueError("feature needs a name and a version")
        bad = [c for c in self.required_columns if c not in VALID_COLUMNS]
        if bad:
            raise ValueError(f"unknown required columns {bad}")
        if self.instruments not in ("single", "pair"):
            raise ValueError("instruments must be 'single' or 'pair'")
        if self.lookback < 1 or self.warmup < 0:
            raise ValueError("lookback >= 1 and warmup >= 0 required")
        if self.information_time != "bar_close":
            raise ValueError("only bar_close information time is supported")
        canonical_json(self.params)   # raises if params have no canonical form

    def as_dict(self) -> dict:
        return {"name": self.name, "version": self.version, "required_columns": list(self.required_columns),
                "instruments": self.instruments, "lookback": self.lookback, "warmup": self.warmup,
                "session_reset": self.session_reset, "params": self.params,
                "information_time": self.information_time}

    @property
    def feature_id(self) -> str:
        return "F4-" + sha256_text(canonical_json(self.as_dict()))[:20]


class Feature(ABC):
    spec: FeatureSpec

    @abstractmethod
    def _compute(self, bars: Bars, other: AlignedOther | None) -> np.ndarray:
        ...

    def compute(self, bars: Bars, other: Bars | None = None) -> np.ndarray:
        if self.spec.instruments == "pair":
            if other is None:
                raise ValueError(f"{self.spec.name} is a pair feature and needs the other market")
            aligned = align_other(bars, other)
        else:
            if other is not None:
                raise ValueError(f"{self.spec.name} is single-instrument")
            aligned = None
        cols = {"o": bars.o, "h": bars.h, "l": bars.l, "c": bars.c, "v": bars.v}
        for col in self.spec.required_columns:
            if cols[col] is None:
                raise ValueError(f"required column {col} missing")
        out = np.array(self._compute(bars, aligned), dtype=np.float64, copy=True)
        if out.shape != (bars.n,):
            raise ValueError(f"{self.spec.name}: output shape {out.shape} != ({bars.n},)")
        if self.spec.warmup and bars.n:
            out[: min(self.spec.warmup, bars.n)] = np.nan
        return out


def assert_causal(feature: Feature, bars: Bars, other: Bars | None = None, n_cuts: int = 5,
                  seeds=(0, 1)) -> None:
    """Raise AssertionError if changing future bars changes any earlier feature value."""
    cuts = sorted({max(1, int(bars.n * f)) for f in np.linspace(0.1, 0.9, n_cuts)})
    fn = (lambda b: feature.compute(b)) if other is None else (lambda b, o: feature.compute(b, o))
    problems = check_causality(fn, bars, cuts, other=other, seeds=seeds)
    if problems:
        raise AssertionError(f"{feature.spec.name} is NOT causal: " + "; ".join(problems[:5]))


# ---------------------------------------------------------------- session-aware helpers

def session_start_mask(bars: Bars) -> np.ndarray:
    s = np.asarray(bars.sday)
    m = np.ones(len(s), dtype=bool)
    if len(s) > 1:
        m[1:] = s[1:] != s[:-1]
    return m


def group_ids(bars: Bars, session_reset: bool) -> np.ndarray:
    """Contiguous group id: lookbacks never cross a roll, nor a session if session_reset."""
    br = np.zeros(bars.n, dtype=bool)
    if bars.n > 1:
        br[1:] = np.asarray(bars.seg)[1:] != np.asarray(bars.seg)[:-1]
        if session_reset:
            br[1:] |= np.asarray(bars.sday)[1:] != np.asarray(bars.sday)[:-1]
    return np.cumsum(br)


def lag_within_group(x: np.ndarray, n: int, gid: np.ndarray) -> np.ndarray:
    """x[i - n] if bar i-n is in the same group as bar i, else NaN."""
    x = np.asarray(x, dtype=np.float64)
    out = np.full(len(x), np.nan)
    if n < len(x):
        same = gid[n:] == gid[:-n] if n > 0 else np.ones(len(x), bool)
        out[n:] = np.where(same, x[:-n] if n > 0 else x, np.nan)
    return out


def trailing_mean_prev(x: np.ndarray, n: int, gid: np.ndarray) -> np.ndarray:
    """Mean of x[i-n .. i-1] within the group (excludes bar i); NaN if fewer than n values."""
    x = np.asarray(x, dtype=np.float64)
    out = np.full(len(x), np.nan)
    cs = np.concatenate([[0.0], np.cumsum(np.nan_to_num(x))])
    cnt = np.concatenate([[0], np.cumsum(np.isfinite(x))])
    idx = np.arange(len(x))
    lo = idx - n
    ok = lo >= 0
    ok[ok] &= gid[lo[ok]] == gid[idx[ok]]
    i = idx[ok]
    full = (cnt[i] - cnt[i - n]) == n
    out[i[full]] = (cs[i] - cs[i - n])[full] / n
    return out


# ---------------------------------------------------------------- trivial proof features

class LogReturn(Feature):
    """log(c[i] / c[i-n]) within session and contract. FRAMEWORK TEST FEATURE ONLY."""

    def __init__(self, n: int = 5):
        self.spec = FeatureSpec("log_return", "1", ("c",), "single", lookback=n, warmup=0,
                                session_reset=True, params={"n": int(n)})

    def _compute(self, bars, other):
        gid = group_ids(bars, self.spec.session_reset)
        prev = lag_within_group(bars.c, self.spec.params["n"], gid)
        return np.log(np.asarray(bars.c) / prev)


class VolumeRatio(Feature):
    """v[i] / mean(v[i-n..i-1]) within session and contract. FRAMEWORK TEST FEATURE ONLY."""

    def __init__(self, n: int = 20):
        self.spec = FeatureSpec("volume_ratio", "1", ("v",), "single", lookback=n + 1, warmup=0,
                                session_reset=True, params={"n": int(n)})

    def _compute(self, bars, other):
        gid = group_ids(bars, self.spec.session_reset)
        base = trailing_mean_prev(bars.v, self.spec.params["n"], gid)
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(base > 0, np.asarray(bars.v) / base, np.nan)


class PairReturnSpread(Feature):
    """1-bar log return of primary minus the other market's SAME-minute 1-bar return.
    FRAMEWORK TEST FEATURE ONLY (proves synchronized cross-market access)."""

    def __init__(self):
        self.spec = FeatureSpec("pair_return_spread", "1", ("c",), "pair", lookback=2, warmup=0,
                                session_reset=True, params={})

    def _compute(self, bars, other: AlignedOther):
        gid = group_ids(bars, True)
        r1 = np.log(np.asarray(bars.c) / lag_within_group(bars.c, 1, gid))
        oc = other.c
        prev_oc = lag_within_group(oc, 1, gid)
        both = other.valid & np.r_[False, other.valid[:-1]]
        r2 = np.where(both, np.log(oc / prev_oc), np.nan)
        return r1 - r2
