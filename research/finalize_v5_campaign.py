"""Summarize the frozen V5 campaign after validation and joint audit reveal."""
from __future__ import annotations

import json
import subprocess

from quantlab5.isolation import ledger
from quantlab5.isolation.prereg_gate import prereg_ready
from quantlab5.isolation.stage_gate import current_stage
from quantlab5.project import ROOT, default_project
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text

READS_MARKET_DATA = False
OUT = ROOT / "V5_COMPLETE_RESEARCH_REPORT.md"


def _read(rel):
    return json.loads((ROOT/rel).read_text(encoding="utf-8"))


def main():
    if OUT.exists():
        raise RuntimeError("final campaign report already exists")
    ok, reason = prereg_ready(ROOT)
    if not ok:
        raise RuntimeError(reason)
    project = default_project()
    stage = current_stage(project)
    disc, val = _read("reports/V5_DISCOVERY_EXECUTABLE.json"), _read("reports/V5_VALIDATION_EXECUTABLE.json")
    cohort = _read("V5_SCIENTIFIC_COHORT_FREEZE.json")
    ids = sorted(cohort["candidate_ids"])
    if sorted(val["survivor_ids"]) != ids:
        raise RuntimeError("scientific cohort differs from supported validation survivors")
    a1 = a2 = None
    if ids:
        marker = _read("BOTH_HISTORICAL_AUDITS_COMPLETE.json")
        body = {k: v for k, v in marker.items() if k != "body_sha256"}
        if (sha256_text(canonical_json(body)) != marker.get("body_sha256")
                or marker["status"] != "COMPLETE"):
            raise RuntimeError("joint audit completion marker invalid")
        p1 = ROOT/"reports/V5_HISTORICAL_AUDIT_1_REPORT.json"
        p2 = ROOT/"reports/V5_HISTORICAL_AUDIT_2_REPORT.json"
        if file_sha256(p1) != marker["audit_1_sha256"] or file_sha256(p2) != marker["audit_2_sha256"]:
            raise RuntimeError("public audits do not match joint marker")
        a1, a2 = _read("reports/V5_HISTORICAL_AUDIT_1_REPORT.json"), _read("reports/V5_HISTORICAL_AUDIT_2_REPORT.json")
        if a1["candidate_ids"] != ids or a2["candidate_ids"] != ids:
            raise RuntimeError("audits evaluated different candidate sets")
        if stage != "HISTORICAL_AUDIT_2":
            raise RuntimeError("audits complete but stage state differs")
    elif stage != "VALIDATION_FROZEN":
        raise RuntimeError("empty cohort has unexpected stage state")
    reads = ledger.data_reads(project.ledger_path)
    allowed = [r for r in reads if r.get("result") == ledger.ALLOWED]
    if any(r.get("partition") == "LIVE_FORWARD" for r in allowed):
        raise RuntimeError("LIVE_FORWARD access was recorded")
    ok, reason = ledger.verify(project.ledger_path)
    if not ok:
        raise RuntimeError(reason)
    prereg_commit = subprocess.run(["git", "rev-parse", "v5-prereg^{commit}"],
                                   cwd=ROOT, capture_output=True, text=True,
                                   check=True).stdout.strip()
    tests = _read("reports/V5_PREDISCOVERY_TESTS.json")
    by_stage = {s: sum(r["stage"] == s for r in disc["records"].values()) for s in ("A", "B", "C")}
    lines = ["# V5 historical research report", "",
             f"Final pre-DISCOVERY commit/tag: `{prereg_commit}` / `v5-prereg`.",
             f"Complete pre-DISCOVERY suite: {tests['passed']} passed, {tests.get('skipped', 0)} skipped.",
             f"Stage inventory actually evaluated: A={by_stage['A']}, B={by_stage['B']}, C={by_stage['C']}; "
             f"total={disc['candidate_count']}.",
             f"DISCOVERY qualifiers: {disc['qualifier_count']}; exact candidates tested in VALIDATION: "
             f"{len(val['candidate_ids'])}.",
             f"VALIDATION SUPPORTED={val['class_counts']['SUPPORTED']}, "
             f"INCONCLUSIVE / UNDERPOWERED={val['class_counts']['INCONCLUSIVE / UNDERPOWERED']}, "
             f"REJECTED={val['class_counts']['REJECTED']}.",
             "", "## Complete scientific cohort", "",
             ", ".join(ids) if ids else "Empty: no exact candidate passed frozen validation confirmation.",
             "", "## Historical audit outcomes", ""]
    if ids:
        both = only_one = neither = 0
        lines += ["| Q5 ID | Validation | 2023–2025 | 2026 | $250/$300/$350/$400 coverage |",
                  "| --- | --- | --- | --- | --- |"]
        for cid in ids:
            x, y = a1["rows"][cid], a2["rows"][cid]
            s1, s2 = x["classification"] == "SUPPORTED", y["classification"] == "SUPPORTED"
            both += s1 and s2
            only_one += s1 != s2
            neither += not s1 and not s2
            coverage = "/".join(f"{x['mnq_budget_coverage'][str(b)]['coverage']:.2f}"
                                for b in (250, 300, 350, 400))
            lines.append(f"| {cid} | SUPPORTED | {x['classification']} | {y['classification']} | {coverage} |")
        lines += ["", f"Supported in both audits: {both}; exactly one: {only_one}; neither: {neither}."]
    else:
        lines.append("No scientific cohort existed; neither audit partition was opened.")
    lines += ["", "## Duplicates, deployment and limitations", "",
              f"Exact signal duplicates annotated: {sum(k != v for k,v in disc['exact_duplicate_of'].items())}; "
              f"behavioral duplicates annotated: {sum(k != v for k,v in disc['behavior_duplicate_of'].items())}. "
              "No duplicate annotation removed a qualifier.",
              "Individual integer MNQ coverage at $250/$300/$350/$400 is retained in each period's full JSON. "
              "No portfolio or prop configuration was selected in this revised scientific campaign.",
              "The synthetic/direct-null market program was abandoned after its frozen gates failed; "
              "its reports and tags remain intact. Discovery is exploratory. Day-block bootstrap "
              "inference is approximate under regime change; costs include unvalidated MNQ commission "
              "assumptions. Earlier V2/V3/V4 knowledge contaminates researcher-level historical blinding. "
              "The strongest future evidence requires sessions arriving after final V5 freeze.",
              "", "## Access status", "",
              f"Stage: `{stage}`. Main ledger: {reason}. Allowed DATA_READ records: {len(allowed)}. "
              "LIVE_FORWARD allowed reads: 0. LIVE_FORWARD remains sealed.", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"V5 historical campaign report written: cohort {len(ids)}")


if __name__ == "__main__":
    main()
