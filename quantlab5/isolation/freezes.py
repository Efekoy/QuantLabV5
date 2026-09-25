"""Create stage freezes (DISCOVERY / VALIDATION / FINAL_COHORT / AUDIT_1_REPORT / AUDIT_2_REPORT) as
tamper-evident manifests. (Ported from QuantLabV4; V5: required sections for every kind and the
NO-CANDIDATE-CAP content check run BEFORE anything is written.)

A freeze pins: its content sections (e.g. the final cohort, parameters, sizing rules
and selection process), the hashes of any files it names, the ledger head (so later
truncation is detectable), and the git commit. The stage gate pins the freeze's
body hash when the corresponding stage is entered and re-verifies it before every
read. FINAL_COHORT_FREEZE's `created_utc` becomes the LIVE_FORWARD start time.
"""
from __future__ import annotations

import subprocess

from quantlab5.isolation import ledger
from quantlab5.isolation.manifests import build_manifest, write_manifest
from quantlab5.isolation.stage_gate import (FREEZE_KINDS, StageViolation, check_no_cap, required_sections,
                                           verified_state)


def git_commit(root) -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def create_freeze(project, kind: str, sections: dict, files=()) -> str:
    if kind not in FREEZE_KINDS:
        raise ValueError(f"unknown freeze kind {kind}")
    verified_state(project)          # refuses if state/ledger/registry/earlier freezes are invalid
    missing = [s for s in required_sections(project, kind) if sections.get(s) in (None, "", [], {})]
    if missing:
        raise StageViolation(f"{FREEZE_KINDS[kind]} lacks required sections {missing}")
    check_no_cap(project, kind, sections)
    doc = build_manifest(FREEZE_KINDS[kind], sections, project.root, files,
                         ledger_anchor=ledger.head(project.ledger_path), git_commit=git_commit(project.root))
    sha = write_manifest(project.freeze_path(kind), doc)
    ledger.append(project.ledger_path, "FREEZE_CREATED", ledger.INFO, FREEZE_KINDS[kind], freeze_sha256=sha,
                  created_utc=doc["created_utc"])
    return sha
