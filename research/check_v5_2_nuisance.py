"""Record the unchanged V5.1 fidelity gate on V5.2 positive-price worlds."""
from __future__ import annotations

import json

from quantlab5.project import ROOT
from quantlab5.util.hashing import file_sha256
from quantlab5.v5_2.positive_null import PositivePairedNull
from research.check_v5_1_nuisance import diagnose

READS_MARKET_DATA = False
SEEDS = (9101, 9102, 9103)
OUT = ROOT / "reports/V5_2_NUISANCE_FIDELITY.json"


def main() -> None:
    if OUT.exists():
        raise RuntimeError("V5.2 diagnostic outcome already exists")
    artifact = ROOT / "V5_1_DISCOVERY_NUISANCE_CALIBRATION.json"
    tape = ROOT / "reports/V5_1_NUISANCE_TAPE.npz"
    generator = PositivePairedNull(artifact, tape)
    rows = [diagnose(generator, seed) for seed in SEEDS]
    result = {"kind": "V5_2_UNCHANGED_V5_1_NUISANCE_GATE",
              "status": "PASS" if all(row["pass"] for row in rows) else "FAIL_NUISANCE_FIDELITY",
              "generator_code_sha256": file_sha256(ROOT / "quantlab5/v5_2/positive_null.py"),
              "v5_1_protocol_freeze_sha256": file_sha256(ROOT / "V5_1_NUISANCE_PROTOCOL_FREEZE.json"),
              "v5_1_nuisance_artifact_sha256": file_sha256(artifact),
              "v5_1_tape_sha256": file_sha256(tape),
              "seed_results": rows,
              "strategy_evaluations_on_real_discovery": 0}
    OUT.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if result["status"] != "PASS":
        raise SystemExit("V5.2 positivity fix failed unchanged nuisance fidelity; STOP")


if __name__ == "__main__":
    main()
