"""Two preregistered direct transformations of canonical NQ/ES bars."""
from __future__ import annotations

import numpy as np

from quantlab5.data.schema import Bars

METHODS = ("joint_bar_reflection", "joint_session_reflection")


def _flips(keys: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    unique = np.unique(keys)
    sign = np.where(rng.random(len(unique)) < .5, -1.0, 1.0)
    return unique, sign


def transform(real: dict[str, Bars], method: str, seed: int) -> dict[str, Bars]:
    """Reflect original candles or sessions jointly, never returning source bars."""
    if method not in METHODS:
        raise ValueError("unknown frozen direct-null method")
    if set(real) != {"NQ", "ES"}:
        raise ValueError("paired NQ/ES source required")
    rng = np.random.default_rng(int(seed))
    field = "ts" if method == METHODS[0] else "sday"
    keys = np.concatenate([getattr(real[x], field) for x in ("NQ", "ES")])
    unique, bit = _flips(keys, rng)
    out = {}
    for inst in ("NQ", "ES"):
        b = real[inst]
        f = bit[np.searchsorted(unique, getattr(b, field))]
        if method == METHODS[0]:
            pivot = np.asarray(b.o)
        else:
            # Each session's first real open is the reflection pivot. This
            # preserves all within-session signed increments up to one sign.
            first = np.r_[0, np.flatnonzero(b.sday[1:] != b.sday[:-1])+1]
            pivot = np.asarray(b.o)[first[np.searchsorted(first, np.arange(b.n), side="right")-1]]
        o = pivot + f*(b.o-pivot)
        c = pivot + f*(b.c-pivot)
        h = np.where(f > 0, b.h, 2*pivot-b.l)
        l = np.where(f > 0, b.l, 2*pivot-b.h)
        out[inst] = b.with_prices(o=o, h=h, l=l, c=c, source=f"direct-null:{method}:{seed}")
    return out
