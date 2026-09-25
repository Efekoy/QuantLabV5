"""QuantLabV4 causal feature library, triggers and filters (frozen with the preregistration).

`compute_world(market)` returns a `WorldFeatures` holding:
  catalog   one spec per feature: name, version, family, required columns/instruments, lookback,
            warmup, session-reset rule, information time (bar close), parameters
  F         the ML feature subset at decision bars (float32)
  triggers  signed sparse events at decision bars: (trigger_id, family, params, positions, signs)
  bits_long / bits_short   uint64 filter bitmasks at decision bars (bit k = filter k satisfied for a
            trade in that direction; non-directional filters set the same bit in both)
  sym       symbolic-sequence codes at decision bars

Conventions
  * Every value at bar t uses bars <= t only (verified by tests/test_v4_features_causality.py).
  * Lookbacks never cross a session or a contract roll (group = session x contract segment),
    unless a feature explicitly says "across sessions" (volatility EWMAs, time-of-day baselines,
    prior-session levels), which use only EARLIER bars/sessions.
  * Volume-derived features are NaN inside the cleaning-v1 roll window; time-of-day volume
    baselines skip roll-window sessions.
  * Scale: sig1(t) = per-minute log-return scale = sqrt( sqrt(E_tod[r^2] * mean_30(r^2)) ), where
    E_tod is the mean of r^2 at the same session minute over the previous 20 sessions.
  * VWAP is a BAR-BASED approximation: sum(typical_price * volume)/sum(volume) with typical price
    (h+l+c)/3 per 1-minute bar. It is NOT transaction-level VWAP.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from numba import njit

from quantlab5.features import ops as O
from quantlab5.data.market import Market

FEATURE_LIB_VERSION = "featurelib_v4.0_2026-09-23"
RTH_OPEN = 930


@dataclass
class Trigger:
    tid: str
    family: str
    params: dict
    pos: np.ndarray       # int32 positions into market.dec (sorted)
    sign: np.ndarray      # int8 +1/-1


@dataclass
class Filter:
    fid: str
    group: str
    directional: bool
    bit: int
    description: str


@dataclass
class WorldFeatures:
    catalog: list = field(default_factory=list)
    F: dict = field(default_factory=dict)
    triggers: list = field(default_factory=list)
    filters: list = field(default_factory=list)
    bits_long: np.ndarray | None = None
    bits_short: np.ndarray | None = None
    sym: dict = field(default_factory=dict)
    stop_scale: np.ndarray | None = None    # points, per NQ bar (for exits)


ML_KEEP = {
    "retz_1", "retz_5", "retz_15", "retz_30", "retz_60", "retz_240", "dsma_60", "pos_range_60", "pos_range_240",
    "open_retz", "gapz", "trend_agree", "lrvol_1_k20", "lrvol_5_k20", "lrvol_15_k20", "lrvol_60_k20",
    "lrvol_cum_rth", "vol_mom", "vol_accel", "vol_conc_15", "vol_entropy_15", "sgnvol_15", "sgnvol_60",
    "clvvol_15", "obv_30", "pvt_30", "ret_per_vol_15", "dirvol_30", "vdist_rth", "vdist_glx", "vslope_rth",
    "er_5", "er_15", "er_60", "er_240", "ols_t_30", "ols_r2_60", "retr_30", "revs_30", "top3_60", "late_30",
    "rvratio_30", "semi_30", "skew_60", "kurt_60", "jr_60", "jz", "jcount_pos_30", "jcount_neg_30", "vr5_120",
    "ac1_120", "entropy_60", "vr_ch", "on_retz", "on_range", "on_lrvol", "on_er", "on_final30z", "pm_retz",
    "rel_lrvol_15", "corr_60", "corr_ch", "beta_120", "residz_15", "es_retz_15", "rsi_14", "macd_hist",
    "adx_14", "bb_pb", "tod", "dow", "sig1",
}


def _sessions(sday):
    u, inv = np.unique(np.asarray(sday), return_inverse=True)
    return u, inv.astype(np.int64)


def tod_expected(x, sidx, sm, S, K, exclude=None, min_frac=0.5):
    """E[x at this session-minute] over the previous K sessions (strictly earlier), skipping excluded."""
    X = np.full((S, 1380), np.nan)
    xv = np.asarray(x, dtype=np.float64).copy()
    if exclude is not None:
        xv[np.asarray(exclude, bool)] = np.nan
    X[sidx, sm] = xv
    fin = np.isfinite(X)
    cs = np.vstack([np.zeros((1, 1380)), np.cumsum(np.where(fin, X, 0.0), axis=0)])
    cc = np.vstack([np.zeros((1, 1380)), np.cumsum(fin, axis=0)])
    s = np.arange(S)
    lo = np.maximum(0, s - K)
    num = cs[s] - cs[lo]
    cnt = cc[s] - cc[lo]
    with np.errstate(invalid="ignore", divide="ignore"):
        E = np.where(cnt >= max(1, min_frac * K), num / cnt, np.nan)
    return E[sidx, sm]


class _Builder:
    def __init__(self, m: Market):
        self.m = m
        b = m.nq
        self.n = b.n
        self.g = m.gid
        self.dec = m.dec
        self.pos = np.full(self.n, -1, dtype=np.int64)
        self.pos[self.dec] = np.arange(len(self.dec))
        self.W = WorldFeatures()
        self._bl = np.zeros(len(self.dec), dtype=np.uint64)
        self._bs = np.zeros(len(self.dec), dtype=np.uint64)
        self._nbits = 0

    # ---------------------------------------------------------------- registration
    def feat(self, name, family, arr, lookback, cols=("c",), inst=("NQ",), reset="session+roll", params=None,
             warmup=None):
        self.W.catalog.append({"name": name, "version": "1", "family": family, "required_columns": list(cols),
                               "instruments": list(inst), "lookback_bars": lookback,
                               "warmup_bars": lookback if warmup is None else warmup, "session_reset": reset,
                               "information_time": "bar_close", "params": params or {}})
        if name in ML_KEEP:
            self.W.F[name] = np.asarray(arr, dtype=np.float64)[self.dec].astype(np.float32)
        return arr

    def trig(self, family, name, params, up, dn=None, sign=None):
        """up/dn: boolean masks (full length) for +1 / -1 events; or up=mask with sign array."""
        up = np.asarray(up, dtype=bool)
        if sign is not None:
            s = np.sign(np.nan_to_num(np.asarray(sign, dtype=np.float64)))
            ev = up & (s != 0)
            sg = s
        else:
            dn = np.zeros(self.n, bool) if dn is None else np.asarray(dn, dtype=bool)
            ev = up ^ dn
            sg = np.where(up, 1.0, -1.0)
        idx = np.nonzero(ev & (self.pos >= 0))[0]
        pid = f"{family}:{name}:" + ",".join(f"{k}={v}" for k, v in sorted(params.items()))
        self.W.triggers.append(Trigger(pid, family, dict(params, name=name),
                                       self.pos[idx].astype(np.int32), sg[idx].astype(np.int8)))

    def filt(self, fid, group, long_mask, short_mask=None, description=""):
        k = self._nbits
        if k >= 64:
            raise ValueError("more than 64 filter bits")
        lm = np.asarray(long_mask, dtype=bool)[self.dec]
        sm_ = lm if short_mask is None else np.asarray(short_mask, dtype=bool)[self.dec]
        bit = np.uint64(1) << np.uint64(k)
        self._bl[lm] |= bit
        self._bs[sm_] |= bit
        self.W.filters.append(Filter(fid, group, short_mask is not None, k, description))
        self._nbits += 1

    # ---------------------------------------------------------------- helpers
    def lag(self, x, k=1):
        return O.lag(x, k, self.g)

    def xup(self, f, thr):
        f = np.asarray(f, dtype=np.float64)
        p = self.lag(f)
        return (f > thr) & (p <= thr)

    def xdn(self, f, thr):
        f = np.asarray(f, dtype=np.float64)
        p = self.lag(f)
        return (f < thr) & (p >= thr)

    def enter(self, cond):
        """True on the first bar a condition becomes true (was false/undefined on the previous bar)."""
        cond = np.asarray(cond, dtype=bool)
        prev = self.lag(cond.astype(np.float64))
        return cond & ~(prev == 1.0)

    def signed_cross(self, family, name, f, thr, params):
        self.trig(family, name, dict(params, thr=thr), self.xup(f, thr), self.xdn(f, -thr))


CHUNK_SESSIONS = 150
WARMUP_SESSIONS = 125          # >= the longest cross-session dependency (120-session tod baseline)


def compute_world(m: Market, chunk_sessions: int = CHUNK_SESSIONS, warmup_sessions: int = WARMUP_SESSIONS
                  ) -> WorldFeatures:
    """Compute on the whole market, or (to bound memory) in chunks of sessions, each preceded by a
    warm-up of earlier sessions. Values in a chunk depend only on the chunk's own past bars."""
    sday = np.asarray(m.nq.sday)
    days = np.unique(sday)
    with np.errstate(all="ignore"):
        if len(days) <= chunk_sessions + warmup_sessions:
            return _compute(m)
        return _compute_chunked(m, days, chunk_sessions, warmup_sessions)


