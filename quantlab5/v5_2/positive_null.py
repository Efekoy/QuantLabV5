"""Positive OHLC via a multiplicative map of paired, randomized latent ticks.

Every latent OHLC component is transformed by the same strictly increasing
exponential map. This is not price clipping: the map is smooth and invertible,
and price is positive for every finite latent value. The latent unsigned tape
and independent timewise sign law are inherited from stopped V5.1.
"""
from __future__ import annotations

import numpy as np

from quantlab5.data.schema import bars_from_arrays
from quantlab5.v5_1.paired_null import PairedNuisanceNull


class PositivePairedNull(PairedNuisanceNull):
    name = "v5.2_paired_sign_multiplicative_ohlc"

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
            latent_high = np.maximum(latent_open, latent_close)+up
            latent_low = np.minimum(latent_open, latent_close)-down
            anchor = float(self.artifact["median_price"][inst])
            center = float(np.median(latent_close))

            def price(latent):
                # The derivative at the median equals one point per latent
                # point; far tails remain positive without a hard boundary.
                return anchor*np.exp((latent-center)/anchor)

            open_, close = price(latent_open), price(latent_close)
            high, low = price(latent_high), price(latent_low)
            if not all(np.isfinite(z).all() and np.min(z) > 0
                       for z in (open_, high, low, close)):
                raise ValueError("V5.2 multiplicative price overflow or underflow")
            symbols = np.char.add(inst+"S", x["seg"].astype(str))
            out[inst] = bars_from_arrays(inst, x["ts"], open_, high, low, close,
                                         x["volume"], symbols,
                                         source=f"v5.2:null:{seed}")
        return out
