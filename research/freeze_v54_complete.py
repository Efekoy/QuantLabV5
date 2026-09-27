"""Pin the complete V5.4 report and verify no LIVE_FORWARD access occurred."""
from __future__ import annotations

import json

from quantlab5.isolation import ledger
from quantlab5.isolation.stage_gate import current_stage
from quantlab5.project import ROOT, default_project
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v54.access import _frozen_file


OUT = ROOT / "V5_4_COMPLETE_RESEARCH_FREEZE.json"
FILES = ("V5_4_COMPLETE_RESEARCH_REPORT.md",
         "V5_4_BOTH_HISTORICAL_AUDITS_COMPLETE.json",
         "V5_4_HISTORICAL_AUDITS_REPORT.md",
         "reports/V5_4_HISTORICAL_AUDIT_RESULTS.json")


def main():
    if OUT.exists():
        raise RuntimeError("V5.4 complete freeze already exists")
    for name, tag in (("V5_4_DISCOVERY_FREEZE.json", "v5.4-discovery"),
                      ("V5_4_VALIDATION_FREEZE.json", "v5.4-validation"),
                      ("V5_4_SCIENTIFIC_COHORT_FREEZE.json", "v5.4-validation"),
                      ("V5_4_HISTORICAL_AUDIT_MANIFEST.json", "v5.4-cohort"),
                      ("V5_4_AUDIT_1_REPORT_FREEZE.json", "v5.4-audit1"),
                      ("V5_4_AUDIT_2_REPORT_FREEZE.json", "v5.4-audit2")):
        ok, reason = _frozen_file(ROOT, name, tag)
        if not ok:
            raise RuntimeError(reason)
    both = json.loads((ROOT / FILES[1]).read_text(encoding="utf-8"))
    body_both = {k: v for k, v in both.items() if k != "body_sha256"}
    if sha256_text(canonical_json(body_both)) != both["body_sha256"]:
        raise RuntimeError("both-audit reveal body changed")
    if file_sha256(ROOT / FILES[3]) != both["results_sha256"]:
        raise RuntimeError("simultaneous audit result changed")
    cohort = json.loads((ROOT / "V5_4_SCIENTIFIC_COHORT_FREEZE.json").read_text(encoding="utf-8"))
    first = json.loads((ROOT / "reports/v54/first_pass_complete.json").read_text(encoding="utf-8"))
    validation = json.loads((ROOT / "V5_4_VALIDATION_FREEZE.json").read_text(encoding="utf-8"))
    if both["candidate_ids"] != cohort["candidate_ids"]:
        raise RuntimeError("audit reveal changed the scientific cohort")
    if first["qualifier_count"] != validation["evaluated_count"]:
        raise RuntimeError("validation did not test every discovery qualifier")
    project = default_project()
    if current_stage(project) != "VALIDATION_FROZEN":
        raise RuntimeError("original V5 stage changed")
    ok, reason = ledger.verify(project.ledger_path)
    if not ok:
        raise RuntimeError(reason)
    if any(r["result"] == ledger.ALLOWED and r["partition"] == "LIVE_FORWARD"
           for r in ledger.data_reads(project.ledger_path)):
        raise RuntimeError("LIVE_FORWARD was opened")
    body = {"kind": "V5_4_COMPLETE_HISTORICAL_RESEARCH_FREEZE", "status": "FROZEN",
            "specifications_evaluated": first["specifications_evaluated"],
            "discovery_qualifiers": first["qualifier_count"],
            "validation_tested": validation["evaluated_count"],
            "scientific_cohort_ids": cohort["candidate_ids"],
            "dual_audit_supported_ids": both["dual_supported_ids"],
            "live_forward_sealed": True,
            "ledger_anchor": ledger.head(project.ledger_path),
            "files_sha256": {rel: file_sha256(ROOT / rel) for rel in FILES}}
    OUT.write_text(json.dumps({**body, "body_sha256": sha256_text(canonical_json(body))},
                              sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("V5.4 complete historical research freeze prepared")


if __name__ == "__main__":
    main()
