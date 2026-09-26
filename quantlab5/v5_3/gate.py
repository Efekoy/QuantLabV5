"""Verify the V5.3 generator design freeze before fidelity or power work."""
from __future__ import annotations

import json
from pathlib import Path

from quantlab5.project import ROOT
from quantlab5.search.candidate_id import candidate_id
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v5.candidate_inventory import inventory

FREEZE = ROOT / "V5_3_GENERATOR_PROTOCOL_FREEZE.json"


def freeze_ready() -> tuple[bool, str]:
    try:
        doc = json.loads(FREEZE.read_text(encoding="utf-8"))
        if doc.get("kind") != "V5_3_GENERATOR_PROTOCOL_FREEZE" or doc.get("status") != "FROZEN":
            return False, "V5.3 generator protocol is not frozen"
        body = {k: v for k, v in doc.items() if k != "body_sha256"}
        if sha256_text(canonical_json(body)) != doc.get("body_sha256"):
            return False, "V5.3 freeze body hash mismatch"
        for rel, expected in doc["files_sha256"].items():
            p = Path(rel)
            if p.is_absolute() or ".." in p.parts or file_sha256(ROOT / p) != expected:
                return False, f"V5.3 pinned file mismatch: {rel}"
        inv = inventory()
        stage_a = [candidate_id(x) for x in inv["stage_a"]]
        universe = [candidate_id(x) for x in (inv["stage_a"]+inv["stage_b"]
                                               + inv["stage_c_universe"])]
        if (doc.get("stage_a_ids_sha256") != sha256_text("\n".join(stage_a))
                or doc.get("candidate_universe_ids_sha256") != sha256_text("\n".join(universe))):
            return False, "V5.3 candidate IDs differ from inherited grammar"
        stress = json.loads((ROOT / "reports/V5_3_STRUCTURAL_STRESS.json").read_text(encoding="utf-8"))
        if (stress.get("status") != "PASS" or stress.get("completed_worlds") != 1001
                or stress.get("invalid_worlds") != 0):
            return False, "V5.3 structural stress no longer passes"
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return False, f"V5.3 generator freeze invalid: {exc}"
    return True, "V5.3 generator protocol verifies"
