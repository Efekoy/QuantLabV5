"""Pin the entire supported cohort and audit contract before either audit read."""
from __future__ import annotations

import json

from quantlab5.project import ROOT, default_project
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v54.access import _frozen_file


OUT = ROOT / "V5_4_HISTORICAL_AUDIT_MANIFEST.json"


def main():
    if OUT.exists():
        raise RuntimeError("V5.4 audit manifest already exists")
    for name in ("V5_4_VALIDATION_FREEZE.json", "V5_4_SCIENTIFIC_COHORT_FREEZE.json"):
        ok, reason = _frozen_file(ROOT, name, "v5.4-validation")
        if not ok:
            raise RuntimeError(reason)
    cohort = json.loads((ROOT / "V5_4_SCIENTIFIC_COHORT_FREEZE.json").read_text(encoding="utf-8"))
    ids = cohort["candidate_ids"]
    if len(ids) != len(set(ids)) or set(ids) != set(cohort["specs"]):
        raise RuntimeError("V5.4 cohort IDs/specifications are inconsistent")
    endpoint = min(default_project().partitions()["registry"]
                   ["historical_audit_2_last_session"].values())
    code = ("quantlab5/v54/universe.py", "quantlab5/v54/events.py",
            "quantlab5/v54/engine.py", "quantlab5/v54/inference.py",
            "research/run_v54_blind_audits.py", "config/costs.yaml")
    body = {"kind": "V5_4_HISTORICAL_AUDIT_MANIFEST", "status": "FROZEN",
            "cohort_sha256": file_sha256(ROOT / "V5_4_SCIENTIFIC_COHORT_FREEZE.json"),
            "candidate_ids": ids, "candidate_count": len(ids),
            "specs_sha256": sha256_text(canonical_json(cohort["specs"])),
            "audit_1": ["2023-01-03", "2025-12-31"],
            "audit_2": ["2026-01-02", endpoint],
            "same_cohort_both_audits": True, "portfolio_selection": "none",
            "files_sha256": {rel: file_sha256(ROOT / rel) for rel in code}}
    OUT.write_text(json.dumps({**body, "body_sha256": sha256_text(canonical_json(body))},
                              sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(f"V5.4 audit manifest frozen for {len(ids):,} exact candidates")


if __name__ == "__main__":
    main()
