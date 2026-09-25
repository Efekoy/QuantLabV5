"""Look-ahead detector: rewrite the future and check that the past did not change.

(Adapted from quantlab3/diagnostics/causality.py. The method is unchanged; the V3
coupling to V3Features / V3 families / the V3 management library was removed so it
works on ANY function of Bars: features, signals, whole signal->trade pipelines.)

For a cut point k, every bar from k onward (open, high, low, close AND volume, and
the other market's bars for cross-market functions) is replaced by an unrelated
random walk, timestamps kept. Recomputing from scratch must leave every output
value on bars < k bit-identical (NaN == NaN), and every trade that exited before
bar k identical. Any difference means information from bar >= k was used.
"""
from __future__ import annotations

import numpy as np

from quantlab5.data.schema import Bars


def _mutate_arrays(o, h, l, c, v, k, rng):
    o, h, l, c, v = (np.array(x, dtype=np.float64, copy=True) for x in (o, h, l, c, v))
    m = len(c) - k
    if m <= 0:
        return o, h, l, c, v
    start = c[k - 1] if k > 0 and np.isfinite(c[k - 1]) else 100.0
    steps = rng.standard_normal(m) * max(abs(start) * 0.002, 0.25)
    cc = start + np.cumsum(steps) + rng.choice([-1, 1]) * abs(start) * 0.03
    cc = np.maximum(cc, abs(start) * 0.1)
    oo = np.r_[cc[0] - steps[0], cc[:-1]]
    oo = np.maximum(oo, abs(start) * 0.1)
    hh = np.maximum(oo, cc) + np.abs(rng.standard_normal(m)) * abs(start) * 0.001
    ll = np.minimum(oo, cc) - np.abs(rng.standard_normal(m)) * abs(start) * 0.001
    ll = np.maximum(ll, abs(start) * 0.05)
    vv = rng.integers(0, 5000, m).astype(np.float64)
    o[k:], h[k:], l[k:], c[k:], v[k:] = oo, hh, ll, cc, vv
    return o, h, l, c, v


def mutate_after(bars: Bars, k: int, seed: int = 0) -> Bars:
    rng = np.random.default_rng(seed)
    o, h, l, c, v = _mutate_arrays(bars.o, bars.h, bars.l, bars.c, bars.v, k, rng)
    return bars.with_prices(o, h, l, c, v, source=bars.source + "+mutated")


def _as_tuple(x):
    return tuple(x) if isinstance(x, (tuple, list)) else (x,)


def prefix_differences(a_out, b_out, k: int) -> list[str]:
    problems = []
    for j, (a, b) in enumerate(zip(_as_tuple(a_out), _as_tuple(b_out))):
        a, b = np.asarray(a), np.asarray(b)
        if a.shape != b.shape:
            problems.append(f"output {j}: shape changed {a.shape} -> {b.shape}")
            continue
        if a.dtype.kind == "f":
            same = (a[:k] == b[:k]) | (np.isnan(a[:k]) & np.isnan(b[:k]))
        else:
            same = a[:k] == b[:k]
        bad = np.nonzero(~same)[0]
        if len(bad):
            problems.append(f"output {j}: {len(bad)} values before the cut changed (first at {int(bad[0])}, cut {k})")
    return problems


def check_causality(fn, bars: Bars, cuts, other: Bars | None = None, seeds=(0, 1)) -> list[str]:
    """fn(bars) or fn(bars, other) -> array or tuple of arrays aligned to `bars`.

    Returns a list of problems (empty = causal at every cut tested)."""
    problems = []
    base = fn(bars) if other is None else fn(bars, other)
    for k in cuts:
        for seed in seeds:
            b2 = mutate_after(bars, k, seed)
            if other is None:
                out = fn(b2)
            else:
                # mutate the other market from the SAME wall-clock minute onward
                ko = int(np.searchsorted(other.ts, bars.ts[k])) if k < bars.n else other.n
                out = fn(b2, mutate_after(other, ko, seed + 1000))
            problems += [f"cut {k} seed {seed}: {p}" for p in prefix_differences(base, out, k)]
    return problems


def check_trade_causality(pipeline, bars: Bars, cuts, seeds=(0, 1)) -> list[str]:
    """pipeline(bars) -> Trades. Trades that EXITED before the cut must be identical."""
    problems = []
    t1 = pipeline(bars)
    for k in cuts:
        for seed in seeds:
            t2 = pipeline(mutate_after(bars, k, seed))
            m1, m2 = t1.exit_idx < k, t2.exit_idx < k
            a = (t1.entry_idx[m1], t1.exit_idx[m1], t1.side[m1], t1.entry_px[m1], t1.exit_px[m1])
            b = (t2.entry_idx[m2], t2.exit_idx[m2], t2.side[m2], t2.entry_px[m2], t2.exit_px[m2])
            if any(len(x) != len(y) or not np.array_equal(x, y) for x, y in zip(a, b)):
                problems.append(f"cut {k} seed {seed}: trades completed before the cut changed")
    return problems
