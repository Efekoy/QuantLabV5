"""Fail closed on V5.4 real reads until its complete tagged freeze verifies."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from quantlab5.isolation import ledger
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text


NAME = "V5_4_PREREGISTRATION_FREEZE.json"
TAG = "v5.4-prereg"


def ready(root: Path) -> tuple[bool, str]:
    path = root / NAME
    if not path.is_file():
        return False, "V5.4 preregistration freeze is missing"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
        body = {k: v for k, v in doc.items() if k != "body_sha256"}
        if (doc.get("kind") != "V5_4_FINAL_PREREGISTRATION"
                or doc.get("status") != "FINAL"
                or sha256_text(canonical_json(body)) != doc.get("body_sha256")):
            return False, "V5.4 preregistration body is not final or has changed"
        files = doc.get("files_sha256")
        if not isinstance(files, dict) or not files:
            return False, "V5.4 pinned file map is missing"
        critical = {"V5_4_SEARCH_UNIVERSE.json", "V5_4_RESEARCH_PROTOCOL.md",
                    "quantlab5/v54/universe.py", "quantlab5/v54/engine.py",
                    "quantlab5/v54/events.py", "quantlab5/isolation/load_view.py",
                    "config/costs.yaml", "research/run_v54_discovery.py"}
        if not critical <= set(files):
            return False, "V5.4 preregistration omits critical code/config"
        for rel, expected in files.items():
            p = Path(rel)
            if p.is_absolute() or ".." in p.parts or not (root/p).is_file():
                return False, f"unsafe or missing V5.4 pinned file: {rel}"
            if file_sha256(root/p) != expected:
                return False, f"V5.4 pinned file mismatch: {rel}"
        ok, reason = ledger.verify(root/"ledgers/DATA_ACCESS_LEDGER.jsonl",
                                   doc.get("ledger_anchor_before_v54"))
        if not ok:
            return False, f"V5.4 ledger anchor invalid: {reason}"
        def rev(rel):
            return subprocess.run(["git", "rev-parse", f"{TAG}:{rel}"], cwd=root,
                                  check=True, capture_output=True, text=True).stdout.strip()
        def work(rel):
            return subprocess.run(["git", "hash-object", f"--path={rel}", rel],
                                  cwd=root, check=True, capture_output=True,
                                  text=True).stdout.strip()
        if rev(NAME) != work(NAME):
            return False, "V5.4 tag does not contain this exact freeze"
        for rel in files:
            if rev(rel) != work(rel):
                return False, f"V5.4 tagged file differs: {rel}"
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        return False, f"V5.4 freeze verification failed: {exc}"
    return True, "V5.4 hashes, ledger anchor, and tag verify"