def _submarket(m: Market, d0, d1):
    from quantlab5.data.market import build_market
    sday = np.asarray(m.nq.sday)
    a, b = np.searchsorted(sday, d0, "left"), np.searchsorted(sday, d1, "right")
    es_sd = np.asarray(m.es.sday)
    ea, eb = np.searchsorted(es_sd, d0, "left"), np.searchsorted(es_sd, d1, "right")
    return build_market(m.nq.slice(a, b), m.es.slice(ea, eb), m.nq_symbols[a:b], m.es_symbols[ea:eb]), a


def _compute_chunked(m, days, chunk, warm):
    out = WorldFeatures()
    nd = len(m.dec)
    out.bits_long = np.zeros(nd, np.uint64)
    out.bits_short = np.zeros(nd, np.uint64)
    out.stop_scale = np.full(m.n, np.nan)
    trig_parts, F_parts, sym_parts = None, {}, {}
    for s0 in range(0, len(days), chunk):
        s1 = min(s0 + chunk, len(days))
        sub, off = _submarket(m, days[max(0, s0 - warm)], days[s1 - 1])
        W = _compute(sub)
        first_bar = int(np.searchsorted(np.asarray(m.nq.sday), days[s0], "left")) - off
        keep = sub.dec >= first_bar                      # decision bars belonging to this chunk's data part
        gdec = sub.dec[keep] + off
        gpos = np.searchsorted(m.dec, gdec)
        if not np.array_equal(m.dec[gpos], gdec):
            raise RuntimeError("chunked decision bars do not match the full market")
        kidx = np.nonzero(keep)[0]
        k0 = int(kidx[0]) if len(kidx) else len(sub.dec)
        out.bits_long[gpos] = W.bits_long[keep]
        out.bits_short[gpos] = W.bits_short[keep]
        lo = first_bar
        out.stop_scale[off + lo: off + sub.n] = W.stop_scale[lo:]
        if trig_parts is None:
            out.catalog, out.filters = W.catalog, W.filters
            trig_parts = [(t.tid, t.family, t.params, [], []) for t in W.triggers]
        for tp, t in zip(trig_parts, W.triggers):
            sel = t.pos >= k0
            tp[3].append(gpos[0] + (t.pos[sel] - k0) if len(gpos) else t.pos[sel][:0])
            tp[4].append(t.sign[sel])
        for k, v in W.F.items():
            F_parts.setdefault(k, []).append(v[keep])
        for k, v in W.sym.items():
            sym_parts.setdefault(k, []).append(v[keep])
        del W, sub
    out.triggers = [Trigger(tid, fam, prm, np.concatenate(p).astype(np.int32), np.concatenate(s).astype(np.int8))
                    for tid, fam, prm, p, s in trig_parts]
    out.F = {k: np.concatenate(v) for k, v in F_parts.items()}
    out.sym = {k: np.concatenate(v) for k, v in sym_parts.items()}
    return out


