"""Frozen full-market null and planted-edge campaign on nuisance-only worlds.

This program never calls load_view and never receives real OHLCV. It consumes
the hash-checked nuisance artifact and generates independent synthetic worlds.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import beta

from quantlab5.data.market import build_market, tail_sessions
from quantlab5.engine.costs import CostModel
from quantlab5.isolation.calibration_gate import FREEZE, science_freeze_ready
from quantlab5.project import ROOT
from quantlab5.util.hashing import file_sha256
from quantlab5.v5.calibrated_null import CalibratedZeroEdgeWorlds
from quantlab5.v5.inference import sequential_decision
from quantlab5.v5.market_plant import (EFFECTS_R, FREQUENCIES, SHAPES,
                                        plant_e03_long, realized_plant_effect_r)
from quantlab5.v5.market_search import adaptive_search, calibrate_stage_a_reference
from quantlab5.v5.validation import validate_frozen_cohort
from research.check_v5_nuisance_fit import diagnose

READS_MARKET_DATA = False
ARTIFACT = ROOT / "V5_DISCOVERY_NUISANCE_CALIBRATION.json"
TEMPLATE = ROOT / "reports/V5_DISCOVERY_CALENDAR_TEMPLATE.npz"
OUTPUT = ROOT / "reports/V5_EXECUTABLE_CALIBRATION.json"
REFERENCE_SEEDS = tuple(range(1000, 1019))
ADAPTIVE_NULL_REFERENCE_SEEDS = tuple(range(2000, 2500))
ALL_NULL_TEST_SEEDS = tuple(range(3000, 3200))
PLANT_SEED_BASE = 100000
VALIDATION_SEED_BASE = 500000


def _world(generator, seed):
    bars = generator.generate_seed(seed)
    nq_seg = generator.template["nq_segment"]
    es_seg = generator.template["es_segment"]
    nq_symbols = np.char.add("NQS", nq_seg.astype(str))
    es_symbols = np.char.add("ESS", es_seg.astype(str))
    return build_market(bars["NQ"], bars["ES"], nq_symbols, es_symbols)


def _upper(k, n):
    return 1.0 if k == n else float(beta.ppf(.95, k+1, n-k))


def _lower(k, n):
    return 0.0 if k == 0 else float(beta.ppf(.05, k, n-k+1))


def _checkpoint(doc):
    temp = OUTPUT.with_suffix(".tmp")
    temp.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    temp.replace(OUTPUT)


def main() -> None:
    ready, reason = science_freeze_ready(ROOT)
    if not ready:
        raise RuntimeError(reason)
    state = json.loads((ROOT / "ledgers/CALIBRATION_ACCESS_STATE.json").read_text())
    if state.get("state") != "COMPLETE":
        raise RuntimeError("DISCOVERY nuisance calibration is not closed")
    generator = CalibratedZeroEdgeWorlds(ARTIFACT, TEMPLATE)
    if generator.doc["precalibration_science_freeze_sha256"] != file_sha256(ROOT / FREEZE):
        raise RuntimeError("nuisance artifact does not match science freeze")
    cfg = yaml.safe_load((ROOT / "config/costs.yaml").read_text(encoding="utf-8"))
    costs = CostModel(cfg, "v5_executable_calibration")
    fingerprints = {"science_freeze_sha256": file_sha256(ROOT / FREEZE),
                    "nuisance_artifact_sha256": file_sha256(ARTIFACT),
                    "calendar_template_sha256": file_sha256(TEMPLATE)}
    if OUTPUT.exists():
        result = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if result.get("fingerprints") != fingerprints:
            raise RuntimeError("calibration checkpoint belongs to different frozen inputs")
    else:
        result = {"kind": "V5_EXECUTABLE_MARKET_CALIBRATION", "status": "RUNNING",
                  "fingerprints": fingerprints, "reference_seeds": REFERENCE_SEEDS,
                  "adaptive_null_reference_seeds": ADAPTIVE_NULL_REFERENCE_SEEDS,
                  "all_null_test_seeds": ALL_NULL_TEST_SEEDS,
                  "null_reference": [], "all_null": [], "plants": {}}
    if "nuisance_fit" not in result:
        result["nuisance_fit"] = {str(seed): diagnose(generator, seed)
                                  for seed in (9001, 9002, 9003)}
        if not all(row["pass"] for row in result["nuisance_fit"].values()):
            result["status"] = "FAIL_NUISANCE_MODEL"
            _checkpoint(result)
            raise RuntimeError("frozen nuisance model failed before search calibration")
        _checkpoint(result)
    if "stage_a_reference" not in result:
        seed_market = _world(generator, 999)
        reference = calibrate_stage_a_reference(seed_market, generator,
                                                REFERENCE_SEEDS, costs)
        result["stage_a_reference"] = reference.tolist()
        _checkpoint(result)
    reference = np.asarray(result["stage_a_reference"], float)
    for seed in ADAPTIVE_NULL_REFERENCE_SEEDS[len(result["null_reference"]):]:
        world = _world(generator, seed)
        trace = adaptive_search(world, costs, reference)
        result["null_reference"].append({"seed": seed, "global_statistic": trace.global_statistic})
        _checkpoint(result)
    null_stats = np.asarray([x["global_statistic"] for x in result["null_reference"]], float)
    for seed in ALL_NULL_TEST_SEEDS[len(result["all_null"]):]:
        trace = adaptive_search(_world(generator, seed), costs, reference)
        validation = tail_sessions(_world(generator, VALIDATION_SEED_BASE+seed), 1008)
        holdout = validate_frozen_cohort(validation, trace, costs, seed=700000+seed)
        decision = sequential_decision(null_stats >= trace.global_statistic)
        evaluated = {r.candidate_id: r for r in holdout.evaluated}
        result["all_null"].append({"seed": seed, "nominees": len(trace.nominee_ids),
            "qualifiers": len(trace.qualifying_ids), "survivors": len(holdout.survivor_ids),
            "survivor_families": sorted({evaluated[cid].family for cid in holdout.survivor_ids}),
            "expanded_families": list(trace.expanded_families),
            "adaptive_global_decision": asdict(decision)})
        _checkpoint(result)
    cell_index = 0
    for effect in EFFECTS_R:
        for frequency in FREQUENCIES:
            for shape in SHAPES:
                key = f"{effect:g}R_{frequency}py_{shape}"
                rows = result["plants"].setdefault(key, [])
                target_count = 100 if (frequency == 500 and shape == "stable_plateau"
                                       and effect in (.10, .15)) else 20
                for rep in range(len(rows), target_count):
                    seed = PLANT_SEED_BASE + cell_index*1000 + rep
                    base = _world(generator, seed)
                    plant = plant_e03_long(base, effect_r=effect,
                                          trades_per_year=frequency, shape=shape,
                                          seed=seed+900000)
                    realized_discovery = realized_plant_effect_r(base, plant)
                    trace = adaptive_search(plant.world, costs, reference)
                    val_base = tail_sessions(_world(generator, VALIDATION_SEED_BASE+seed), 1008)
                    val_plant = plant_e03_long(val_base, effect_r=effect,
                                               trades_per_year=frequency, shape=shape,
                                               seed=seed+1200000)
                    realized_validation = realized_plant_effect_r(val_base, val_plant)
                    holdout = validate_frozen_cohort(val_plant.world, trace, costs,
                                                     seed=seed+1300000)
                    target = set(plant.target_ids)
                    e03_c = any(r.family == "E03" and r.stage == "C" for r in trace.records)
                    nominated = any(r.candidate_id in trace.nominee_ids and r.family == "E03"
                                    and r.side == "long" for r in trace.records)
                    primary = ("E03" in trace.expanded_families and e03_c
                               and bool(target & set(trace.qualifying_ids))
                               and (nominated or shape in ("isolated_needle", "regime_specific"))
                               and bool(target & set(holdout.survivor_ids)))
                    decision = sequential_decision(null_stats >= trace.global_statistic)
                    rows.append({"discovery_seed": seed, "validation_seed": VALIDATION_SEED_BASE+seed,
                                 "discovery_events": len(plant.selected_decision_bars),
                                 "discovery_sessions": int(np.unique(base.nq.sday).size),
                                 "validation_events": len(val_plant.selected_decision_bars),
                                 "validation_sessions": int(np.unique(val_base.nq.sday).size),
                                 "realized_discovery_effect_r": realized_discovery,
                                 "realized_validation_effect_r": realized_validation,
                                 "stage_a_expanded": "E03" in trace.expanded_families,
                                 "stage_c_generated": e03_c, "target_qualified": bool(target & set(trace.qualifying_ids)),
                                 "representative_nominated": nominated,
                                 "target_validation_survived": bool(target & set(holdout.survivor_ids)),
                                 "primary_power_event": bool(primary),
                                 "adaptive_global_decision": asdict(decision)})
                    _checkpoint(result)
                cell_index += 1
    null_n = len(result["all_null"])
    false_survivors = sum(row["survivors"] > 0 for row in result["all_null"])
    core = {}
    for effect in (.10, .15):
        key = f"{effect:g}R_500py_stable_plateau"
        rows = result["plants"][key]
        k = sum(row["primary_power_event"] for row in rows)
        core[key] = {"successes": k, "worlds": len(rows), "lower95": _lower(k, len(rows))}
    realized_cells = {}
    for key, rows in result["plants"].items():
        realized = np.mean([r["realized_discovery_effect_r"] for r in rows]
                           + [r["realized_validation_effect_r"] for r in rows])
        requested = float(key.split("R_", 1)[0])
        frequency = int(key.split("R_", 1)[1].split("py_", 1)[0])
        events = sum(r["discovery_events"]+r["validation_events"] for r in rows)
        sessions = sum(r["discovery_sessions"]+r["validation_sessions"] for r in rows)
        actual_frequency = 252*events/sessions
        realized_cells[key] = {"requested_r": requested, "realized_mean_r": float(realized),
                               "within_20_percent": bool(abs(realized-requested) <= .2*requested),
                               "requested_events_per_year": frequency,
                               "actual_events_per_year": actual_frequency,
                               "frequency_within_20_percent": bool(abs(actual_frequency-frequency) <= .2*frequency)}
    result["all_null_summary"] = {"worlds": null_n, "any_false_validation_survivor": false_survivors,
                                  "upper95": _upper(false_survivors, null_n),
                                  "worlds_with_nominees": sum(row["nominees"] > 0 for row in result["all_null"]),
                                  "total_nominees": sum(row["nominees"] for row in result["all_null"]),
                                  "worlds_with_qualifiers": sum(row["qualifiers"] > 0 for row in result["all_null"]),
                                  "total_qualifiers": sum(row["qualifiers"] for row in result["all_null"]),
                                  "total_false_validation_survivors": sum(row["survivors"] for row in result["all_null"]),
                                  "expanded_family_counts": dict(Counter(
                                      family for row in result["all_null"]
                                      for family in row["expanded_families"])),
                                  "family_false_survivors": dict(Counter(
                                      family for row in result["all_null"]
                                      for family in row["survivor_families"]))}
    result["core_power"] = core
    result["realized_plant_effects"] = realized_cells
    result["final_gate_passed"] = bool(result["all_null_summary"]["upper95"] <= .10
        and core["0.1R_500py_stable_plateau"]["lower95"] >= .70
        and core["0.15R_500py_stable_plateau"]["lower95"] >= .90
        and all(x["within_20_percent"] and x["frequency_within_20_percent"]
                for x in realized_cells.values()))
    result["status"] = "PASS" if result["final_gate_passed"] else "FAIL"
    result["completed_utc"] = datetime.now(timezone.utc).isoformat()
    _checkpoint(result)


if __name__ == "__main__":
    main()
