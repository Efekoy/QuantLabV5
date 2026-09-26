"""Write the outcome-blind V5 A/B/C structural inventory for review."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quantlab5.search.candidate_id import candidate_id
from quantlab5.v5.candidate_inventory import inventory


def main() -> None:
    x = inventory()
    out = {
        "status": "EXECUTABLE_GRAMMAR_UNCALIBRATED",
        "counts": x["counts"],
        "ab_ordered_id_sha256": x["ab_ordered_id_sha256"],
        "stage_a": [{"id": candidate_id(s), "spec": s} for s in x["stage_a"]],
        "stage_b": [{"id": candidate_id(s), "spec": s} for s in x["stage_b"]],
        "stage_c_max_slots": x["stage_c_max_slots"],
        "stage_c_conditional_id_universe": [
            {"id": candidate_id(s), "spec": s} for s in x["stage_c_universe"]],
        "warning": "C slots are conditional on discovery winners; complete synthetic power and false-positive calibration are pending.",
    }
    path = ROOT / "reports/V5_CANDIDATE_INVENTORY.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(path, out["counts"])


if __name__ == "__main__":
    main()