def _compute(m: Market) -> WorldFeatures:
    B = _Builder(m)
    b = m.nq
    g = B.g
    n = B.n
    o, h, l, c = (np.asarray(x, dtype=np.float64) for x in (b.o, b.h, b.l, b.c))
    v = np.asarray(b.v, dtype=np.float64)
    sm = np.asarray(b.sm).astype(np.int64)
    sday = np.asarray(b.sday).astype(np.int64)
    days, sidx = _sessions(sday)
    S = len(days)
    rw = m.rw
    vv = np.where(rw, np.nan, v)                 # volume masked in the roll window
    rth = sm >= RTH_OPEN
    gstart = O.group_start(g)
    pig = np.arange(n) - gstart                  # bars since group start

    # ------------------------------------------------ base scales
    r1 = np.log(c / B.lag(c))
    pc = B.lag(c)
    tr = np.where(np.isfinite(pc), np.maximum(h, pc) - np.minimum(l, pc), h - l)
    er2 = tod_expected(r1 ** 2, sidx, sm, S, 20)
    rv30m = O.rmean(r1 ** 2, 30, g, 0.5)
    var1 = np.sqrt(er2 * rv30m)
    var1 = np.where(np.isfinite(var1) & (var1 > 0), var1, er2)
    sig1 = np.sqrt(var1)
    etr = tod_expected(tr, sidx, sm, S, 20)
    atr30 = O.rmean(tr, 30, g, 0.5)
    stop_scale = np.sqrt(etr * atr30)
    stop_scale = np.where(np.isfinite(stop_scale) & (stop_scale > 0), stop_scale, etr)
    B.W.stop_scale = stop_scale
    sigL = np.sqrt(O.ewm_across_sessions(r1 ** 2, 6000, b.seg, 1000))
    B.feat("sig1", "BASE", sig1, 30, params={"tod_sessions": 20, "recent_bars": 30}, reset="across sessions (earlier only)")
    B.feat("stop_scale", "BASE", stop_scale, 30, cols=("h", "l", "c"), reset="across sessions (earlier only)")

    # ================================================= A. RETURNS AND PRICE
    retz = {}
    for H in (1, 5, 15, 30, 60, 120, 240):
        z = np.log(c / B.lag(c, H)) / (sig1 * np.sqrt(H))
        retz[H] = B.feat(f"retz_{H}", "RET", z, H, params={"H": H})
    for H in (1, 5, 15, 30, 60):
        for thr in (1.5, 2.0, 2.5, 3.0):
            B.signed_cross("RET", "retz_cross", retz[H], thr, {"H": H})
    for H in (15, 60, 240):
        B.feat(f"dsma_{H}", "RET", np.log(c / O.rmean(c, H, g)) / (sig1 * np.sqrt(H)), H, params={"H": H})
    pos_range = {}
    for H in (15, 60, 240):
        hh, ll = O.rmax(h, H, g), O.rmin(l, H, g)
        pos_range[H] = B.feat(f"pos_range_{H}", "RET", (c - ll) / (hh - ll), H, cols=("h", "l", "c"), params={"H": H})
    rth_open = O.last_value_where(sm == RTH_OPEN, o, g)
    rth_open = np.where(rth, rth_open, np.nan)
    mins_open = np.maximum(sm - RTH_OPEN + 1, 1)
    open_retz = B.feat("open_retz", "RET", np.log(c / rth_open) / (sig1 * np.sqrt(mins_open)), 390,
                       cols=("o", "c"), params={"anchor": "09:30 open"})
    for thr in (1.0, 1.5, 2.0):
        B.signed_cross("RET", "open_retz_cross", open_retz, thr, {})
    glx_open = o[gstart]
    B.feat("glx_retz", "RET", np.log(c / glx_open) / (sigL * np.sqrt(pig + 1)), 1380, cols=("o", "c"),
           params={"anchor": "session open 18:00"})
    trend_agree = sum(np.sign(np.nan_to_num(retz[H])) for H in (5, 15, 60, 240))
    trend_agree = np.where(np.isfinite(retz[240]), trend_agree, np.nan)
    B.feat("trend_agree", "RET", trend_agree, 240, params={"H": [5, 15, 60, 240]})
    B.trig("RET", "trend_agree_full", {}, B.xup(trend_agree, 3.5), B.xdn(trend_agree, -3.5))
    # prior RTH close (last bar before 16:00 of the previous session with RTH bars)
    last_rth = pd.Series(np.where(rth & (sm < 1320), np.arange(n), -1)).groupby(sidx).max().to_numpy()
    prev_close_by_s = np.full(S, np.nan)
    ok = last_rth[:-1] >= 0
    prev_close_by_s[1:][ok] = c[last_rth[:-1][ok]]
    prev_close = prev_close_by_s[sidx]
    gapz = B.feat("gapz", "RET", np.log(c / prev_close) / (sigL * np.sqrt(1380)), 1380, reset="prior session close",
                  params={"ref": "prior session last RTH close"})

    # ================================================= B. VOLUME AND PARTICIPATION
    Ev = {K: tod_expected(v, sidx, sm, S, K, exclude=rw) for K in (10, 20, 60, 120)}
    lrv = {}

    def rvol(W, K):
        return O.rsum(vv, W, g) / O.rsum(Ev[K], W, g)

    for W in (1, 3, 5, 10, 15, 30, 60):
        lrv[(W, 20)] = B.feat(f"lrvol_{W}_k20", "VOL", np.log(rvol(W, 20)), W, cols=("v",), params={"W": W, "K": 20},
                              reset="window in session; baseline previous 20 sessions (roll window excluded)")
    for W in (5, 15, 30):
        for K in (10, 60, 120):
            lrv[(W, K)] = B.feat(f"lrvol_{W}_k{K}", "VOL", np.log(rvol(W, K)), W, cols=("v",), params={"W": W, "K": K})
    cum_v = O.cum_in_group(vv, g, sm == RTH_OPEN)
    cum_e = O.cum_in_group(Ev[20], g, sm == RTH_OPEN)
    lrv_cum_rth = B.feat("lrvol_cum_rth", "VOL", np.where(rth, np.log(cum_v / cum_e), np.nan), 390, cols=("v",))
    lrv_cum_sess = B.feat("lrvol_cum_sess", "VOL", np.log(O.cum_in_group(vv, g) / O.cum_in_group(Ev[20], g)), 1380,
                          cols=("v",))
    vol_mom = B.feat("vol_mom", "VOL", lrv[(5, 20)] - lrv[(60, 20)], 60, cols=("v",))
    vol_accel = B.feat("vol_accel", "VOL", lrv[(5, 20)] - B.lag(lrv[(5, 20)], 5), 10, cols=("v",))
    _, vslope_t, _, _ = O.rolling_ols(np.log1p(vv), 15, g)
    B.feat("vol_slope_t15", "VOL", vslope_t, 15, cols=("v",))
    s15 = O.rsum(vv, 15, g)
    vol_conc = B.feat("vol_conc_15", "VOL", O.rmax(vv, 15, g) / s15, 15, cols=("v",))
    B.feat("vol_conc_60", "VOL", O.rmax(vv, 60, g) / O.rsum(vv, 60, g), 60, cols=("v",))
    vlogv = O.rsum(np.where(vv > 0, vv * np.log(vv), 0.0), 15, g)
    B.feat("vol_entropy_15", "VOL", -(vlogv / s15 - np.log(s15)) / np.log(15), 15, cols=("v",))
    dc = c - pc
    sgn_bar = np.sign(c - o)
    clv = np.where(h > l, ((c - l) - (h - c)) / (h - l), 0.0)
    sgnvol, clvvol, obv = {}, {}, {}
    for W in (15, 60):
        sv = O.rsum(vv, W, g)
        B.feat(f"upvol_{W}", "VOL", O.rsum(vv * (c > o), W, g) / sv, W, cols=("o", "c", "v"))
        sgnvol[W] = B.feat(f"sgnvol_{W}", "VOL", O.rsum(vv * sgn_bar, W, g) / sv, W, cols=("o", "c", "v"))
        clvvol[W] = B.feat(f"clvvol_{W}", "VOL", O.rsum(vv * clv, W, g) / sv, W, cols=("h", "l", "c", "v"))
    for W in (30, 120):
        obv[W] = B.feat(f"obv_{W}", "VOL", O.rsum(vv * np.sign(dc), W, g) / O.rsum(vv, W, g), W, cols=("c", "v"))
    B.feat("pvt_30", "VOL", O.rsum(vv * r1, 30, g) / O.rsum(vv, 30, g) / sig1, 30, cols=("c", "v"))
    rv15 = np.exp(lrv[(15, 20)])
    B.feat("ret_per_vol_15", "VOL", np.abs(retz[15]) / rv15, 15, cols=("c", "v"))
    rng15 = (O.rmax(h, 15, g) - O.rmin(l, 15, g)) / (c * sig1 * np.sqrt(15))
    B.feat("range_per_vol_15", "VOL", rng15 / rv15, 15, cols=("h", "l", "c", "v"))
    er15_tmp = (c - B.lag(c, 15)) / O.rsum(np.abs(dc), 15, g)
    B.feat("er_per_vol_15", "VOL", np.abs(er15_tmp) / rv15, 15, cols=("c", "v"))
    net30 = np.sign(c - B.lag(c, 30))
    vdir = O.rsum(vv * (np.sign(dc) == net30), 30, g)
    vopp = O.rsum(vv * (np.sign(dc) == -net30), 30, g)
    dirvol = B.feat("dirvol_30", "VOL", np.log((vdir + 1) / (vopp + 1)), 30, cols=("c", "v"))
    B.feat("vol_expansion", "VOL", lrv[(15, 20)] - B.lag(lrv[(15, 20)], 15), 30, cols=("v",))
    # triggers VOL
    for W in (1, 5, 15):
        for thr in (2.0, 3.0, 5.0):
            B.trig("VOL", "rvol_cross_up", {"W": W, "thr": thr}, B.xup(lrv[(W, 20)], np.log(thr)),
                   sign=c - B.lag(c, W))
    for thr in (1.0, 1.5):
        B.trig("VOL", "vol_accel_up", {"thr": thr}, B.xup(vol_accel, thr), sign=retz[5])
    for W in (15, 60):
        for thr in (0.3, 0.5):
            B.signed_cross("VOL", "sgnvol_cross", sgnvol[W], thr, {"W": W})
            B.signed_cross("VOL", "clvvol_cross", clvvol[W], thr, {"W": W})
    for W in (30, 120):
        for thr in (0.2, 0.35):
            B.signed_cross("VOL", "obv_cross", obv[W], thr, {"W": W})
    for thr in (0.35, 0.5):
        B.trig("VOL", "vol_conc_spike", {"thr": thr}, B.xup(vol_conc, thr), sign=retz[1])
    for thr in (2.0, 3.0):
        absorb = (rv15 > thr) & (np.abs(retz[15]) < 0.5)
        B.trig("VOL", "absorption", {"rvol": thr}, B.enter(absorb), sign=clvvol[15])
    for thr in (0.7, 1.2):
        B.trig("VOL", "dirvol_cross", {"thr": thr}, B.xup(dirvol, thr), sign=net30)

    # ================================================= C. VWAP (bar-based approximation)
    tp = (h + l + c) / 3.0
    vw_rth = O.cum_in_group(tp * v, g, sm == RTH_OPEN) / O.cum_in_group(v, g, sm == RTH_OPEN)
    vw_rth = np.where(rth, vw_rth, np.nan)
    vw_glx = O.cum_in_group(tp * v, g) / O.cum_in_group(v, g)
    vdist = {}
    for nm, vw in (("rth", vw_rth), ("glx", vw_glx)):
        vdist[nm] = B.feat(f"vdist_{nm}", "VWAP", np.log(c / vw) / (sig1 * np.sqrt(30)), 1,
                           cols=("h", "l", "c", "v"), reset="anchored at 09:30" if nm == "rth" else "anchored at 18:00",
                           params={"approximation": "bar typical price"})
    vslope = B.feat("vslope_rth", "VWAP", np.log(vw_rth / B.lag(vw_rth, 15)) / (sig1 * np.sqrt(15)), 15,
                    cols=("h", "l", "c", "v"))
    for nm, vw in (("rth", vw_rth), ("glx", vw_glx)):
        side = np.sign(c - vw)
        up = (side > 0) & (B.lag(side) < 0)
        dn = (side < 0) & (B.lag(side) > 0)
        B.trig("VWAP", "cross", {"anchor": nm}, up, dn)
        for thr in (1.5, 2.0, 3.0):
            B.signed_cross("VWAP", "dist_cross", vdist[nm], thr, {"anchor": nm})
        if nm == "rth":
            s_series = pd.Series(np.nan_to_num(side))
            grp = (s_series != s_series.shift()).cumsum() + pd.Series(g) * 0
            run = s_series.groupby([pd.Series(g), grp]).cumcount().to_numpy() + 1
            prev_run = B.lag(run.astype(float))
            for N in (15, 30):
                B.trig("VWAP", "reclaim", {"anchor": nm, "N": N}, up & (prev_run >= N), dn & (prev_run >= N))
            for N in (5, 10):
                B.trig("VWAP", "acceptance", {"anchor": nm, "N": N}, (run == N) & (side > 0), (run == N) & (side < 0))
            B.feat("vside_run_rth", "VWAP", run * side, 30, cols=("c", "v"))
        touch = (l <= vw) & (h >= vw)
        prior_above = B.lag(np.sign(c - vw)) > 0
        prior_below = B.lag(np.sign(c - vw)) < 0
        B.trig("VWAP", "rejection", {"anchor": nm}, touch & prior_above & (c > vw), touch & prior_below & (c < vw))
    for thr in (1.0, 2.0):
        B.signed_cross("VWAP", "slope_cross", vslope, thr, {})
    # ES VWAP state vs NQ (for filters / XMKT)
    etp = (m.eh + m.el + m.ec) / 3.0
    ev0 = np.nan_to_num(m.ev)
    evw = O.cum_in_group(np.nan_to_num(etp) * ev0, g, sm == RTH_OPEN) / O.cum_in_group(ev0, g, sm == RTH_OPEN)
    es_vside = np.where(rth, np.sign(m.ec - evw), np.nan)
    B.feat("es_vside_rth", "VWAP", es_vside, 1, inst=("ES",), cols=("h", "l", "c", "v"))
    B.feat("vwap_state_disagree", "VWAP", np.sign(np.nan_to_num(vdist["rth"])) - np.nan_to_num(es_vside), 1,
           inst=("NQ", "ES"))

    # ================================================= D. PATH GEOMETRY
    er = {}
    for H in (5, 15, 30, 60, 120, 240):
        er[H] = B.feat(f"er_{H}", "PATH", (c - B.lag(c, H)) / O.rsum(np.abs(dc), H, g), H, params={"H": H})
    olst, olsr2 = {}, {}
    for H in (15, 30, 60, 120):
        slope, t, r2, rsd = O.rolling_ols(c, H, g)
        olst[H] = B.feat(f"ols_t_{H}", "PATH", t, H, params={"H": H})
        olsr2[H] = B.feat(f"ols_r2_{H}", "PATH", r2, H, params={"H": H}) * 1.0
        B.feat(f"ols_resid_{H}", "PATH", rsd / (c * sig1), H, params={"H": H})
    ps = {}
    for H in (15, 30, 60, 120):
        retr, revs, dfrac, run, big1, top3, early, late = O.path_stats(c, H, g)
        ps[H] = dict(retr=retr, revs=revs, dfrac=dfrac, run=run, big1=big1, top3=top3, early=early, late=late)
        for k, arr in ps[H].items():
            B.feat(f"{k}_{H}", "PATH", arr, H, params={"H": H})
    body30 = B.feat("body_30", "PATH", O.rsum(c - o, 30, g) / (c - B.lag(c, 30)), 30, cols=("o", "c"))
    B.feat("wick_30", "PATH", O.rsum((h - l) - np.abs(c - o), 30, g) / O.rsum(h - l, 30, g), 30, cols=("o", "h", "l", "c"))
    B.feat("hhi_30", "PATH", O.rsum(dc ** 2, 30, g) / O.rsum(np.abs(dc), 30, g) ** 2, 30)
    for H in (15, 30, 60, 120):
        for thr in (0.5, 0.7):
            B.signed_cross("PATH", "er_cross", er[H], thr, {"H": H})
    for H in (15, 30, 60):
        for thr in (3.0, 5.0):
            B.signed_cross("PATH", "ols_t_cross", olst[H], thr, {"H": H})
    for H in (30, 60):
        for thr in (0.7, 0.85):
            B.trig("PATH", "r2_cross", {"H": H, "thr": thr}, B.xup(olsr2[H], thr), sign=olst[H])
        rz = retz[H]
        B.trig("PATH", "clean_trend", {"H": H}, B.enter((np.abs(rz) > 1.5) & (ps[H]["retr"] < 0.25)), sign=rz)
        B.trig("PATH", "low_concentration_trend", {"H": H}, B.enter((np.abs(rz) > 1.5) & (ps[H]["top3"] < 0.3)), sign=rz)
        B.trig("PATH", "late_acceleration", {"H": H}, B.enter((np.abs(rz) > 1.5) & (ps[H]["late"] > 0.6)), sign=rz)
    for N in (6, 8):
        B.trig("PATH", "directional_run", {"H": 30, "N": N}, B.xup(ps[30]["run"], N - 0.5), sign=retz[30])
    B.trig("PATH", "body_dominance", {"H": 30}, B.enter((np.abs(retz[30]) > 1.5) & (body30 > 0.8)), sign=retz[30])

    # ================================================= E. RETURN DISTRIBUTION
    semi, rvr = {}, {}
    rpos = np.where(r1 > 0, r1 ** 2, 0.0)
    rneg = np.where(r1 < 0, r1 ** 2, 0.0)
    for W in (15, 30, 60, 120):
        RV = O.rsum(r1 ** 2, W, g)
        rvr[W] = B.feat(f"rvratio_{W}", "DIST", RV / O.rsum(er2, W, g), W, reset="window in session; tod baseline 20 sessions")
        semi[W] = B.feat(f"semi_{W}", "DIST", (O.rsum(rpos, W, g) - O.rsum(rneg, W, g)) / RV, W)
        B.feat(f"skew_{W}", "DIST", O.rsum(r1 ** 3, W, g) * np.sqrt(W) / RV ** 1.5, W)
        B.feat(f"kurt_{W}", "DIST", W * O.rsum(r1 ** 4, W, g) / RV ** 2, W)
        B.feat(f"mabs_{W}", "DIST", O.rmean(np.abs(r1), W, g) / sig1, W)
    tailf = {}
    for W in (30, 60):
        tailf[W] = B.feat(f"tailfreq_{W}", "DIST", O.rmean((np.abs(r1) > 3 * sig1).astype(float), W, g), W)
    B.feat("maxpos_30", "DIST", O.rmax(r1, 30, g) / sig1, 30)
    B.feat("maxneg_30", "DIST", O.rmin(r1, 30, g) / sig1, 30)
    skew = {W: O.rsum(r1 ** 3, W, g) * np.sqrt(W) / O.rsum(r1 ** 2, W, g) ** 1.5 for W in (60, 120)}
    for W in (30, 60):
        for thr in (0.5, 0.7):
            B.signed_cross("DIST", "semi_cross", semi[W], thr, {"W": W})
    for W in (60, 120):
        for thr in (1.0, 2.0):
            B.signed_cross("DIST", "skew_cross", skew[W], thr, {"W": W})
    for W in (15, 30):
        for thr in (2.0, 3.0):
            B.trig("DIST", "rv_shock", {"W": W, "thr": thr}, B.xup(rvr[W], thr), sign=retz[W])
    for W in (30, 60):
        B.trig("DIST", "tail_cluster", {"W": W}, B.xup(tailf[W], 0.1), sign=retz[W])

    # ================================================= F. JUMPS (bipower-variation based)
    absr = np.abs(r1)
    BV60 = (np.pi / 2) * O.rsum(absr * B.lag(absr), 60, g)
    sig_bv = np.sqrt(B.lag(BV60) / 59.0)
    jz = B.feat("jz", "JUMP", r1 / sig_bv, 61, params={"bv_window": 60, "uses": "previous bars only for scale"})
    jr = {}
    for W in (30, 60):
        RV = O.rsum(r1 ** 2, W, g)
        BV = (np.pi / 2) * O.rsum(absr * B.lag(absr), W, g)
        jr[W] = B.feat(f"jr_{W}", "JUMP", np.maximum(RV - BV, 0) / RV, W, params={"W": W})
    j4p = (jz > 4).astype(float)
    j4n = (jz < -4).astype(float)
    jcp = B.feat("jcount_pos_30", "JUMP", O.rsum(j4p, 30, g, 0.5), 30)
    jcn = B.feat("jcount_neg_30", "JUMP", O.rsum(j4n, 30, g, 0.5), 30)
    jany = (np.abs(jz) > 4)
    B.feat("bars_since_jump", "JUMP", O.bars_since(jany, g), 1380)
    last_jsign = O.last_value_where(jany, np.sign(jz), g)
    for thr in (4.0, 6.0):
        B.trig("JUMP", "jump_bar", {"thr": thr}, jz > thr, jz < -thr)
    B.trig("JUMP", "double_jump_same_dir", {}, B.xup(jcp, 1.5), B.xup(jcn, 1.5))
    B.trig("JUMP", "opposing_jumps", {}, jany & (jcp >= 1) & (jcn >= 1), sign=np.sign(jz))
    er30l = B.lag(er[30])
    B.trig("JUMP", "trend_then_jump_same", {}, jany & (er30l * np.sign(jz) > 0.5), sign=np.sign(jz))
    B.trig("JUMP", "trend_then_jump_against", {}, jany & (er30l * np.sign(jz) < -0.5), sign=np.sign(jz))
    bsj = O.bars_since(jany, g)
    cont = (bsj >= 10) & (bsj <= 30) & (er[5] * last_jsign > 0.6)
    B.trig("JUMP", "jump_then_smooth", {}, B.enter(cont), sign=last_jsign)
    for thr in (0.4, 0.6):
        B.trig("JUMP", "jr_cross", {"W": 60, "thr": thr}, B.xup(jr[60], thr), sign=retz[60])
    # ES jumps
    er1 = np.log(m.ec / O.lag(m.ec, 1, g))
    eabs = np.abs(er1)
    eBV = (np.pi / 2) * O.rsum(eabs * O.lag(eabs, 1, g), 60, g, 0.9)
    ejz = er1 / np.sqrt(O.lag(eBV, 1, g) / 59.0)
    B.feat("es_jz", "JUMP", ejz, 61, inst=("ES",))
    B.trig("JUMP", "nq_only_jump", {}, (np.abs(jz) > 4) & (np.abs(ejz) < 2), sign=jz)
    B.trig("JUMP", "es_only_jump", {}, (np.abs(ejz) > 4) & (np.abs(jz) < 2), sign=ejz)
    B.trig("JUMP", "joint_jump", {}, (np.abs(jz) > 4) & (np.abs(ejz) > 4) & (np.sign(jz) == np.sign(ejz)), sign=jz)

    # ================================================= G. PERSISTENCE AND STATE TRANSITIONS
    R2_120 = O.rsum(r1 ** 2, 120, g)
    r5 = np.log(c / B.lag(c, 5))
    r15 = np.log(c / B.lag(c, 15))
    vr5 = B.feat("vr5_120", "PERS", O.rsum(r5 ** 2, 120, g) / (5 * R2_120), 125)
    B.feat("vr15_120", "PERS", O.rsum(r15 ** 2, 120, g) / (15 * R2_120), 135)
    B.feat("vr5_60", "PERS", O.rsum(r5 ** 2, 60, g) / (5 * O.rsum(r1 ** 2, 60, g)), 65)
    r1l = B.lag(r1)
    ac120 = B.feat("ac1_120", "PERS", O.rolling_corr(r1, r1l, 120, g), 121)
    B.feat("ac1_30", "PERS", O.rolling_corr(r1, r1l, 30, g), 31)
    B.feat("sac1_60", "PERS", O.rolling_corr(np.sign(r1), np.sign(r1l), 60, g), 61)
    up = (dc > 0).astype(float)
    pat = up + 2 * B.lag(up) + 4 * B.lag(up, 2)
    ent = np.zeros(n)
    for k in range(8):
        pk = O.rmean((pat == k).astype(float), 60, g)
        ent -= np.where(pk > 0, pk * np.log(pk), 0.0)
    ent = np.where(np.isfinite(pat) & (pig >= 62), ent / np.log(8), np.nan)
    ent = B.feat("entropy_60", "PERS", ent, 62)
    vr_ch = B.feat("vr_ch", "PERS", vr5 - B.lag(vr5, 30), 155)
    B.feat("ac_ch", "PERS", ac120 - B.lag(ac120, 30), 151)
    B.feat("er_ch", "PERS", np.abs(er[30]) - B.lag(np.abs(er[30]), 30), 60)
    B.feat("ent_ch", "PERS", ent - B.lag(ent, 30), 92)
    B.feat("rvol_ch", "PERS", lrv[(15, 20)] - B.lag(lrv[(15, 20)], 30), 45, cols=("v",))
    B.feat("volreg_ch", "PERS", np.log(rvr[30]) - B.lag(np.log(rvr[30]), 30), 60)
    s30 = retz[30]
    lagk = lambda x: B.lag(x, 30)  # noqa: E731
    for hi, lo_ in ((1.2, 0.9), (1.4, 1.0)):
        B.trig("PERS", "vr_low_to_high", {"hi": hi, "lo": lo_}, B.enter((vr5 > hi) & (lagk(vr5) < lo_)), sign=s30)
    B.trig("PERS", "vr_high_to_low", {}, B.enter((vr5 < 0.8) & (lagk(vr5) > 1.1)), sign=s30)
    B.trig("PERS", "ac_neg_to_pos", {}, B.enter((ac120 > 0.05) & (lagk(ac120) < -0.05)), sign=s30)
    B.trig("PERS", "ac_pos_to_neg", {}, B.enter((ac120 < -0.05) & (lagk(ac120) > 0.05)), sign=s30)
    for thr in (0.5, 0.7):
        B.trig("PERS", "er_low_to_high", {"thr": thr}, B.enter((np.abs(er[30]) > thr) & (lagk(np.abs(er[30])) < 0.2)),
               sign=s30)
    B.trig("PERS", "entropy_high_to_low", {}, B.enter((ent < 0.85) & (lagk(ent) > 0.95)), sign=s30)
    B.trig("PERS", "rvol_normal_to_abnormal", {}, B.enter((rv15 > 2) & (lagk(rv15) < 1.2)), sign=s30)
    B.trig("PERS", "vol_low_to_high", {}, B.enter((rvr[30] > 1.5) & (lagk(rvr[30]) < 0.8)), sign=s30)
    B.trig("PERS", "choppy_to_directional", {}, B.enter((lagk(ps[30]["revs"]) > 0.5) & (np.abs(er[30]) > 0.5)), sign=s30)
    vr_on = O.bars_since(B.xup(vr5, 1.1), g)
    vr_mature = O.bars_since(vr5 < 1.1, g)
    mom = B.xup(np.abs(s30), 1.5)
    B.trig("PERS", "momentum_at_persistence_onset", {}, mom & (vr_on <= 15) & (vr5 > 1.1), sign=s30)
    B.trig("PERS", "momentum_in_mature_persistence", {}, mom & (vr_mature > 60), sign=s30)

    # ================================================= I. OVERNIGHT AND OPENING
    onm = sm < RTH_OPEN
    idx_on_last = pd.Series(np.where(onm, np.arange(n), -1)).groupby(sidx).max().to_numpy()
    idx_first = pd.Series(np.arange(n)).groupby(sidx).min().to_numpy()
    has_on = idx_on_last >= 0
    li = np.where(has_on, idx_on_last, 0)
    on_hi = pd.Series(np.where(onm, h, -np.inf)).groupby(sidx).max().to_numpy()
    on_lo = pd.Series(np.where(onm, l, np.inf)).groupby(sidx).min().to_numpy()
    on_cnt = pd.Series(onm.astype(float)).groupby(sidx).sum().to_numpy()
    on_path = pd.Series(np.where(onm, np.nan_to_num(np.abs(dc)), 0.0)).groupby(sidx).sum().to_numpy()
    sigL_s = sigL[li]
    on_close = c[li]
    on_open = o[idx_first]
    on_ret_s = np.log(on_close / on_open) / (sigL_s * np.sqrt(np.maximum(on_cnt, 1)))
    on_rng_s = (on_hi - on_lo) / (on_close * sigL_s * np.sqrt(np.maximum(on_cnt, 1)))
    on_er_s = (on_close - on_open) / on_path
    on_lrv_s = lrv_cum_sess[li]
    on_loc_s = (on_close - on_lo) / (on_hi - on_lo)
    on_rpos = pd.Series(np.where(onm, np.nan_to_num(rpos), 0.0)).groupby(sidx).sum().to_numpy()
    on_rneg = pd.Series(np.where(onm, np.nan_to_num(rneg), 0.0)).groupby(sidx).sum().to_numpy()
    on_semi_s = (on_rpos - on_rneg) / (on_rpos + on_rneg)
    on_jumps_s = pd.Series(np.where(onm, np.abs(np.nan_to_num(jz)) > 4, False).astype(float)).groupby(sidx).sum().to_numpy()
    fin = {}
    for k in (15, 30, 60):
        j0 = np.maximum(li - k, 0)
        valid = has_on & (g[j0] == g[li])
        fin[k] = np.where(valid, np.log(c[li] / c[j0]) / (sig1[li] * np.sqrt(k)), np.nan)
    pm = (sm >= 840) & onm                        # 08:00 - 09:29
    idx_pm_first = pd.Series(np.where(pm, np.arange(n), n + 1)).groupby(sidx).min().to_numpy()
    okpm = idx_pm_first <= n
    pmf = np.where(okpm, np.minimum(idx_pm_first, n - 1), 0)
    pm_ret_s = np.where(okpm & has_on, np.log(on_close / o[pmf]) / (sig1[li] * np.sqrt(90)), np.nan)
    cv_pm = O.cum_in_group(vv, g, sm == 840)
    ce_pm = O.cum_in_group(Ev[20], g, sm == 840)
    pm_lrv_s = np.where(okpm & has_on, np.log(cv_pm[li] / ce_pm[li]), np.nan)
    _, _, on_r2_s = _session_ols_r2(c, onm, sidx, S)

    def per_rth(x_s):
        out = np.asarray(x_s, dtype=np.float64)[sidx]
        return np.where(rth & has_on[sidx], out, np.nan)

    # Decision bar 09:29 (sm 929) is the LAST overnight bar: its values are known at its close.
    def per_rth_incl929(x_s):
        out = np.asarray(x_s, dtype=np.float64)[sidx]
        return np.where((sm >= RTH_OPEN - 1) & has_on[sidx] & ((sm >= RTH_OPEN) | (np.arange(n) == li[sidx])),
                        out, np.nan)

    on = {}
    for nm, arr in (("on_retz", on_ret_s), ("on_range", on_rng_s), ("on_er", on_er_s), ("on_lrvol", on_lrv_s),
                    ("on_loc", on_loc_s), ("on_semi", on_semi_s), ("on_jumps", on_jumps_s), ("on_r2", on_r2_s),
                    ("on_final15z", fin[15]), ("on_final30z", fin[30]), ("on_final60z", fin[60]),
                    ("pm_retz", pm_ret_s), ("pm_lrvol", pm_lrv_s)):
        on[nm] = B.feat(nm, "OPEN", per_rth_incl929(arr), 930, cols=("o", "h", "l", "c", "v"),
                        reset="per session: overnight bars 18:00-09:29, constant through RTH")
    on_hi_b, on_lo_b = per_rth_incl929(on_hi), per_rth_incl929(on_lo)
    at929 = sm == RTH_OPEN - 1
    for X in (1, 3, 5, 10, 15, 30, 60):
        at = sm == (RTH_OPEN - 1 + X)
        for thr in (0.5, 1.0, 1.5):
            B.trig("OPEN", "opening_move", {"X": X, "thr": thr}, at & (open_retz > thr), at & (open_retz < -thr))
    for X in (0, 5, 15):
        at = sm == (RTH_OPEN - 1 + X)
        for thr in (0.5, 1.0, 1.5):
            B.trig("OPEN", "overnight_return", {"X": X, "thr": thr}, at & (on["on_retz"] > thr),
                   at & (on["on_retz"] < -thr))
    for thr in (1.0, 1.5):
        B.trig("OPEN", "overnight_final30", {"thr": thr}, at929 & (on["on_final30z"] > thr),
               at929 & (on["on_final30z"] < -thr))
    first30 = rth & (sm < 960)
    acc_up = first30 & (c > on_hi_b) & ~(B.lag(c) > on_hi_b)
    acc_dn = first30 & (c < on_lo_b) & ~(B.lag(c) < on_lo_b)
    B.trig("OPEN", "overnight_acceptance", {}, _first_in_session(acc_up, sidx), _first_in_session(acc_dn, sidx))
    broke_up = O.cum_in_group((first30 & (h > on_hi_b)).astype(float), g) > 0
    broke_dn = O.cum_in_group((first30 & (l < on_lo_b)).astype(float), g) > 0
    rej_dn = rth & (sm < 990) & broke_up & (c < on_hi_b) & (B.lag(c) >= on_hi_b)
    rej_up = rth & (sm < 990) & broke_dn & (c > on_lo_b) & (B.lag(c) <= on_lo_b)
    B.trig("OPEN", "overnight_rejection", {}, _first_in_session(rej_up, sidx), _first_in_session(rej_dn, sidx))
    for thr in (0.5, 1.0):
        B.trig("OPEN", "gap", {"thr": thr}, at929 & (gapz > thr), at929 & (gapz < -thr))

    # ================================================= J. NQ/ES CROSS-MARKET
    esig = np.sqrt(np.sqrt(tod_expected(er1 ** 2, sidx, sm, S, 20) * O.rmean(er1 ** 2, 30, g, 0.5)))
    es_retz = {}
    for H in (5, 15, 30):
        es_retz[H] = B.feat(f"es_retz_{H}", "XMKT", np.log(m.ec / O.lag(m.ec, H, g)) / (esig * np.sqrt(H)), H, inst=("ES",))
    evv = np.where(m.es_rw, np.nan, m.ev)
    Eev = tod_expected(evv, sidx, sm, S, 20)
    es_lrv = {W: np.log(O.rsum(evv, W, g) / O.rsum(Eev, W, g)) for W in (5, 15)}
    for W in (5, 15):
        B.feat(f"es_lrvol_{W}", "XMKT", es_lrv[W], W, inst=("ES",), cols=("v",))
    rel_lrv = B.feat("rel_lrvol_15", "XMKT", lrv[(15, 20)] - es_lrv[15], 15, inst=("NQ", "ES"), cols=("v",))
    B.feat("rel_lrvol_ch", "XMKT", rel_lrv - B.lag(rel_lrv, 30), 45, inst=("NQ", "ES"), cols=("v",))
    eRV30 = O.rsum(er1 ** 2, 30, g)
    esemi30 = (O.rsum(np.where(er1 > 0, er1 ** 2, 0), 30, g) - O.rsum(np.where(er1 < 0, er1 ** 2, 0), 30, g)) / eRV30
    rel_semi = B.feat("rel_semi_30", "XMKT", semi[30] - esemi30, 30, inst=("NQ", "ES"))
    edc = m.ec - O.lag(m.ec, 1, g)
    rel_er = {}
    for H in (15, 60):
        eer = (m.ec - O.lag(m.ec, H, g)) / O.rsum(np.abs(edc), H, g)
        rel_er[H] = B.feat(f"rel_er_{H}", "XMKT", er[H] - eer, H, inst=("NQ", "ES"))
    _, _, er2_60, _ = O.rolling_ols(m.ec, 60, g)
    B.feat("rel_r2_60", "XMKT", olsr2[60] - er2_60, 60, inst=("NQ", "ES"))
    corr60 = B.feat("corr_60", "XMKT", O.rolling_corr(r1, er1, 60, g), 60, inst=("NQ", "ES"))
    corr240 = O.rolling_corr(r1, er1, 240, g)
    B.feat("corr_240", "XMKT", corr240, 240, inst=("NQ", "ES"))
    B.feat("corr_ch", "XMKT", corr60 - corr240, 240, inst=("NQ", "ES"))
    beta = B.feat("beta_120", "XMKT", O.rolling_beta(r1, er1, 120, g), 120, inst=("NQ", "ES"))
    B.feat("beta_ch", "XMKT", beta - B.lag(beta, 60), 180, inst=("NQ", "ES"))
    eret15 = np.log(m.ec / O.lag(m.ec, 15, g))
    residz = B.feat("residz_15", "XMKT", (np.log(c / B.lag(c, 15)) - beta * eret15) / (sig1 * np.sqrt(15)), 135,
                    inst=("NQ", "ES"))
    eRVr30 = eRV30 / O.rsum(tod_expected(er1 ** 2, sidx, sm, S, 20), 30, g)
    voldis = B.feat("vol_disagree_30", "XMKT", np.log(rvr[30]) - np.log(eRVr30), 30, inst=("NQ", "ES"))
    evr5 = O.rsum(np.log(m.ec / O.lag(m.ec, 5, g)) ** 2, 120, g) / (5 * O.rsum(er1 ** 2, 120, g))
    persdis = B.feat("pers_disagree", "XMKT", vr5 - evr5, 125, inst=("NQ", "ES"))
    nq_lrv5, es_l5 = lrv[(5, 20)], es_lrv[5]
    for thr in (0.7, 1.0):
        B.trig("XMKT", "rel_rvol_nq_dominant", {"thr": thr}, B.xup(rel_lrv, thr), sign=retz[15])
        B.trig("XMKT", "rel_rvol_es_dominant", {"thr": thr}, B.xdn(rel_lrv, -thr), sign=es_retz[15])
    B.trig("XMKT", "nq_only_participation_shock", {}, B.enter((nq_lrv5 > np.log(3)) & (es_l5 < np.log(1.5))), sign=retz[5])
    B.trig("XMKT", "es_only_participation_shock", {}, B.enter((es_l5 > np.log(3)) & (nq_lrv5 < np.log(1.5))),
           sign=es_retz[5])
    B.trig("XMKT", "joint_participation_shock", {}, B.enter((es_l5 > np.log(3)) & (nq_lrv5 > np.log(3))), sign=retz[5])
    for thr in (0.5, 0.3):
        B.trig("XMKT", "corr_breakdown", {"thr": thr}, B.xdn(corr60, thr), sign=residz)
    for thr in (2.0, 3.0):
        B.signed_cross("XMKT", "residual_cross", residz, thr, {})
    for thr in (0.4, 0.6):
        B.signed_cross("XMKT", "er_disagree", rel_er[15], thr, {"H": 15})
    B.signed_cross("XMKT", "semi_disagree", rel_semi, 0.5, {})
    B.trig("XMKT", "vol_disagree", {"thr": 0.7}, B.xup(np.abs(voldis), 0.7), sign=retz[15])
    B.trig("XMKT", "pers_disagree", {"thr": 0.4}, B.xup(np.abs(persdis), 0.4), sign=retz[30])
    B.trig("XMKT", "es_volume_lead", {}, B.enter((es_l5 > np.log(3)) & (np.abs(retz[5]) < 0.5)), sign=es_retz[5])

    # ================================================= K. CALENDAR / TIME OF DAY
    dd = sday.astype("datetime64[D]")
    dow = ((sday + 3) % 7).astype(float)          # 0 = Monday
    month = (dd.astype("datetime64[M]").astype(np.int64) % 12 + 1).astype(float)
    dom = (dd - dd.astype("datetime64[M]")).astype(np.int64) + 1
    mon_key = dd.astype("datetime64[M]").astype(np.int64)
    s_mon = mon_key[pd.Series(np.arange(n)).groupby(sidx).min().to_numpy()]
    tdom_s = pd.Series(np.ones(S)).groupby(s_mon).cumsum().to_numpy()          # k-th session of month (causal)
    tdom = tdom_s[sidx].astype(float)
    last_day = (dd.astype("datetime64[M]") + np.timedelta64(1, "M")).astype("datetime64[D]") - np.timedelta64(1, "D")
    wd_left = np.busday_count(dd + np.timedelta64(1, "D"), last_day + np.timedelta64(1, "D")).astype(float)              # weekdays after today (approx.)
    first_fri = dd.astype("datetime64[M]").astype("datetime64[D]")
    third_fri = np.busday_offset(first_fri, 2, roll="forward", weekmask="Fri")
    opex_week = (dd >= third_fri - np.timedelta64(4, "D")) & (dd <= third_fri)
    tod = sm.astype(float)
    B.feat("dow", "CAL", dow, 0, cols=(), reset="calendar")
    B.feat("month", "CAL", month, 0, cols=(), reset="calendar")
    B.feat("tdom", "CAL", tdom, 0, cols=(), reset="calendar (count of sessions so far this month)")
    B.feat("weekdays_left_in_month", "CAL", wd_left, 0, cols=(), reset="calendar (weekday approximation; holidays ignored)")
    B.feat("opex_week", "CAL", opex_week.astype(float), 0, cols=(), reset="calendar (third-Friday week)")
    B.feat("tod", "CAL", tod, 0, cols=(), reset="clock")
    for T in (929, 959, 1019, 1079, 1139, 1199, 1259, 1284):
        B.trig("CAL", "time_of_day", {"sm": T}, sm == T, sign=np.ones(n))

    # ================================================= L. TECHNICAL INDICATOR COMPLETENESS
    gain = np.where(dc > 0, dc, 0.0)
    loss = np.where(dc < 0, -dc, 0.0)
    ag, al_ = O.ewm(gain, 27, g, 14), O.ewm(loss, 27, g, 14)          # Wilder alpha = 1/14 -> span 27
    rsi = B.feat("rsi_14", "TECH", 100 - 100 / (1 + ag / al_), 14)
    macd = O.ewm(c, 12, g, 26) - O.ewm(c, 26, g, 26)
    mh = macd - O.ewm(macd, 9, g, 9)
    macdh = B.feat("macd_hist", "TECH", mh / (c * sig1), 35)
    upm = h - B.lag(h)
    dnm = B.lag(l) - l
    pdm = np.where((upm > dnm) & (upm > 0), upm, 0.0)
    ndm = np.where((dnm > upm) & (dnm > 0), dnm, 0.0)
    atr14 = O.ewm(tr, 27, g, 14)
    pdi = 100 * O.ewm(pdm, 27, g, 14) / atr14
    ndi = 100 * O.ewm(ndm, 27, g, 14) / atr14
    dx = 100 * np.abs(pdi - ndi) / (pdi + ndi)
    adx = B.feat("adx_14", "TECH", O.ewm(dx, 27, g, 14), 28, cols=("h", "l", "c"))
    B.feat("di_diff_14", "TECH", pdi - ndi, 14, cols=("h", "l", "c"))
    sma20 = O.rmean(tp, 20, g)
    cci = B.feat("cci_20", "TECH", (tp - sma20) / (0.015 * 0.8 * O.rstd(tp, 20, g)), 20, cols=("h", "l", "c"),
                 params={"mad_approx": "0.8*std"})
    stoch = B.feat("stoch_14", "TECH", 100 * pos_range_n(c, h, l, 14, g), 14, cols=("h", "l", "c"))
    aroon = B.feat("aroon_osc_25", "TECH", _aroon(h, l, 25, gstart), 25, cols=("h", "l"))
    bb = B.feat("bb_pb", "TECH", (c - O.rmean(c, 20, g)) / (2 * O.rstd(c, 20, g)), 20)
    kel = B.feat("keltner_pos", "TECH", (c - O.ewm(c, 20, g, 20)) / (2 * O.ewm(tr, 20, g, 20)), 20, cols=("h", "l", "c"))
    for lo_, hi in ((30, 70), (20, 80)):
        B.trig("TECH", "rsi_extreme", {"lo": lo_, "hi": hi}, B.xup(rsi, hi), B.xdn(rsi, lo_))
    B.trig("TECH", "macd_zero_cross", {}, B.xup(macdh, 0.0), B.xdn(macdh, 0.0))
    dd_ = pdi - ndi
    B.trig("TECH", "dmi_cross_adx25", {}, B.xup(dd_, 0.0) & (adx > 25), B.xdn(dd_, 0.0) & (adx > 25))
    for thr in (100.0, 200.0):
        B.signed_cross("TECH", "cci_cross", cci, thr, {})
    B.trig("TECH", "stoch_extreme", {}, B.xup(stoch, 80.0), B.xdn(stoch, 20.0))
    B.signed_cross("TECH", "aroon_cross", aroon, 50.0, {})
    B.signed_cross("TECH", "bollinger_break", bb, 1.0, {})
    B.signed_cross("TECH", "keltner_break", kel, 1.0, {})

    # ================================================= M. OLD PRICE EVENTS WITH NEW INFORMATION
    for X in (15, 30, 60):
        in_or = rth & (sm < RTH_OPEN + X)
        orh = O.last_value_where(in_or & (sm == RTH_OPEN + X - 1), O.rmax(h, X, g), g)
        orl = O.last_value_where(in_or & (sm == RTH_OPEN + X - 1), O.rmin(l, X, g), g)
        after = rth & (sm >= RTH_OPEN + X)
        B.trig("REOPEN", "orb", {"X": X}, _first_in_session(after & (c > orh), sidx),
               _first_in_session(after & (c < orl), sidx))
    for N in (60, 120, 240):
        ph, pl = B.lag(O.rmax(h, N, g)), B.lag(O.rmin(l, N, g))
        B.trig("REOPEN", "rolling_breakout", {"N": N}, (c > ph) & ~(B.lag(c) > B.lag(ph)),
               (c < pl) & ~(B.lag(c) < B.lag(pl)))
    for N in (60, 240):
        ph, pl = B.lag(O.rmax(h, N, g)), B.lag(O.rmin(l, N, g))
        bo_up, bo_dn = c > ph, c < pl
        lvl_up = O.last_value_where(bo_up, ph, g)
        lvl_dn = O.last_value_where(bo_dn, pl, g)
        since_up, since_dn = O.bars_since(bo_up, g), O.bars_since(bo_dn, g)
        fail_up = (since_up >= 1) & (since_up <= 5) & (c < lvl_up) & (B.lag(c) >= lvl_up)
        fail_dn = (since_dn >= 1) & (since_dn <= 5) & (c > lvl_dn) & (B.lag(c) <= lvl_dn)
        B.trig("REOPEN", "failed_breakout", {"N": N}, fail_dn, fail_up)
    rng30z = (O.rmax(h, 30, g) - O.rmin(l, 30, g)) / (c * sig1 * np.sqrt(30))
    r1z = r1 / sig1
    for rthr, bthr in ((2.0, 2.5), (1.5, 3.0)):
        cond = (B.lag(rng30z) < rthr) & (np.abs(r1z) > bthr)
        B.trig("REOPEN", "compression_expansion", {"range": rthr, "bar": bthr}, cond, sign=r1z)
    body_frac = np.where(h > l, np.abs(c - o) / (h - l), 0.0)
    for thr in (3.0, 4.0):
        B.trig("REOPEN", "displacement", {"thr": thr}, (np.abs(r1z) > thr) & (body_frac > 0.7), sign=r1z)
    rth_hi_s = pd.Series(np.where(rth & (sm < 1320), h, -np.inf)).groupby(sidx).max().to_numpy()
    rth_lo_s = pd.Series(np.where(rth & (sm < 1320), l, np.inf)).groupby(sidx).min().to_numpy()
    prev_hi = np.r_[np.nan, rth_hi_s[:-1]][sidx]
    prev_lo = np.r_[np.nan, rth_lo_s[:-1]][sidx]
    prev_hi = np.where(np.isfinite(prev_hi), prev_hi, np.nan)
    prev_lo = np.where(np.isfinite(prev_lo), prev_lo, np.nan)
    B.feat("dist_prev_hi", "REOPEN", np.log(c / prev_hi) / (sigL * np.sqrt(390)), 1380, cols=("h", "c"),
           reset="prior session RTH high")
    B.trig("REOPEN", "prior_session_level_break", {}, rth & (c > prev_hi) & ~(B.lag(c) > prev_hi),
           rth & (c < prev_lo) & ~(B.lag(c) < prev_lo))
    ab_up = O.bars_since(rth & (c > prev_hi), g)
    ab_dn = O.bars_since(rth & (c < prev_lo), g)
    B.trig("REOPEN", "prior_session_failed_break", {},
           (ab_dn >= 1) & (ab_dn <= 5) & (c > prev_lo) & (B.lag(c) <= prev_lo),
           (ab_up >= 1) & (ab_up <= 5) & (c < prev_hi) & (B.lag(c) >= prev_hi))
    B.trig("REOPEN", "overnight_level_break", {}, rth & (sm >= 960) & (c > on_hi_b) & ~(B.lag(c) > on_hi_b),
           rth & (sm >= 960) & (c < on_lo_b) & ~(B.lag(c) < on_lo_b))
    for thr in (0.5, 1.0):
        gap_up = (l - B.lag(h, 2)) / (c * sig1)
        gap_dn = (B.lag(l, 2) - h) / (c * sig1)
        B.trig("REOPEN", "fvg", {"thr": thr}, gap_up > thr, gap_dn > thr)

    # ================================================= H. SYMBOLIC STATES (5-minute bars)
    B.W.sym = _symbolic(B, c, h, l, vv, Ev[20], sig1, g, sm)

    # ================================================= FILTERS (<= 64 bits)
    L = lambda x, t: np.nan_to_num(np.asarray(x, np.float64), nan=-np.inf) > t   # noqa: E731
    Lt = lambda x, t: np.nan_to_num(np.asarray(x, np.float64), nan=np.inf) < t  # noqa: E731
    B.filt("rvol_high", "volume", L(lrv[(15, 20)], np.log(1.5)), description="RVOL15 > 1.5")
    B.filt("rvol_low", "volume", Lt(lrv[(15, 20)], np.log(0.7)), description="RVOL15 < 0.7")
    B.filt("rvol_cum_rth_high", "volume", L(lrv_cum_rth, np.log(1.3)), description="cumulative RTH RVOL > 1.3")
    B.filt("vol_accelerating", "volume", L(vol_mom, np.log(1.5)), description="RVOL5 > 1.5 x RVOL60")
    B.filt("on_rvol_high", "volume", L(on["on_lrvol"], np.log(1.3)), description="overnight RVOL > 1.3")
    B.filt("volreg_high", "volatility", L(rvr[60], 1.5), description="RV60 > 1.5 x tod baseline")
    B.filt("volreg_low", "volatility", Lt(rvr[60], 0.7), description="RV60 < 0.7 x tod baseline")
    B.filt("on_range_high", "volatility", L(on["on_range"], 1.3), description="overnight range high")
    B.filt("on_range_low", "volatility", Lt(on["on_range"], 0.7), description="overnight range low")
    B.filt("jump_recent", "volatility", L(O.rsum(jany.astype(float), 30, g, 0.5), 0.5), description="|jz|>4 in last 30")
    B.filt("er_high", "persistence", L(np.abs(er[60]), 0.4), description="|ER60| > 0.4")
    B.filt("er_low", "persistence", Lt(np.abs(er[60]), 0.15), description="|ER60| < 0.15")
    B.filt("vr_high", "persistence", L(vr5, 1.2), description="VR(5,120) > 1.2")
    B.filt("vr_low", "persistence", Lt(vr5, 0.8), description="VR(5,120) < 0.8")
    B.filt("entropy_low", "persistence", Lt(ent, 0.9), description="3-bar pattern entropy < 0.9")
    B.filt("first_hour", "time", (sm >= 929) & (sm < 989), description="decision 09:29-10:28")
    B.filt("midday", "time", (sm >= 1049) & (sm < 1229), description="decision 10:49-13:48")
    B.filt("last_90", "time", (sm >= 1229) & (sm < 1290), description="decision 13:49-15:29")
    B.filt("monday", "calendar", dow == 0)
    B.filt("friday", "calendar", dow == 4)
    B.filt("month_turn", "calendar", (tdom <= 3) | (wd_left <= 1), description="first 3 / last 2 sessions of month")
    B.filt("opex_week", "calendar", opex_week)
    B.filt("corr_low", "cross", Lt(corr60, 0.6), description="corr60(NQ,ES) < 0.6")
    B.filt("es_confirms", "cross", L(es_retz[15], 0.5), Lt(es_retz[15], -0.5), "ES 15m z agrees with trade (>0.5)")
    B.filt("es_diverges", "cross", Lt(es_retz[15], -0.5), L(es_retz[15], 0.5), "ES 15m z against trade")
    B.filt("trend240_aligned", "trend", L(retz[240], 0.5), Lt(retz[240], -0.5))
    B.filt("trend60_aligned", "trend", L(retz[60], 0.5), Lt(retz[60], -0.5))
    B.filt("trend60_against", "trend", Lt(retz[60], -0.5), L(retz[60], 0.5))
    B.filt("range_top_for_long", "trend", L(pos_range[240], 0.8), Lt(pos_range[240], 0.2))
    B.filt("range_bottom_for_long", "trend", Lt(pos_range[240], 0.2), L(pos_range[240], 0.8))
    B.filt("vwap_aligned", "vwap", L(vdist["rth"], 0.0), Lt(vdist["rth"], 0.0), "long above / short below RTH VWAP")
    B.filt("vwap_against", "vwap", Lt(vdist["rth"], 0.0), L(vdist["rth"], 0.0))
    B.filt("on_aligned", "overnight", L(on["on_retz"], 0.5), Lt(on["on_retz"], -0.5))
    B.filt("on_against", "overnight", Lt(on["on_retz"], -0.5), L(on["on_retz"], 0.5))
    B.filt("open_aligned", "flow", L(open_retz, 0.5), Lt(open_retz, -0.5))
    B.filt("sgnvol_aligned", "flow", L(sgnvol[60], 0.1), Lt(sgnvol[60], -0.1))
    B.filt("clvvol_aligned", "flow", L(clvvol[60], 0.1), Lt(clvvol[60], -0.1))
    B.filt("semi_aligned", "flow", L(semi[60], 0.2), Lt(semi[60], -0.2))
    B.filt("rsi_stretched_against", "oscillator", Lt(rsi, 30), L(rsi, 70), "long when RSI<30 / short when RSI>70")
    B.W.bits_long, B.W.bits_short = B._bl, B._bs
    return B.W


