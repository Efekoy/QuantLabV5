"""Null / surrogate market generators.

A generator maps a market (instrument -> Bars) plus a seed to a NULL market with the
same timestamps, sessions and contract segments, and returns ordinary `Bars`
(source "null:<name>:<seed>"), which then enter the SAME evaluation pipeline as real
data. Generators never mutate their input and are deterministic in (input, seed).

Implemented at bootstrap (tested only on synthetic data):

  BlockSignFlipNull      block-based directional randomisation: each block of
                         `block_minutes` wall-clock minutes has its bar-to-bar price
                         moves multiplied by a random +-1 (high/low swap when flipped).
                         Magnitudes, volatility clustering, time-of-day profile and
                         volume are preserved; direction within a block is not.
                         joint=True: all instruments share the flip of each wall-clock
                         block, preserving contemporaneous NQ/ES co-movement signs.
  SessionPermutationNull day/block resampling: whole-session intraday paths (offsets
                         from the session open, plus volume) are permuted -- or drawn
                         with replacement -- among sessions with an identical minute
                         structure; levels are re-chained, gaps kept. joint=True
                         applies the same session mapping to every instrument.

Both work additively in price points, so tick multiples stay tick multiples. A path
that would go non-positive is REJECTED by the Bars integrity check, never repaired.
Roll gaps are preserved unflipped (they are not tradable moves).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from quantlab5.data.schema import Bars
from quantlab5.util.hashing import canonical_json, sha256_text


def _rng(seed: int, name: str, params: dict) -> np.random.Generator:
    mix = int(sha256_text(canonical_json([int(seed), name, params]))[:16], 16)
    return np.random.Generator(np.random.PCG64(mix))


def _seg_first(bars: Bars) -> np.ndarray:
    f = np.ones(bars.n, dtype=bool)
    if bars.n > 1:
        f[1:] = np.asarray(bars.seg)[1:] != np.asarray(bars.seg)[:-1]
    return f


class NullGenerator(ABC):
    name = "abstract"

    @abstractmethod
    def params(self) -> dict:
        ...

    @abstractmethod
    def _generate(self, market: dict[str, Bars], rng: np.random.Generator) -> dict[str, dict]:
        """Return instrument -> dict(o=, h=, l=, c=, v=) arrays."""

    def generate(self, market: dict[str, Bars], seed: int) -> dict[str, Bars]:
        rng = _rng(seed, self.name, self.params())
        arrays = self._generate(market, rng)
        tag = f"null:{self.name}:{seed}"
        return {k: market[k].with_prices(**arrays[k], source=tag) for k in market}


def flip_path(b: Bars, s: np.ndarray) -> dict:
    """Apply per-bar signs s (+1/-1) to bar-to-bar moves, preserving roll gaps."""
    o, h, l, c = (np.asarray(x, dtype=np.float64) for x in (b.o, b.h, b.l, b.c))
    s = np.asarray(s, dtype=np.float64)
    n = b.n
    if n == 0:
        return {"o": o, "h": h, "l": l, "c": c, "v": np.asarray(b.v)}
    first = _seg_first(b)
    c_prev = np.r_[np.nan, c[:-1]]
    ref = np.where(first, o, c_prev)                     # raw reference price of each bar's offsets
    gap = np.where(first, o - c_prev, 0.0)               # raw roll gap, kept unflipped
    gap[0] = 0.0
    step = np.where(first, gap + s * (c - o), s * (c - c_prev))
    c_new = np.empty(n)
    c_new[0] = o[0] + s[0] * (c[0] - o[0])
    c_new[1:] = c_new[0] + np.cumsum(step[1:])
    ref_new = np.where(first, np.r_[o[0], c_new[:-1]] + gap, np.r_[np.nan, c_new[:-1]])
    ref_new[0] = o[0]
    do, dh, dl = o - ref, h - ref, l - ref
    o_new = ref_new + s * do
    h_new = np.where(s > 0, ref_new + dh, ref_new - dl)
    l_new = np.where(s > 0, ref_new + dl, ref_new - dh)
    return {"o": o_new, "h": h_new, "l": l_new, "c": c_new, "v": np.asarray(b.v)}


class BlockSignFlipNull(NullGenerator):
    name = "block_sign_flip"

    def __init__(self, block_minutes: int = 30, joint: bool = True):
        if block_minutes < 1:
            raise ValueError("block_minutes >= 1")
        self.block_minutes = int(block_minutes)
        self.joint = bool(joint)

    def params(self) -> dict:
        return {"block_minutes": self.block_minutes, "joint": self.joint}

    def _generate(self, market, rng):
        out = {}
        if self.joint:
            blocks = np.unique(np.concatenate([np.asarray(b.tmin) // self.block_minutes for b in market.values()]))
            flips = rng.choice(np.array([-1.0, 1.0]), size=len(blocks))
            for k in sorted(market):
                b = market[k]
                s = flips[np.searchsorted(blocks, np.asarray(b.tmin) // self.block_minutes)]
                out[k] = flip_path(b, s)
        else:
            for k in sorted(market):
                b = market[k]
                ub, inv = np.unique(np.asarray(b.tmin) // self.block_minutes, return_inverse=True)
                s = rng.choice(np.array([-1.0, 1.0]), size=len(ub))[inv]
                out[k] = flip_path(b, s)
        return out


class SessionPermutationNull(NullGenerator):
    name = "session_permutation"

    def __init__(self, joint: bool = True, replace: bool = False):
        self.joint = bool(joint)
        self.replace = bool(replace)

    def params(self) -> dict:
        return {"joint": self.joint, "replace": self.replace}

    @staticmethod
    def sessions(b: Bars) -> dict[int, tuple[int, int]]:
        sd = np.asarray(b.sday)
        if b.n == 0:
            return {}
        cut = np.r_[0, np.nonzero(sd[1:] != sd[:-1])[0] + 1, b.n]
        return {int(sd[a]): (int(a), int(z)) for a, z in zip(cut[:-1], cut[1:])}

    def _mapping(self, days_by_sig: dict, rng) -> dict[int, int]:
        m = {}
        for sig in sorted(days_by_sig):
            days = sorted(days_by_sig[sig])
            src = rng.choice(days, size=len(days), replace=True) if self.replace else rng.permutation(days)
            m.update({d: int(x) for d, x in zip(days, src)})
        return m

    def _generate(self, market, rng):
        sess = {k: self.sessions(market[k]) for k in sorted(market)}
        groups = [sorted(market)] if self.joint else [[k] for k in sorted(market)]
        mapping: dict[str, dict[int, int]] = {}
        for grp in groups:
            common = set.intersection(*(set(sess[k]) for k in grp))
            by_sig: dict[str, list[int]] = {}
            for d in common:
                sig = sha256_text("|".join(np.asarray(market[k].sm)[slice(*sess[k][d])].tobytes().hex()
                                           for k in grp))
                by_sig.setdefault(sig, []).append(d)
            mp = self._mapping(by_sig, rng)
            for k in grp:
                mapping[k] = mp
        out = {}
        for k in sorted(market):
            b = market[k]
            o, h, l, c, v = (np.asarray(x, dtype=np.float64) for x in (b.o, b.h, b.l, b.c, b.v))
            no, nh, nl, nc, nv = o.copy(), h.copy(), l.copy(), c.copy(), v.copy()
            prev_raw_close = prev_new_close = None
            for d in sorted(sess[k]):
                a, z = sess[k][d]
                sa, sz = sess[k][mapping[k].get(d, d)]
                base = o[sa]
                # the slot keeps its own raw opening gap; its level is re-chained to the new previous close
                open_new = o[a] if prev_new_close is None else prev_new_close + (o[a] - prev_raw_close)
                no[a:z] = open_new + (o[sa:sz] - base)
                nh[a:z] = open_new + (h[sa:sz] - base)
                nl[a:z] = open_new + (l[sa:sz] - base)
                nc[a:z] = open_new + (c[sa:sz] - base)
                nv[a:z] = v[sa:sz]
                prev_raw_close, prev_new_close = c[z - 1], nc[z - 1]
            out[k] = {"o": no, "h": nh, "l": nl, "c": nc, "v": nv}
        return out


# ============================================================ V4 campaign nulls (session re-anchored)
from numba import njit as _njit  # noqa: E402


@_njit(cache=True)
def _rebuild(o, h, l, c, first, src, s):
    """Rebuild a path from per-bar offsets. Bar i takes the offsets of bar src[i] (relative to that bar's own
    reference: previous close, or its own open on a group's first bar), multiplied by sign s[i]
    (s = -1 swaps high/low). Each group (session x contract) restarts at the REAL open of its first bar."""
    n = len(o)
    no = np.empty(n)
    nh = np.empty(n)
    nl = np.empty(n)
    nc = np.empty(n)
    for i in range(n):
        j = src[i]
        refj = o[j] if (first[j] or j == 0) else c[j - 1]
        if first[i]:
            ref_new = o[i]
        else:
            ref_new = nc[i - 1]
        sg = s[i]
        no[i] = ref_new + sg * (o[j] - refj)
        nc[i] = ref_new + sg * (c[j] - refj)
        if sg > 0:
            nh[i] = ref_new + (h[j] - refj)
            nl[i] = ref_new + (l[j] - refj)
        else:
            nh[i] = ref_new - (l[j] - refj)
            nl[i] = ref_new - (h[j] - refj)
    return no, nh, nl, nc


def _group_first(b: Bars) -> np.ndarray:
    sd = np.asarray(b.sday)
    seg = np.asarray(b.seg)
    f = np.ones(b.n, dtype=bool)
    if b.n > 1:
        f[1:] = (sd[1:] != sd[:-1]) | (seg[1:] != seg[:-1])
    return f


def _apply(b: Bars, src: np.ndarray, s: np.ndarray) -> dict:
    o, h, l, c = (np.asarray(x, dtype=np.float64) for x in (b.o, b.h, b.l, b.c))
    first = _group_first(b)
    no, nh, nl, nc = _rebuild(o, h, l, c, first, src.astype(np.int64), s.astype(np.float64))
    return {"o": no, "h": nh, "l": nl, "c": nc, "v": np.asarray(b.v, np.float64)[src]}


class MinuteSignFlipNull(NullGenerator):
    """Null A (joint=False) / Null C (joint=True): every 1-minute bar's move is multiplied by an
    independent random sign (high/low swapped when flipped); sessions re-anchored at their real open.
    Preserves: |returns|, bar ranges, volatility clustering, intraday seasonality, volume and its link to
    |moves|, session structure, rolls. joint=True also preserves NQ/ES contemporaneous co-movement
    (same sign at the same minute) and common volatility/volume shocks.
    Destroys: every directional/serial predictability (autocorrelation, trends, lead-lag, signed-flow
    relations, reversals)."""
    name = "minute_sign_flip"

    def __init__(self, joint: bool):
        self.joint = bool(joint)

    def params(self) -> dict:
        return {"joint": self.joint, "reanchor": "session_open"}

    def _generate(self, market, rng):
        out = {}
        if self.joint:
            mins = np.unique(np.concatenate([np.asarray(b.tmin) for b in market.values()]))
            flips = rng.choice(np.array([-1.0, 1.0]), size=len(mins))
            for k in sorted(market):
                b = market[k]
                out[k] = _apply(b, np.arange(b.n), flips[np.searchsorted(mins, np.asarray(b.tmin))])
        else:
            for k in sorted(market):
                b = market[k]
                out[k] = _apply(b, np.arange(b.n), rng.choice(np.array([-1.0, 1.0]), size=b.n))
        return out


class TodBlockResampleNull(NullGenerator):
    """Null B: each session's `block_minutes` time-of-day blocks are replaced by the SAME clock block of a
    randomly drawn donor session (the same donor for every instrument when joint=True). Bars carry their
    own OHLC offsets and volume; sessions re-anchored at the real open; missing donor minutes keep the
    original bar. Preserves: realistic within-block paths and price-volume structure, time-of-day
    seasonality, NQ/ES contemporaneous structure (joint). Destroys: chronology across blocks and days
    (trend persistence beyond the block, overnight->RTH links, multi-block context, calendar links).
    NOT edge-free for effects that live entirely inside one block: a secondary, path-preserving null."""
    name = "tod_block_resample"

    def __init__(self, block_minutes: int = 30, joint: bool = True):
        self.block_minutes = int(block_minutes)
        self.joint = bool(joint)

    def params(self) -> dict:
        return {"block_minutes": self.block_minutes, "joint": self.joint, "reanchor": "session_open"}

    def _generate(self, market, rng):
        keys = sorted(market)
        days = np.unique(np.concatenate([np.asarray(market[k].sday) for k in keys]))
        nblk = 1380 // self.block_minutes + 1
        donors = {}
        if self.joint:
            d = rng.integers(0, len(days), size=(len(days), nblk))
            donors = {k: d for k in keys}
        else:
            donors = {k: rng.integers(0, len(days), size=(len(days), nblk)) for k in keys}
        out = {}
        for k in keys:
            b = market[k]
            si = np.searchsorted(days, np.asarray(b.sday))
            sm = np.asarray(b.sm).astype(np.int64)
            grid = np.full((len(days), 1380), -1, dtype=np.int64)
            grid[si, sm] = np.arange(b.n)
            dsess = donors[k][si, sm // self.block_minutes]
            src = grid[dsess, sm]
            src = np.where(src >= 0, src, np.arange(b.n))
            out[k] = _apply(b, src, np.ones(b.n))
        return out
