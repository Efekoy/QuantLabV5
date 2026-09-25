"""s02 -- Bootstrap freeze. Verifies the bootstrap and writes freezes/V5_BOOTSTRAP_FREEZE.json.
(Ported from QuantLabV4 research/s02_bootstrap_freeze.py; V5 sections added.)

    python research/s02_bootstrap_freeze.py

Requires a CLEAN git working tree (the freeze pins the committed code). Checks:
  1. stage is DISCOVERY
  2. data-access ledger verifies; no ALLOWED research read of any partition but DISCOVERY
  3. every registered partition file still matches its hash (and each source file)
  4. hashes every git-tracked file (code, config, docs, tests, provenance)
  5. writes the freeze (write-once, read-only) and re-verifies it reproduces every hash
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from quantlab5 import research_log as RL  # noqa: E402
from quantlab5.isolation import ledger  # noqa: E402
from quantlab5.isolation.manifests import build_manifest, verify_manifest, write_manifest  # noqa: E402
from quantlab5.isolation.stage_gate import current_stage, registry_hash, verify_registry_files  # noqa: E402
from quantlab5.project import default_project  # noqa: E402
from quantlab5.util.hashing import file_sha256  # noqa: E402

READS_MARKET_DATA = False
EXCLUDE_PREFIX = ("ledgers/", "freezes/")
EXCLUDE = {"provenance/AUTONOMOUS_RESUME_STATE.json"}


def git(*a) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *a], text=True).strip()


def main() -> None:
    p = default_project()
    if git("status", "--porcelain", "--untracked-files=no"):
        raise SystemExit("working tree has uncommitted changes to tracked files; commit first")
    commit = git("rev-parse", "HEAD")
    stage = current_stage(p)
    assert stage == "DISCOVERY", stage
    ok, msg = ledger.verify(p.ledger_path)
    assert ok, msg
    reads = ledger.data_reads(p.ledger_path)
    forbidden = [r for r in reads if r["result"] == "ALLOWED" and r["partition"] != "DISCOVERY"]
    assert not forbidden, f"forbidden reads: {forbidden}"
    parts = verify_registry_files(p)
    reg = p.partitions()["registry"]
    for k, s in reg["sources"].items():
        assert file_sha256(Path(s["path"])) == s["sha256"], f"source {k} changed"
    files = [f for f in git("ls-files").splitlines()
             if not f.startswith(EXCLUDE_PREFIX) and f not in EXCLUDE]
    tenv = json.loads((ROOT / "provenance" / "TEST_ENVIRONMENT.json").read_text())
    user = os.environ.get("USERNAME", "unknown")
    iso = json.loads((ROOT / "provenance" / f"ISOLATION_CHECK_{user}.json").read_text())
    reg_defs = p.partitions()["definitions"]
    if tenv["failures"] or tenv["errors"] or tenv["exit_code"]:
        raise SystemExit(f"test suite not green ({tenv['summary_line']}); refusing to freeze")
    sections = {
        "purpose": "QuantLabV5 bootstrap checkpoint: infrastructure only, no strategy research, no V5 catalog",
        "code_commit": commit, "stage": stage,
        "registry_sha256": registry_hash(p), "partition_sha256": parts,
        "source_sha256": {k: s["sha256"] for k, s in reg["sources"].items()},
        "data_reads": {"allowed": sum(r["result"] == "ALLOWED" for r in reads),
                       "refused": sum(r["result"] == "REFUSED" for r in reads),
                       "allowed_non_discovery": 0},
        "tests": {k: tenv[k] for k in ("tests", "failures", "errors", "skipped", "summary_line")},
        "os_isolation_active": iso["os_isolation_active_for_this_account"],
        "os_isolation_check": {"user": iso["user"], "checked_utc": iso["checked_utc"],
                               "sealed_and_raw_all_denied": iso["sealed_and_raw_all_denied"]},
        "partition_definitions": reg_defs,
        "joint_last_complete_session": reg["joint_last_complete_session"],
        "historical_audit_2_last_session": reg["historical_audit_2_last_session"],
        "v4_crosscheck_identical": {x["v5"]: x["identical_file"] for x in reg["v4_crosscheck"]},
        "no_candidate_cap": p.stage_policy["no_candidate_cap"],
        "v4_source_commit": json.loads((ROOT / "provenance" / "V4_COPIED_FILES.json").read_text())["v4_git_head"],
        "v4_files_copied": len(json.loads((ROOT / "provenance" / "V4_COPIED_FILES.json").read_text())["files"]),
        "prior_labs_manifest_sha256": file_sha256(ROOT / "provenance" / "PRIOR_LABS_MANIFEST.json"),
    }
    doc = build_manifest("V5_BOOTSTRAP_FREEZE", sections, ROOT, files, ledger_anchor=ledger.head(p.ledger_path),
                         git_commit=commit)
    path = ROOT / "freezes" / "V5_BOOTSTRAP_FREEZE.json"
    if path.exists():
        raise SystemExit(f"{path.name} exists")
    sha = write_manifest(path, doc)
    assert verify_manifest(path, ROOT, "V5_BOOTSTRAP_FREEZE") == sha
    assert ledger.verify(p.ledger_path, doc["ledger_anchor"])[0]
    ledger.append(p.ledger_path, "BOOTSTRAP_FREEZE", ledger.INFO, "bootstrap frozen", freeze_sha256=sha,
                  code_commit=commit)
    RL.log(p, "FREEZE", "V5 bootstrap freeze written", freeze_sha256=sha, code_commit=commit, files=len(files))
    print(f"[s02] freeze {path.name} body_sha256={sha} files={len(files)} code_commit={commit}")
    print("[s02] reproduction check: OK")


if __name__ == "__main__":
    main()
