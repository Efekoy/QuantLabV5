import json

from quantlab5.isolation import ledger
from quantlab5.isolation.calibration_gate import FREEZE, science_freeze_ready
from quantlab5.search.candidate_id import candidate_id
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v5.candidate_inventory import inventory
from research.freeze_v5_precalibration import PINNED_FILES


def test_precalibration_freeze_requires_pinned_files_and_ledger_anchor(tmp_path):
    for rel in PINNED_FILES:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rel, encoding="utf-8")
    ledger_path = tmp_path / "ledgers/DATA_ACCESS_LEDGER.jsonl"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger.append(ledger_path, "LEDGER_CREATED", reason="synthetic test")
    space = inventory()
    a = [candidate_id(s) for s in space["stage_a"]]
    all_ids = [candidate_id(s) for s in space["stage_a"] + space["stage_b"]
               + space["stage_c_universe"]]
    body = {"kind": "V5_PRECALIBRATION_SCIENCE_FREEZE", "status": "FROZEN",
            "files_sha256": {rel: file_sha256(tmp_path / rel) for rel in PINNED_FILES},
            "stage_a_ids_sha256": sha256_text("\n".join(a)),
            "candidate_universe_ids_sha256": sha256_text("\n".join(all_ids)),
            "ledger_anchor_before_access": ledger.head(ledger_path)}
    doc = {**body, "body_sha256": sha256_text(canonical_json(body))}
    freeze = tmp_path / FREEZE
    freeze.write_text(json.dumps(doc), encoding="utf-8")
    ledger.append(ledger_path, "PRECALIBRATION_SCIENCE_FROZEN",
                  science_freeze_sha256=file_sha256(freeze))
    assert science_freeze_ready(tmp_path)[0]
    (tmp_path / "quantlab5/v5/signals.py").write_text("altered", encoding="utf-8")
    assert not science_freeze_ready(tmp_path)[0]
