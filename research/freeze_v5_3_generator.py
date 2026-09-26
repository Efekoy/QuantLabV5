"""Freeze V5.3 generator design after full structural stress, before fidelity."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import subprocess

from quantlab5.project import ROOT
from quantlab5.search.candidate_id import candidate_id
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v5.candidate_inventory import inventory
from quantlab5.v5_3.gate import FREEZE

READS_MARKET_DATA = False
STRATEGY_FILES = (
    "quantlab5/v5/candidate_inventory.py", "quantlab5/v5/signals.py",
    "quantlab5/v5/market_search.py", "quantlab5/v5/validation.py",
    "quantlab5/v5/inference.py", "quantlab5/v5/market_plant.py",
    "quantlab5/v5/duplicate_accounting.py", "quantlab5/v5/risk_coverage.py",
    "quantlab5/engine/execution.py", "quantlab5/engine/costs.py",
    "config/costs.yaml", "config/stage_policy.yaml", "config/execution.yaml",
)
FILES = STRATEGY_FILES + (
    "quantlab5/v5_3/range_null.py", "quantlab5/v5_3/gate.py",
    "research/stress_v5_3_structure.py", "research/freeze_v5_3_generator.py",
    "research/check_v5_3_nuisance.py",
    "research/check_v5_1_nuisance.py", "tests/test_v5_3_range_null.py",
    "V5_3_GENERATOR_PROTOCOL.md", "V5_3_RANGE_GENERATOR_DIAGNOSIS.md",
    "reports/V5_3_RANGE_DIAGNOSIS.json", "reports/V5_3_STRUCTURAL_STRESS.json",
    "V5_1_NUISANCE_PROTOCOL_FREEZE.json",
    "V5_1_DISCOVERY_NUISANCE_CALIBRATION.json",
    "reports/V5_1_NUISANCE_TAPE.npz",
    "quantlab5/v5_1/paired_null.py",
)


def main() -> None:
    if FREEZE.exists():
        raise RuntimeError("V5.3 generator protocol freeze already exists")
    stress = json.loads((ROOT / "reports/V5_3_STRUCTURAL_STRESS.json").read_text(encoding="utf-8"))
    if (stress.get("status") != "PASS" or stress.get("completed_worlds") != 1001
            or stress.get("invalid_worlds") != 0
            or stress.get("numerical_overflow_or_underflow_events") != 0
            or stress.get("ohlc_invariant_failures") != 0
            or stress.get("minimum_price", 0) <= 0):
        raise RuntimeError("V5.3 structural stress did not pass")
    protocol = (ROOT / "V5_3_GENERATOR_PROTOCOL.md").read_text(encoding="utf-8")
    if "**Status: FROZEN GENERATOR DESIGN." not in protocol:
        raise RuntimeError("V5.3 protocol document is not marked frozen")
    tag = subprocess.run(["git", "rev-parse", "v5.2-calibration-failed^{commit}"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    if subprocess.run(["git", "diff", "--quiet", "v5.2-calibration-failed", "--",
                       *STRATEGY_FILES], cwd=ROOT).returncode != 0:
        raise RuntimeError("V5.3 strategy research differs from archived V5.2")
    inv = inventory()
    stage_a = [candidate_id(x) for x in inv["stage_a"]]
    universe = [candidate_id(x) for x in (inv["stage_a"]+inv["stage_b"]
                                           + inv["stage_c_universe"])]
    body = {
        "kind": "V5_3_GENERATOR_PROTOCOL_FREEZE", "status": "FROZEN",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "v5_2_failed_archive_commit": tag,
        "strategy_files_unchanged_from_v5_2_tag": True,
        "stage_a_ids_sha256": sha256_text("\n".join(stage_a)),
        "candidate_universe_ids_sha256": sha256_text("\n".join(universe)),
        "files_sha256": {rel: file_sha256(ROOT / rel) for rel in FILES},
        "structural_seed_policy": "0..999 plus 1002",
        "structural_world_count": 1001,
        "fidelity_seeds": [9101, 9102, 9103],
        "downstream_seed_policy": {
            "stage_a_reference": [1000, 1018],
            "adaptive_null_reference": [2000, 2499],
            "all_null_test": [3000, 3199],
            "plants": "100000 + cell_index*1000 + replication; validation 500000 + discovery seed",
        },
        "fidelity_thresholds_source": "V5_1_NUISANCE_PROTOCOL_FREEZE.json",
        "zero_edge_threshold": .01,
        "range_quantile_error_max": .25,
        "extreme_value_treatment": "none; nonfinite or underflow world fails",
        "structural_invariants": ["finite OHLCV", "positive OHLC", "ordered OHLC",
                                  "nonnegative volume", "strictly increasing timestamps",
                                  "exact NQ/ES tape calendars", "at least one million matched timestamps"],
        "new_real_market_access_authorized": False,
        "real_strategy_search_authorized": False,
    }
    doc = {**body, "body_sha256": sha256_text(canonical_json(body))}
    FREEZE.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(file_sha256(FREEZE))


if __name__ == "__main__":
    main()
