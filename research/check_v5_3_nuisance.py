"""Apply the unchanged V5.1 nuisance and zero-edge diagnostics to V5.3."""
from __future__ import annotations

import json

from quantlab5.project import ROOT
from quantlab5.util.hashing import file_sha256
from quantlab5.v5_3.gate import FREEZE, freeze_ready
from quantlab5.v5_3.range_null import RangeSeparatedNull
from research.check_v5_1_nuisance import diagnose

READS_MARKET_DATA = False
SEEDS = (9101, 9102, 9103)
OUT = ROOT / "reports/V5_3_NUISANCE_FIDELITY.json"


def main() -> None:
    ok, reason = freeze_ready()
    if not ok:
        raise RuntimeError(reason)
    if OUT.exists():
        raise RuntimeError("V5.3 frozen fidelity result already exists")
    generator = RangeSeparatedNull(ROOT / "V5_1_DISCOVERY_NUISANCE_CALIBRATION.json",
                                   ROOT / "reports/V5_1_NUISANCE_TAPE.npz")
    rows = [diagnose(generator, seed) for seed in SEEDS]
    nuisance_ok = all(x["nuisance_pass"] for x in rows)
    zero_edge_ok = all(x["zero_edge_pass"] for x in rows)
    status = ("PASS" if nuisance_ok and zero_edge_ok else
              "FAIL_NUISANCE_FIDELITY" if not nuisance_ok else "FAIL_ZERO_EDGE")
    result = {"kind": "V5_3_UNCHANGED_FROZEN_NUISANCE_AND_ZERO_EDGE",
              "status": status, "protocol_freeze_sha256": file_sha256(FREEZE),
              "generator_code_sha256": file_sha256(ROOT / "quantlab5/v5_3/range_null.py"),
              "nuisance_artifact_sha256": file_sha256(ROOT / "V5_1_DISCOVERY_NUISANCE_CALIBRATION.json"),
              "nuisance_tape_sha256": file_sha256(ROOT / "reports/V5_1_NUISANCE_TAPE.npz"),
              "seed_results": rows, "real_strategy_outcomes_computed": 0}
    OUT.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if status != "PASS":
        raise SystemExit(f"V5.3 frozen generator gate failed: {status}; STOP")


if __name__ == "__main__":
    main()