# ---------------------------------------------------------------- helpers used above
def pos_range_n(c, h, l, n, g):
    hh, ll = O.rmax(h, n, g), O.rmin(l, n, g)
    return (c - ll) / (hh - ll)


def _first_in_session(mask, sidx):
    mask = np.asarray(mask, dtype=bool)
    idx = np.nonzero(mask)[0]
    out = np.zeros(len(mask), dtype=bool)
    if len(idx):
        _, first = np.unique(np.asarray(sidx)[idx], return_index=True)
        out[idx[first]] = True
    return out


def _session_ols_r2(c, mask, sidx, S):
    """R^2 of close vs time over the masked bars of each session (per-session scalar)."""
    t = np.arange(len(c), dtype=np.float64)
    m = np.asarray(mask, bool)
    df = pd.DataFrame({"s": np.asarray(sidx)[m], "t": t[m], "y": np.asarray(c, float)[m]})
    gb = df.groupby("s")
    n_ = gb.size()
    mt, my = gb["t"].mean(), gb["y"].mean()
    df["dt"] = df["t"] - mt.reindex(df["s"]).to_numpy()
    df["dy"] = df["y"] - my.reindex(df["s"]).to_numpy()
    gb = df.groupby("s")
    sxy = (df["dt"] * df["dy"]).groupby(df["s"]).sum()
    sxx = (df["dt"] ** 2).groupby(df["s"]).sum()
    syy = (df["dy"] ** 2).groupby(df["s"]).sum()
    r2 = (sxy ** 2 / (sxx * syy)).where(n_ >= 30)
    out = np.full(S, np.nan)
    out[r2.index.to_numpy()] = r2.to_numpy()
    return None, None, out


