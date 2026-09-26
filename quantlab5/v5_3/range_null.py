"""Positive close path with separate causal intrabar wick excursions.

Open and close follow the V5.2 positive exponential mapping of paired latent
ticks. Upper and lower wicks come independently from the already permitted
unsigned wick tape, expressed as positive log distances from the completed
open/close body. No clipping, future-state lookahead, or strategy result enters.
"""
from __future__ import annotations

import numpy as np

from quantlab5.data.schema import bars_from_arrays
from quantlab5.v5_1.paired_null import PairedNuisanceNull


class RangeSeparatedNull(PairedNuisanceNull):
    name = "v5.3_paired_sign_separate_log_excursions"

    def __init__(self, artifact_path, tape_path):
        super().__init__(artifact_path, tape_path, "paired_sign")

    def generate_seed(self, seed: int):
        rng = np.random.default_rng(int(seed))
        tape = self.tape
        a = {}
        for inst, prefix in (("NQ", "nq"), ("ES", "es")):
            a[inst] = {"ts": tape[f"{prefix}_ts"], "seg": tape[f"{prefix}_segment"],
                       **{field: tape[f"{prefix}_{field}"] for field in
                          ("gap_ticks", "body_ticks", "up_wick_ticks",
                           "down_wick_ticks", "volume", "gap_body_relation")}}
        signs = {inst: np.where(rng.random(len(a[inst]["ts"])) < .5, -1, 1).astype(np.int8)
                 for inst in ("NQ", "ES")}
        nq, es = a["NQ"], a["ES"]
        pos = np.searchsorted(nq["ts"], es["ts"])
        matched = pos < len(nq["ts"])
        matched[matched] &= nq["ts"][pos[matched]] == es["ts"][matched]
        ei = np.flatnonzero(matched)
        ni = pos[ei]
        p = self.artifact["joint_sign"]["same_sign_fraction"]
        signs["ES"][ei] = signs["NQ"][ni] * np.where(rng.random(len(ei)) < p, 1, -1)
        out = {}
        for inst in ("NQ", "ES"):
            x = a[inst]
            n = len(x["ts"])
            body_sign = signs[inst]
            relation = x["gap_body_relation"].astype(np.int8)
            independent_gap_sign = np.where(rng.random(n) < .5, -1, 1)
            gap_sign = np.where(relation != 0, relation*body_sign, independent_gap_sign)
            gap = gap_sign*x["gap_ticks"].astype(float)*.25
            body = body_sign*x["body_ticks"].astype(float)*.25
            latent_close = np.cumsum(gap+body)
            latent_open = latent_close-body
            flip = rng.random(n) < .5
            up = np.where(flip, x["down_wick_ticks"], x["up_wick_ticks"]).astype(float)*.25
            down = np.where(flip, x["up_wick_ticks"], x["down_wick_ticks"]).astype(float)*.25
            anchor = float(self.artifact["median_price"][inst])

            def price(latent):
                # Initial level is the permitted fixed anchor. This uses no
                # future path statistic and is causal at every bar.
                return anchor*np.exp(latent/anchor)

            open_, close = price(latent_open), price(latent_close)
            upper_core = np.maximum(open_, close)
            lower_core = np.minimum(open_, close)
            # The upper log excursion reproduces its unsigned tape points
            # exactly. The lower uses the reciprocal log distance so every
            # low remains strictly positive without clipping.
            high = upper_core*np.exp(np.log1p(up/upper_core))
            low = lower_core*np.exp(-np.log1p(down/lower_core))
            if not all(np.isfinite(z).all() and np.min(z) > 0
                       for z in (open_, high, low, close)):
                raise ValueError("V5.3 multiplicative price overflow or underflow")
            symbols = np.char.add(inst+"S", x["seg"].astype(str))
            out[inst] = bars_from_arrays(inst, x["ts"], open_, high, low, close,
                                         x["volume"], symbols,
                                         source=f"v5.3:null:{seed}")
        return out
