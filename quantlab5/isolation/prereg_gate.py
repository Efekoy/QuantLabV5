"""Fail closed on live V5 market reads until the complete prereg is tagged.

This is a runtime guard for the actual project root. Synthetic throwaway
projects continue to exercise the ordinary stage machine independently.
The final prereg freeze format must include every research code/config file.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text

FREEZE_NAME = "V5_PREREGISTRATION_FREEZE.json"


def prereg_ready(root: Path) -> tuple[bool, str]:
    path = root / FREEZE_NAME
    if not path.is_file():
        return False, "final V5 preregistration freeze is missing"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, "final V5 preregistration freeze is unreadable"
    if doc.get("kind") != "V5_FINAL_PREREGISTRATION" or doc.get("status") != "FINAL":
        return False, "V5 preregistration is not FINAL"
    body = {k: v for k, v in doc.items() if k != "body_sha256"}
    if sha256_text(canonical_json(body)) != doc.get("body_sha256"):
        return False, "V5 preregistration body hash mismatch"
    files = doc.get("files_sha256")
    if not isinstance(files, dict) or not files:
        return False, "V5 preregistration file hash map is missing"
    required = {"quantlab5/v5/signals.py", "quantlab5/v5/market_search.py",
                "quantlab5/v5/candidate_inventory.py", "config/stage_policy.yaml",
                "config/costs.yaml", "V5_RESEARCH_PREREGISTRATION.md"}
    if not required <= set(files):
        return False, "V5 preregistration lacks critical code/config hashes"
    for rel, expected in files.items():
        relative = Path(rel)
        if relative.is_absolute() or ".." in relative.parts:
            return False, "V5 preregistration contains an unsafe file path"
        source = root / relative
        if not source.is_file() or file_sha256(source) != expected:
            return False, f"V5 preregistration pinned file mismatch: {rel}"
    anchor = doc.get("ledger_anchor_before_discovery")
    if anchor is not None:
        from quantlab5.isolation import ledger
        ok, reason = ledger.verify(root / "ledgers/DATA_ACCESS_LEDGER.jsonl", anchor)
        if not ok:
            return False, f"V5 preregistration ledger anchor invalid: {reason}"
    try:
        subprocess.run(["git", "rev-parse", "v5-prereg^{commit}"],
                       cwd=root, capture_output=True, check=True)
        def blob_id_from_worktree(rel: str) -> str:
            return subprocess.run(["git", "hash-object", f"--path={rel}", rel],
                                  cwd=root, capture_output=True, text=True,
                                  check=True).stdout.strip()

        def blob_id_from_tag(rel: str) -> str:
            return subprocess.run(["git", "rev-parse", f"v5-prereg:{rel}"],
                                  cwd=root, capture_output=True, text=True,
                                  check=True).stdout.strip()

        if blob_id_from_worktree(FREEZE_NAME) != blob_id_from_tag(FREEZE_NAME):
            return False, "v5-prereg tag does not contain this exact freeze"
        for rel in files:
            if blob_id_from_worktree(rel) != blob_id_from_tag(rel):
                return False, f"v5-prereg pinned file mismatch: {rel}"
    except (OSError, subprocess.CalledProcessError):
        return False, "v5-prereg tag or pinned file is missing"
    return True, "final preregistration hashes and tag verify"
