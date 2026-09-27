"""Pin the descriptive overlap supplement before the discovery tag is made."""
from __future__ import annotations

import json

from quantlab5.project import ROOT
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text


FREEZE = ROOT / "V5_4_DISCOVERY_FREEZE.json"
ARTIFACTS = ("V5_4_DISCOVERY_REPORT.md",
             "reports/V5_4_DISCOVERY_OVERLAP.jsonl",
             "reports/V5_4_DISCOVERY_OVERLAP_SUMMARY.json")


def main():
    doc = json.loads(FREEZE.read_text(encoding="utf-8"))
    body = {k: v for k, v in doc.items() if k != "body_sha256"}
    if sha256_text(canonical_json(body)) != doc["body_sha256"]:
        raise RuntimeError("original discovery freeze body changed")
    first = json.loads((ROOT / "reports/v54/first_pass_complete.json").read_text(encoding="utf-8"))
    if body["qualifier_count"] != first["qualifier_count"]:
        raise RuntimeError("discovery qualifier count differs from full first pass")
    for rel, expected in body["files_sha256"].items():
        if rel != "V5_4_DISCOVERY_REPORT.md" and file_sha256(ROOT / rel) != expected:
            raise RuntimeError(f"discovery source artifact changed: {rel}")
    overlap = json.loads((ROOT / ARTIFACTS[2]).read_text(encoding="utf-8"))
    if overlap["qualifier_count"] != body["qualifier_count"]:
        raise RuntimeError("overlap diagnostics omit discovery qualifiers")
    if sum(1 for _ in (ROOT / ARTIFACTS[1]).open("r", encoding="utf-8")) != body["qualifier_count"]:
        raise RuntimeError("overlap JSONL does not annotate every qualifier")
    for rel in ARTIFACTS:
        body["files_sha256"][rel] = file_sha256(ROOT / rel)
    body["descriptive_overlap_no_candidate_deletion"] = True
    FREEZE.write_text(json.dumps({**body, "body_sha256": sha256_text(canonical_json(body))},
                                 sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("V5.4 discovery freeze now pins all descriptive overlap outputs")


if __name__ == "__main__":
    main()
