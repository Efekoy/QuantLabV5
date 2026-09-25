"""Run the COMPLETE V4 discovery search on one world (real, null or synthetic). One code path for all.

    summary = run_world(market, first_year=2010, save_dir=None)

Steps: features/triggers/filters/symbols -> outcome tables -> every RULE candidate (all triggers x
filter combos x 6 variants x 14 exits) -> every SYM candidate -> every ML candidate -> screen.
If save_dir is given, the full per-candidate stats are written there (real world); null worlds keep
only the summary (family and global statistics, top-t lists).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from quantlab5.search import kernel as K
from quantlab5.features.library import SYM_SPECS, compute_world
from quantlab5.search.reference_grammar import SYM_EXITS, combo_masks, filter_combos
from quantlab5.search.ml import FOLDS_DISCOVERY, ml_events
from quantlab5.engine.outcomes import EXITS, compute_outcomes
from quantlab5.search.reference_screen import COST_PTS, evaluate

TOP_K = 500
FAMILIES = ("RET", "VOL", "VWAP", "PATH", "DIST", "JUMP", "PERS", "OPEN", "XMKT", "CAL", "TECH", "REOPEN", "SYM", "ML")


class _Fam:
    def __init__(self):
        self.n_specs = 0
        self.n_eval = 0          # candidates with at least MIN_TRADES trades... (eligible-count base)
        self.n_elig = 0
        self.n_pass = 0
        self.max_t = -np.inf
        self.top = np.zeros(0)

    def add(self, met):
        t = met["t"]
        self.n_specs += t.size
        self.n_eval += int((met["n"] >= 200).sum())
        el = met["eligible"]
        self.n_elig += int(el.sum())
        self.n_pass += int(met["passed"].sum())
        te = t[el]
        if te.size:
            self.max_t = max(self.max_t, float(te.max()))
            self.top = np.sort(np.r_[self.top, np.sort(te)[-TOP_K:]])[-TOP_K:]

    def as_dict(self):
        return {"n_specs": self.n_specs, "n_min_trades": self.n_eval, "n_eligible": self.n_elig,
                "n_pass": self.n_pass, "max_t": self.max_t if np.isfinite(self.max_t) else None,
                "top_t": [round(float(x), 4) for x in self.top[::-1]]}


def year_index(m, first_year: int, n_years: int = K.N_YEARS):
    y = m.years()[m.dec]
    return np.clip(y - first_year, 0, n_years - 1).astype(np.int64), y


def run_world(m, first_year: int = 2010, save_dir: Path | None = None, ml_folds=FOLDS_DISCOVERY, log=None,
              families=None) -> dict:
    t0 = time.time()
    tm = {}
    W = compute_world(m)
    tm["features"] = time.time() - t0
    pnl, xbar = compute_outcomes(m, W.stop_scale)
    tm["outcomes"] = time.time() - t0 - tm["features"]
    cost = COST_PTS["baseline"]
    yidx, years = year_index(m, first_year)
    dec_bar = m.dec.astype(np.int64)
    combos = filter_combos(W.filters)
    cm_l = combo_masks(combos)
    fam = {f: _Fam() for f in FAMILIES}
    if save_dir is not None:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
    t1 = time.time()
    for ti, trig in enumerate(W.triggers):
        if families and trig.family not in families:
            continue
        out = np.zeros((len(combos), 6, len(EXITS), K.NSTAT))
        if len(trig.pos):
            K.eval_trigger(trig.pos.astype(np.int64), trig.sign.astype(np.int64), W.bits_long, W.bits_short,
                           dec_bar, yidx, cm_l, cm_l, pnl, xbar, cost, out, combos=combos)
        fam[trig.family].add(evaluate(out))
        if save_dir is not None:
            np.save(save_dir / f"rule_{ti:03d}.npy", out.astype(np.float32))
        if log and ti % 25 == 0:
            log(f"  trigger {ti}/{len(W.triggers)} {trig.tid} events={len(trig.pos)} t={time.time() - t1:.0f}s")
    tm["rules"] = time.time() - t1
    t2 = time.time()
    sym_saved = {}
    if not families or "SYM" in families:
        ex = np.array(SYM_EXITS, np.int64)
        for a, sp in SYM_SPECS.items():
            for L in sp["lengths"]:
                codes = W.sym[f"{a}_L{L}"]
                pos = np.nonzero(codes >= 0)[0]
                cv = codes[pos]
                o = np.lexsort((pos, cv))
                pos, cv = pos[o], cv[o]
                uniq, start = np.unique(cv, return_index=True)
                start = np.r_[start, len(cv)].astype(np.int64)
                out = np.zeros((len(uniq), 2, len(ex), K.NSTAT))
                if len(uniq):
                    K.eval_codes(pos.astype(np.int64), start, dec_bar, yidx, pnl, xbar, ex, cost, out)
                met = evaluate(out)
                fam["SYM"].add(met)
                # codes that never occurred are still grammar candidates with zero trades
                fam["SYM"].n_specs += (_n_codes(a, L) - len(uniq)) * 2 * len(ex)
                if save_dir is not None:
                    np.save(save_dir / f"sym_{a}_L{L}_codes.npy", uniq)
                    np.save(save_dir / f"sym_{a}_L{L}.npy", out.astype(np.float32))
                    sym_saved[f"{a}_L{L}"] = int(len(uniq))
    tm["sym"] = time.time() - t2
    t3 = time.time()
    ml_meta = []
    if not families or "ML" in families:
        cm0 = np.zeros(1, np.uint64)
        for i, (ss, pos, sg) in enumerate(ml_events(m, W, pnl, years, ml_folds)):
            out = np.zeros((1, 6, len(EXITS), K.NSTAT))
            if len(pos):
                K.eval_trigger(pos, sg, W.bits_long, W.bits_short, dec_bar, yidx, cm0, cm0, pnl, xbar, cost, out)
            o = out[0, 0]                          # cont_both, 14 exits
            fam["ML"].add(evaluate(o))
            ml_meta.append({**ss, "events": int(len(pos))})
            if save_dir is not None:
                np.save(save_dir / f"ml_{i:03d}.npy", o.astype(np.float32))
    tm["ml"] = time.time() - t3
    tm["total"] = time.time() - t0
    fams = {f: v.as_dict() for f, v in fam.items()}
    elig_max = [v["max_t"] for v in fams.values() if v["max_t"] is not None]
    summary = {"families": fams, "global_max_t": max(elig_max) if elig_max else None,
               "global_n_pass": int(sum(v["n_pass"] for v in fams.values())),
               "n_specs_total": int(sum(v["n_specs"] for v in fams.values())),
               "n_triggers": len(W.triggers), "n_filters": len(W.filters), "n_combos": len(combos),
               "timing_s": {k: round(v, 1) for k, v in tm.items()}, "n_decision_bars": int(len(m.dec)),
               "source": m.nq.source}
    if save_dir is not None:
        meta = {"triggers": [{"i": i, "tid": t.tid, "family": t.family, "params": t.params, "events": int(len(t.pos))}
                             for i, t in enumerate(W.triggers)],
                "filters": [f.__dict__ for f in W.filters], "combos": combos,
                "sym_codes_present": sym_saved, "ml": ml_meta, "exits": EXITS, "variants": list(K.VARIANTS),
                "stat_names": list(K.STAT_NAMES), "cost_pts": cost, "first_year": first_year}
        (save_dir / "META.json").write_text(json.dumps(meta, indent=1, default=str), encoding="utf-8")
        (save_dir / "SUMMARY.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary


def _n_codes(a, L):
    sp = SYM_SPECS[a]
    return (sp["ret_levels"] * sp["vol_levels"] * sp["loc_levels"]) ** L
