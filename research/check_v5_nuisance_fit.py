"""Outcome-blind fidelity check of generated zero-edge worlds against allowed nuisances."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from quantlab5.project import ROOT
from quantlab5.v5.calibrated_null import CalibratedZeroEdgeWorlds
from research.calibrate_v5_discovery_nuisance import _joint_sign_agreement, _summarize

READS_MARKET_DATA = False


def diagnose(generator: CalibratedZeroEdgeWorlds, seed: int) -> dict:
    bars = generator.generate_seed(seed)
    findings = {}
    for inst, prefix in (("NQ", "nq"), ("ES", "es")):
        b = bars[inst]
        segment = generator.template[f"{prefix}_segment"]
        md = type("SyntheticView", (), {"bars": lambda self, b=b: b,
             "frame": {"symbol": pd.Series(np.char.add(inst + "S", segment.astype(str)))}})()
        observed, template = _summarize(md)
        target = generator.doc[inst]
        exact_calendar = np.array_equal(template["ts"], generator.template[f"{prefix}_ts"])
        exact_roll = np.array_equal(template["segment"], segment)
        metrics = {}
        for key, floor in (("body_abs_points_by_clock", .25),
                           ("range_points_by_clock", .25), ("volume_by_clock", 1.0)):
            a, z = observed[key], target[key]
            use = np.asarray(z["count"]) >= 100
            rel = []
            for quantile in ("median", "p90"):
                actual = np.asarray(a[quantile], float)[use]
                expected = np.asarray(z[quantile], float)[use]
                # OHLC magnitudes are discrete ticks; one tick of quantile
                # sampling/rounding error is tolerated before relative fit.
                allowance = 0.0 if key == "volume_by_clock" else .25
                rel.extend((np.maximum(np.abs(actual-expected)-allowance, 0)
                            / np.maximum(expected, floor)).tolist())
            metrics[key] = float(max(rel, default=0.0))
        for key in ("abs_body_log_lag_correlation", "volume_log_lag_correlation"):
            metrics[key] = abs(observed[key]["1"]-target[key]["1"])
        findings[inst] = {"calendar_identical": exact_calendar, "roll_identical": exact_roll,
                          "errors": metrics}
    def md(inst):
        b = bars[inst]
        return type("SyntheticView", (), {"bars": lambda self, b=b: b})()
    joint = _joint_sign_agreement(md("NQ"), md("ES"))
    sign_error = abs(joint["same_sign_fraction"]-generator.doc["joint"]["same_sign_fraction"])
    magnitude_error = abs(joint["abs_body_log_correlation"]
                          -generator.doc["joint"]["abs_body_log_correlation"])
    findings["joint_sign_agreement_error"] = sign_error
    findings["joint_abs_body_correlation_error"] = magnitude_error
    findings["pass"] = bool(sign_error <= .05 and magnitude_error <= .10 and all(
        d["calendar_identical"] and d["roll_identical"]
        and max(d["errors"][key] for key in ("body_abs_points_by_clock",
                                            "range_points_by_clock", "volume_by_clock")) <= .25
        and d["errors"]["abs_body_log_lag_correlation"] <= .10
        and d["errors"]["volume_log_lag_correlation"] <= .10
        for d in (findings["NQ"], findings["ES"])))
    return findings


def main() -> None:
    artifact = ROOT / "V5_DISCOVERY_NUISANCE_CALIBRATION.json"
    template = ROOT / "reports/V5_DISCOVERY_CALENDAR_TEMPLATE.npz"
    generator = CalibratedZeroEdgeWorlds(artifact, template)
    result = {str(seed): diagnose(generator, seed) for seed in (9001, 9002, 9003)}
    output = ROOT / "reports/V5_NUISANCE_MODEL_FIT.json"
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if not all(row["pass"] for row in result.values()):
        raise SystemExit("nuisance model fit failed frozen tolerance")


if __name__ == "__main__":
    main()
