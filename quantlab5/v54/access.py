"""Separate V5.4 phase gates atop the immutable original V5 stage history."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v54.prereg_gate import ready


PHASES = {
    "V5_4_FROZEN_BROAD_DISCOVERY": ("DISCOVERY", "2010-06-08", "2018-12-31",
                                     None, None),
    "V5_4_FROZEN_VALIDATION": ("VALIDATION", "2019-01-02", "2022-12-30",
                               "V5_4_DISCOVERY_FREEZE.json", "v5.4-discovery"),
    "V5_4_BLIND_AUDIT_1": ("HISTORICAL_AUDIT_1", "2023-01-03", "2025-12-31",
                            "V5_4_HISTORICAL_AUDIT_MANIFEST.json", "v5.4-cohort"),
    "V5_4_BLIND_AUDIT_2": ("HISTORICAL_AUDIT_2", "2026-01-02", None,
                            "V5_4_AUDIT_1_REPORT_FREEZE.json", "v5.4-audit1"),
}
EXPECTED_COLUMNS = ["open", "high", "low", "close", "volume", "symbol"]


def _frozen_file(root: Path, name: str, tag: str) -> tuple[bool, str]:
    p = root/name
    if not p.is_file():
        return False, f"V5.4 prior phase freeze missing: {name}"
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
        body = {k: v for k, v in doc.items() if k != "body_sha256"}
        if (doc.get("status") != "FROZEN"
                or sha256_text(canonical_json(body)) != doc.get("body_sha256")):
            return False, f"V5.4 prior phase freeze body changed: {name}"
        for rel, expected in doc.get("files_sha256", {}).items():
            if file_sha256(root/rel) != expected:
                return False, f"V5.4 prior phase artifact changed: {rel}"
        committed = subprocess.run(["git", "rev-parse", f"{tag}:{name}"],
                                   cwd=root, check=True, capture_output=True,
                                   text=True).stdout.strip()
        work = subprocess.run(["git", "hash-object", f"--path={name}", name],
                              cwd=root, check=True, capture_output=True,
                              text=True).stdout.strip()
        if committed != work:
            return False, f"V5.4 prior phase tag differs: {name}"
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        return False, f"V5.4 prior phase verification failed: {exc}"
    return True, "frozen phase verifies"


def authorize(project, purpose: str, partition: str, instrument: str,
              start, end, columns, original_v5_stage: str) -> tuple[bool, str]:
    """Called only after the original ledger/stage state itself verifies."""
    if purpose not in PHASES:
        return False, "unknown V5.4 research purpose"
    if original_v5_stage != "VALIDATION_FROZEN":
        return False, "original V5 stage changed from its completed empty-cohort freeze"
    expected_partition, first, last, prior_file, prior_tag = PHASES[purpose]
    if purpose == "V5_4_BLIND_AUDIT_2":
        last = min(project.partitions()["registry"]["historical_audit_2_last_session"].values())
    if (partition != expected_partition or instrument not in ("NQ", "ES")
            or str(start) != first or str(end) != last
            or columns != EXPECTED_COLUMNS):
        return False, f"V5.4 {purpose} may read only full registered {expected_partition} NQ/ES OHLCV"
    ok, reason = ready(project.root)
    if not ok:
        return False, reason
    if prior_file:
        ok, reason = _frozen_file(project.root, prior_file, prior_tag)
        if not ok:
            return False, reason
    if purpose == "V5_4_BLIND_AUDIT_1":
        ok, reason = _frozen_file(project.root, "V5_4_VALIDATION_FREEZE.json",
                                  "v5.4-validation")
        if not ok:
            return False, reason
    if purpose == "V5_4_BLIND_AUDIT_2":
        ok, reason = _frozen_file(project.root, "V5_4_HISTORICAL_AUDIT_MANIFEST.json",
                                  "v5.4-cohort")
        if not ok:
            return False, reason
    return True, purpose+"_ACCESS"