@njit(cache=True)
def _aroon_kernel(h, l, n, gs):
    out = np.full(len(h), np.nan)
    for i in range(len(h)):
        lo = i - n
        if lo < gs[i]:
            continue
        bh, bl, ih, il = -1e300, 1e300, lo, lo
        for j in range(lo, i + 1):
            if h[j] >= bh:
                bh, ih = h[j], j
            if l[j] <= bl:
                bl, il = l[j], j
        out[i] = 100.0 * ((n - (i - ih)) - (n - (i - il))) / n
    return out


def _aroon(h, l, n, gstart):
    # module-level compiled kernel (was re-compiled on every call -- performance fix, identical arithmetic)
    return _aroon_kernel(np.asarray(h, np.float64), np.asarray(l, np.float64), n, np.asarray(gstart, np.int64))


SYM_SPECS = {"A9": {"ret_levels": 3, "vol_levels": 3, "loc_levels": 1, "lengths": (2, 3, 4, 5)},
             "A15": {"ret_levels": 5, "vol_levels": 3, "loc_levels": 1, "lengths": (2, 3)},
             "A45": {"ret_levels": 5, "vol_levels": 3, "loc_levels": 3, "lengths": (2,)}}


def _symbolic(B, c, h, l, vv, Ev20, sig1, g, sm):
    """Symbols on completed 5-minute buckets (session minutes k*5..k*5+4) inside a group:
    return state from the 5-min log return / (sig1*sqrt5); volume state from bucket RVOL;
    close location within the bucket range. Sequences of L consecutive buckets ending at a
    complete bucket; the event is at the bucket's last bar (a decision bar if tradable)."""
    n = len(c)
    bucket = (np.asarray(sm) // 5).astype(np.int64)
    key = g * 400 + bucket
    last = np.ones(n, dtype=bool)
    last[:-1] = key[1:] != key[:-1]
    complete = last & (np.asarray(sm) % 5 == 4)
    first = np.ones(n, dtype=bool)
    first[1:] = key[1:] != key[:-1]
    fidx = np.maximum.accumulate(np.where(first, np.arange(n), 0))
    cprev = O.lag(c, 1, g)
    base = np.where(np.isfinite(cprev[fidx]), cprev[fidx], c[fidx])
    ret5 = np.log(c / base) / (sig1 * np.sqrt(5))
    hh = pd.Series(h).groupby(key).cummax().to_numpy()
    ll = pd.Series(l).groupby(key).cummin().to_numpy()
    loc = np.where(hh > ll, (c - ll) / (hh - ll), 0.5)
    vsum = pd.Series(np.nan_to_num(vv, nan=np.nan)).groupby(key).cumsum().to_numpy()
    esum = pd.Series(Ev20).groupby(key).cumsum().to_numpy()
    rv = vsum / esum
    r5s = np.digitize(np.nan_to_num(ret5), [-1.5, -0.5, 0.5, 1.5])      # 0..4
    r3s = np.digitize(np.nan_to_num(ret5), [-0.5, 0.5])                 # 0..2
    vs = np.digitize(np.nan_to_num(rv, nan=1.0), [0.7, 1.5])            # 0..2
    ls = np.digitize(loc, [1 / 3, 2 / 3])                               # 0..2
    valid_sym = complete & np.isfinite(ret5) & np.isfinite(rv)
    cidx = np.nonzero(complete)[0]
    out = {}
    for name, sp in SYM_SPECS.items():
        rs = r3s if sp["ret_levels"] == 3 else r5s
        A = sp["ret_levels"] * sp["vol_levels"] * sp["loc_levels"]
        sym = rs * (sp["vol_levels"] * sp["loc_levels"]) + vs * sp["loc_levels"] + (ls if sp["loc_levels"] == 3 else 0)
        s_c = np.where(valid_sym[cidx], sym[cidx], -1).astype(np.int64)
        gc = g[cidx]
        bc = bucket[cidx]
        for L in sp["lengths"]:
            code = np.zeros(len(cidx), dtype=np.int64)
            ok = s_c >= 0
            for k in range(L):
                sh = np.full(len(cidx), -1, dtype=np.int64)
                same = np.zeros(len(cidx), dtype=bool)
                if k < len(cidx):
                    sh[k:] = s_c[:len(cidx) - k]
                    same[k:] = (gc[k:] == gc[:len(cidx) - k]) & (bc[k:] - bc[:len(cidx) - k] == k)
                ok &= same & (sh >= 0) if k > 0 else ok
                code = code * A + np.maximum(sh, 0) if k > 0 else np.maximum(s_c, 0)
            codes_full = np.full(n, -1, dtype=np.int64)
            codes_full[cidx[ok]] = code[ok]
            out[f"{name}_L{L}"] = codes_full[B.dec]
    return out
