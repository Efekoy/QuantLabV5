"""Tamper-evident research decision log + autonomous resume state.

  ledgers/RESEARCH_DECISION_LOG.jsonl   hash-chained (same format/verification as the data-access
                                        ledger). Every methodological decision, experiment,
                                        batch, bug, deviation and POST-HOC analysis is recorded.
  provenance/AUTONOMOUS_RESUME_STATE.json  what is complete, what is next, output hashes.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from quantlab5.isolation import ledger
from quantlab5.util.hashing import file_sha256

KINDS = ("DECISION", "EXPERIMENT", "BATCH_DONE", "BATCH_STARTED", "BUG", "DEVIATION", "POST_HOC", "STAGE",
         "FREEZE", "NOTE")


def _git(root: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def log_path(project) -> Path:
    return project.root / "ledgers" / "RESEARCH_DECISION_LOG.jsonl"


def log(project, kind: str, summary: str, **fields) -> dict:
    if kind not in KINDS:
        raise ValueError(f"unknown log kind {kind}")
    try:
        from quantlab5.isolation.stage_gate import current_stage
        stage = current_stage(project)
    except Exception as e:           # noqa: BLE001
        stage = f"UNVERIFIED ({e.__class__.__name__})"
    return ledger.append(log_path(project), kind, ledger.INFO, summary, stage=stage, git_commit=_git(project.root),
                         **fields)


def resume_path(project) -> Path:
    return project.root / "provenance" / "AUTONOMOUS_RESUME_STATE.json"


def load_resume(project) -> dict:
    p = resume_path(project)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"completed": [], "outputs": {}}


def save_resume(project, **updates) -> dict:
    st = load_resume(project)
    st.update(updates)
    st["updated_utc"] = datetime.now(timezone.utc).isoformat()
    st["last_git_commit"] = _git(project.root)
    try:
        from quantlab5.isolation.stage_gate import current_stage
        st["stage"] = current_stage(project)
    except Exception as e:           # noqa: BLE001
        st["stage"] = f"UNVERIFIED ({e})"
    resume_path(project).write_text(json.dumps(st, indent=1, sort_keys=True), encoding="utf-8")
    return st


def mark_done(project, step: str, outputs: dict[str, str] | None = None, next_action: str | None = None) -> dict:
    """Record a completed step and the SHA-256 of its output files (paths relative to the project)."""
    st = load_resume(project)
    done = list(st.get("completed", []))
    if step not in done:
        done.append(step)
    outs = dict(st.get("outputs", {}))
    for rel in outputs or {}:
        p = project.root / rel
        outs[rel] = file_sha256(p) if p.is_file() else "MISSING"
    upd = {"completed": done, "outputs": outs}
    if next_action:
        upd["next_action"] = next_action
    return save_resume(project, **upd)


def verify_outputs(project) -> dict[str, bool]:
    st = load_resume(project)
    return {rel: (project.root / rel).is_file() and file_sha256(project.root / rel) == sha
            for rel, sha in st.get("outputs", {}).items()}
