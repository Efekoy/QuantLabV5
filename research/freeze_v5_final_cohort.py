"""Freeze every validation survivor and the empty portfolio set before audits."""
from __future__ import annotations

import json

from quantlab5.isolation.manifests import (build_manifest, verify_manifest,
                                           write_manifest)
from quantlab5.isolation.stage_gate import advance, current_stage
from quantlab5.project import ROOT, default_project
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text

READS_MARKET_DATA = False
COHORT = ROOT / "V5_SCIENTIFIC_COHORT_FREEZE.json"
AUDIT = ROOT / "V5_HISTORICAL_AUDIT_MANIFEST.json"


def main():
    project = default_project()
    verify_manifest(project.freeze_path("validation"), ROOT, "VALIDATION_FREEZE",
                    ("validation_rules_sha256",))
    doc = json.loads(COHORT.read_text(encoding="utf-8"))
    body = {k: v for k, v in doc.items() if k != "body_sha256"}
    if (sha256_text(canonical_json(body)) != doc.get("body_sha256")
            or doc.get("status") != "FROZEN"):
        raise RuntimeError("scientific cohort freeze is invalid")
    ids = tuple(doc["candidate_ids"])
    specs = doc["specs"]
    if len(ids) != len(set(ids)) or set(ids) != set(specs):
        raise RuntimeError("scientific cohort ID/spec mismatch")
    if current_stage(project) == "VALIDATION":
        advance(project, "VALIDATION_FROZEN")
    if current_stage(project) != "VALIDATION_FROZEN":
        raise RuntimeError("scientific cohort requires frozen validation")
    if not ids:
        print("No validation-supported candidates: no historical audit cohort to open")
        return
    if AUDIT.exists() or project.freeze_path("final_cohort").exists():
        raise RuntimeError("final cohort/audit manifest already exists")
    sections = {"cohort": list(ids), "parameters": specs,
                "prop_selection_rules": {"status": "EXCLUDED_FROM_PRIMARY_V5"},
                "risk_rules": {"budgets_usd": [250, 300, 350, 400],
                               "integer_mnq": True, "one_micro_floor": "SKIP"},
                "portfolio_rules": {"selected_portfolios": [],
                                    "reason": "not part of revised scientific campaign"},
                "sizing_rules": {"config": "config/costs.yaml",
                                 "budgets_usd": [250, 300, 350, 400]},
                "selection_process": "all supported validation exact candidates; no rank or correlation deletion"}
    manifest = build_manifest("FINAL_COHORT_FREEZE", sections, ROOT,
                              files=("V5_SCIENTIFIC_COHORT_FREEZE.json",
                                     "V5_VALIDATION_FREEZE.json",
                                     "V5_HOLDOUT_CONFIRMATION_PROTOCOL_FREEZE.json"))
    write_manifest(project.freeze_path("final_cohort"), manifest)
    validation = json.loads((ROOT/"V5_VALIDATION_FREEZE.json").read_text(encoding="utf-8"))
    audit_sections = {
        "cohort": list(ids), "specs": specs,
        "validation_classifications": {cid: validation["classifications"][cid] for cid in ids},
        "portfolio_definitions": {"selected_portfolios": []},
        "rules": {"audit_1": ["2023-01-03", "2025-12-31"],
                  "audit_2_start": "2026-01-02",
                  "audit_2_end": "minimum registered NQ/ES last session",
                  "same_cohort_both": True, "simultaneous_reveal": True,
                  "costs": "config/costs.yaml"},
    }
    audit_manifest = build_manifest("V5_HISTORICAL_AUDIT_MANIFEST",
                                    audit_sections, ROOT,
                                    files=("V5_SCIENTIFIC_COHORT_FREEZE.json",
                                           "V5_VALIDATION_FREEZE.json",
                                           "V5_HOLDOUT_CONFIRMATION_PROTOCOL_FREEZE.json",
                                           "quantlab5/v5/audit.py",
                                           "research/run_v5_blind_audits.py",
                                           "config/costs.yaml"))
    write_manifest(AUDIT, audit_manifest)
    advance(project, "FINAL_COHORT_FROZEN")
    print(f"Final scientific cohort and blind audit manifest frozen: {len(ids)} candidates")


if __name__ == "__main__":
    main()
