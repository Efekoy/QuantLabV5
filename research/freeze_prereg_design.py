"""Pin the review draft's exact bytes without advancing the data stage."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "V5_PRIOR_LAB_COVERAGE.md",
    "V5_STRATEGY_CATALOG.md",
    "V5_POWER_CALIBRATION_REPORT.md",
    "V5_NULL_METHOD_REPORT.md",
    "V5_RESEARCH_PREREGISTRATION.md",
    "V5_UPDATED_POWER_GATE_INVESTIGATION.md",
    "quantlab5/v5/candidate_inventory.py",
    "reports/V5_CANDIDATE_INVENTORY.json",
    "research/planning_power.py",
)
OUT = ROOT / "V5_PREREGISTRATION_FREEZE.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    body = {
        "kind": "V5_PREREGISTRATION_DESIGN_FREEZE",
        "version": 1,
        "status": "REVIEW_REQUIRED",
        "discovery_search_authorized": False,
        "later_partitions_opened": False,
        "note": "Review-draft hash pin only; not a stage transition or calibrated search authorization.",
        "files_sha256": {name: digest(ROOT / name) for name in FILES},
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return {**body, "body_sha256": hashlib.sha256(canonical).hexdigest()}


def verify() -> bool:
    return json.loads(OUT.read_text(encoding="utf-8")) == build()


if __name__ == "__main__":
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(OUT)
