"""Sequential evaluation-only audits with a single simultaneous reveal."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import shutil

from quantlab5.data.market import load_market
from quantlab5.engine.costs import CostModel
from quantlab5.isolation.manifests import (build_manifest, read_manifest,
                                           verify_manifest, write_manifest)
from quantlab5.isolation.stage_gate import advance, current_stage
from quantlab5.project import ROOT, default_project
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v5.audit import evaluate_exact_cohort

READS_MARKET_DATA = True
AUDIT_MANIFEST = ROOT / "V5_HISTORICAL_AUDIT_MANIFEST.json"
HIDDEN = ROOT / "reports/.blind"
A1 = HIDDEN / "V5_AUDIT_1_RESULT.json"
A2 = HIDDEN / "V5_AUDIT_2_RESULT.json"
BOTH = ROOT / "BOTH_HISTORICAL_AUDITS_COMPLETE.json"


def _write_once(path, obj):
    if path.exists():
        raise RuntimeError(f"audit output already exists: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, indent=2, allow_nan=False)+"\n",
                    encoding="utf-8")


def _manifest(project):
    verify_manifest(AUDIT_MANIFEST, ROOT, "V5_HISTORICAL_AUDIT_MANIFEST",
                    ("cohort", "specs", "rules"))
    doc = read_manifest(AUDIT_MANIFEST)
    sections = doc["sections"]
    ids = tuple(sorted(sections["cohort"]))
    if ids != tuple(sorted(sections["specs"])):
        raise RuntimeError("audit manifest cohort differs from exact specs")
    if not ids:
        raise RuntimeError("empty cohort has no historical candidates to audit")
    return ids, sections["specs"]


def _evaluate(partition, start, end, specs, costs, seed):
    market = load_market(partition, start, end, purpose="V5_FROZEN_BLIND_AUDIT")
    return evaluate_exact_cohort(market, specs, costs, seed=seed)


def main():
    project = default_project()
    ids, specs = _manifest(project)
    costs = CostModel.from_project(project)
    stage = current_stage(project)
    if stage == "FINAL_COHORT_FROZEN":
        advance(project, "HISTORICAL_AUDIT_1")
        stage = current_stage(project)
    if stage == "HISTORICAL_AUDIT_1":
        if not A1.exists():
            result = _evaluate("HISTORICAL_AUDIT_1", "2023-01-03", "2025-12-31",
                               specs, costs, 615005)
            if result["candidate_ids"] != list(ids):
                raise RuntimeError("Audit 1 candidate set changed")
            _write_once(A1, result)
        freeze = project.freeze_path("audit_1_report")
        if not freeze.exists():
            doc = build_manifest("AUDIT_1_REPORT_FREEZE",
                                 {"report": {"path": "reports/.blind/V5_AUDIT_1_RESULT.json",
                                             "sha256": file_sha256(A1),
                                             "cohort_ids_sha256": sha256_text("\n".join(ids))},
                                  "sealed": True}, ROOT,
                                 files=("reports/.blind/V5_AUDIT_1_RESULT.json",
                                        "V5_HISTORICAL_AUDIT_MANIFEST.json"))
            write_manifest(freeze, doc)
        verify_manifest(freeze, ROOT, "AUDIT_1_REPORT_FREEZE", ("report",))
        advance(project, "HISTORICAL_AUDIT_2")
        stage = current_stage(project)
    if stage != "HISTORICAL_AUDIT_2":
        raise RuntimeError(f"blind audit worker cannot run from {stage}")
    # Only A1's hash and frozen cohort fingerprint are touched here. Its
    # performance rows remain unread until A2 has completed.
    a1_freeze = read_manifest(project.freeze_path("audit_1_report"))["sections"]["report"]
    if (file_sha256(A1) != a1_freeze["sha256"]
            or a1_freeze["cohort_ids_sha256"] != sha256_text("\n".join(ids))):
        raise RuntimeError("sealed Audit 1 hash/cohort mismatch")
    if not A2.exists():
        endpoint = min(project.partitions()["registry"]["historical_audit_2_last_session"].values())
        result = _evaluate("HISTORICAL_AUDIT_2", "2026-01-02", endpoint,
                           specs, costs, 715005)
        if result["candidate_ids"] != list(ids):
            raise RuntimeError("Audit 2 candidate set changed")
        _write_once(A2, result)
    # A2 may be read only for its candidate IDs before the joint marker.
    a2 = json.loads(A2.read_text(encoding="utf-8"))
    if a2["candidate_ids"] != list(ids):
        raise RuntimeError("Audit 2 candidate set differs from frozen cohort")
    if not BOTH.exists():
        body = {"kind": "BOTH_HISTORICAL_AUDITS_COMPLETE", "status": "COMPLETE",
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "audit_1_sha256": file_sha256(A1), "audit_2_sha256": file_sha256(A2),
                "cohort_ids_sha256": sha256_text("\n".join(ids)),
                "audit_manifest_sha256": file_sha256(AUDIT_MANIFEST)}
        _write_once(BOTH, {**body, "body_sha256": sha256_text(canonical_json(body))})
    marker = json.loads(BOTH.read_text(encoding="utf-8"))
    body = {k: v for k, v in marker.items() if k != "body_sha256"}
    if (sha256_text(canonical_json(body)) != marker["body_sha256"]
            or marker["audit_1_sha256"] != file_sha256(A1)
            or marker["audit_2_sha256"] != file_sha256(A2)):
        raise RuntimeError("simultaneous audit marker fails verification")
    public_a1 = ROOT / "reports/V5_HISTORICAL_AUDIT_1_REPORT.json"
    public_a2 = ROOT / "reports/V5_HISTORICAL_AUDIT_2_REPORT.json"
    for source, target in ((A1, public_a1), (A2, public_a2)):
        if target.exists():
            if file_sha256(target) != file_sha256(source):
                raise RuntimeError("previous public audit report differs from hidden result")
        else:
            shutil.copyfile(source, target)
    print("Both historical audits complete; simultaneous reports available")


if __name__ == "__main__":
    main()
