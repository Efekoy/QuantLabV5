"""Copy the V2/V3/V4 catalogs and reports into docs/prior_labs/ (reference only; run once).

    python tools/collect_prior_labs.py

These files record what earlier labs already tested and what they concluded, so that V5 can later
avoid re-testing the same things unknowingly. They are NOT inputs to any V5 research code:
  * nothing under quantlab5/ or research/ may reference docs/prior_labs (static test
    tests/test_prior_labs_separation.py);
  * catalog source code (.py) is stored with a `.txt` suffix so it can never be imported;
  * text files over 2 MB are stored gzipped (uncompressed content hash == source_sha256);
  * no market data, trade lists, per-candidate result tables, ledgers or null-world files are copied.

Every file is recorded in provenance/PRIOR_LABS_MANIFEST.json with its source path, source SHA-256,
destination SHA-256 and the source repository's git HEAD / whether the source file was committed.

Important: prior labs looked at 2019-2026 data (V4 used exactly the V5 VALIDATION / HISTORICAL_AUDIT
periods). Reading these reports is knowledge of those periods. See V5_BOOTSTRAP_REPORT.md.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

V5 = Path(__file__).resolve().parents[1]
DESK = V5.parent
DEST = V5 / "docs" / "prior_labs"

V2_FILES = [
    "README.md", "BUILD_REPORT.md", "STRATEGY_CATALOG.md", "NEXT_COMMANDS.md",
    "config/search_space.yaml", "config/research.yaml", "config/final_cohort.yaml", "config/null_funnel.yaml",
    "results/README.md",
    "results/archive/OFFICIAL_EXPERIMENT_2026-09-22/MASTER_RESEARCH_RECORD.md",
    "results/archive/OFFICIAL_EXPERIMENT_2026-09-22/VERIFIED_FACTS.json",
    "results/edge_isolation/EDGE_ISOLATION_REPORT.md", "results/edge_isolation/INTERPRETATION.md",
    "results/edge_isolation/CLUSTERING_PREREGISTRATION.md",
    "results/edge_isolation/CLUSTER_EVIDENCE_PREREGISTRATION.md",
    "results/edge_isolation/PROPOSED_FINAL_SELECTION_RULE.md",
    "results/final_cohort/FINAL_COHORT_REPORT.md", "results/final_cohort/FINAL_FORWARD_COHORT.md",
    "results/final_cohort/RULE_CARDS.md", "results/final_cohort/SELECTION_AUDIT.md",
    "results/final_cohort/forward/FORWARD_PROTOCOL.md", "results/final_cohort/forward/FORWARD_REPORT.md",
    "results/main/reports/DISCOVERY_REPORT.md", "results/null_funnel/config/CLASSIFICATION_RULE.md",
    "results/report/QuantLabV2_Research_Record.pdf",
]
V3_FILES = [
    "README.md", "V3_BOOTSTRAP_REPORT.md", "config/search_space.yaml", "config/research.yaml",
    "preregistration/README.md", "preregistration/V3_DISCOVERY_PREREGISTRATION.md",
    "preregistration/V3_DISCOVERY_PREREGISTRATION.json", "preregistration/V3_CONFIRMATION_PREREGISTRATION.md",
    "preregistration/V3_CONFIRMATION_PREREGISTRATION.json", "strategies/README.md",
    "core/quantlab3/strategies/families/v3_catalog.py", "core/quantlab3/strategies/families/v3_common.py",
    "freezes/README.md", "freezes/DISCOVERY_FREEZE.json", "freezes/DISCOVERY_CANDIDATE_LABELS.json",
    "freezes/FINAL_COHORT_FREEZE.json", "freezes/V3_RESEARCH_FREEZE.json", "forward/FORWARD_PROTOCOL.md",
    "results/README.md", "results/V3_MASTER_RESEARCH_RECORD.md", "results/holdout/REPORT.json",
    "results/audit2026/REPORT.json", "results/audit2026/ERRATUM_2026-09-22.json",
    "results/confirmation/FINAL_SELECTION.json",
] + [f"reports/{p.name}" for p in sorted((DESK / "QuantLabV3" / "reports").glob("*.pdf"))]
V4_FILES = (
    [p.name for p in sorted((DESK / "QuantLabV4").glob("V4_*.md"))]
    + [p.name for p in sorted((DESK / "QuantLabV4").glob("V4_*.json"))]
    + ["README.md", "config/prereg_v4.yaml", "docs/INHERITED_FROM_V3.md", "docs/REMAINING_WORK.md",
       "output/pdf/V4_COMPLETE_RESEARCH_REPORT.pdf"]
    + [f"freezes/{p.name}" for p in sorted((DESK / "QuantLabV4" / "freezes").glob("*.json"))]
)
GZIP_ABOVE = 2_000_000             # large JSON catalogs are stored gzipped (git size); PDFs are copied as-is
LABS = {"V2": ("QuantLabV2", V2_FILES), "V3": ("QuantLabV3", V3_FILES), "V4": ("QuantLabV4", V4_FILES)}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(root: Path, *a) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(root), *a], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:          # noqa: BLE001
        return ""


def main() -> None:
    man = V5 / "provenance" / "PRIOR_LABS_MANIFEST.json"
    if man.exists():
        raise SystemExit(f"{man} exists; the collection is a one-time step")
    doc = {"collected_utc": datetime.now(timezone.utc).isoformat(), "purpose": "reference only; never a V5 input",
           "labs": {}}
    for lab, (dirname, files) in LABS.items():
        root = DESK / dirname
        tracked = set(git(root, "ls-files").splitlines())
        dirty = set(x[3:] for x in git(root, "status", "--porcelain").splitlines())
        recs = []
        for rel in files:
            src = root / rel
            if not src.is_file():
                recs.append({"source": rel, "status": "MISSING_AT_SOURCE"})
                continue
            dst_rel = rel + ".txt" if rel.endswith(".py") else rel
            big = src.stat().st_size > GZIP_ABOVE and not rel.endswith(".pdf")
            dst = DEST / lab / (dst_rel + ".gz" if big else dst_rel)
            dst.parent.mkdir(parents=True, exist_ok=True)
            if big:                       # deterministic gzip (mtime 0); content hash == source hash
                with open(src, "rb") as fi, gzip.GzipFile(dst, "wb", compresslevel=9, mtime=0) as fo:
                    shutil.copyfileobj(fi, fo)
            else:
                shutil.copyfile(src, dst)
            recs.append({"source": rel, "source_sha256": sha(src), "destination": dst.relative_to(V5).as_posix(),
                         "destination_sha256": sha(dst), "bytes": src.stat().st_size, "gzipped": big,
                         "committed_in_source_repo": rel in tracked and rel not in dirty})
        doc["labs"][lab] = {"root": str(root), "git_head": git(root, "rev-parse", "HEAD") or None, "files": recs}
        print(f"{lab}: {sum('destination' in r for r in recs)} files, "
              f"{sum(r.get('status') == 'MISSING_AT_SOURCE' for r in recs)} missing")
    man.write_text(json.dumps(doc, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
