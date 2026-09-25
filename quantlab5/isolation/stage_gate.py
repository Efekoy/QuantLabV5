"""The V5 research stage machine.

(Ported from QuantLabV4 quantlab4/isolation/stage_gate.py, itself adapted from quantlab3. Kept unchanged:
one-way state machine, freeze hashes pinned at transition time and re-verified before every read,
refusals are ledgered, the partition-registry hash is pinned when DISCOVERY opens, the stage-state
file is itself hashed AND cross-checked against the STAGE_ENTERED records in the hash-chained ledger,
so editing STAGE_STATE.json alone cannot move the stage.
Changed for V5: the V5 stages/partitions (config/stage_policy.yaml); five freeze kinds; required
sections for every freeze kind (not only the final cohort); and the V5 NO-CANDIDATE-CAP rule, checked
on freeze contents (`check_no_cap`): everything that qualifies in DISCOVERY advances, every frozen
candidate is evaluated in VALIDATION, and the final cohort is exactly the set of validation survivors.)

    BOOTSTRAP -> DISCOVERY -> DISCOVERY_FROZEN -> VALIDATION -> VALIDATION_FROZEN
      -> FINAL_COHORT_FROZEN -> HISTORICAL_AUDIT_1 -> HISTORICAL_AUDIT_2 -> LIVE_FORWARD

FINAL_COHORT_FROZEN records the freeze timestamp that starts LIVE_FORWARD.

This is the SOFTWARE layer. The HARD layer is the operating system: sealed
partitions live in a vault outside the project that a non-administrator research
account cannot open (tools/harden_isolation.ps1). Software checks alone do not
stop code running as an administrator from opening vault files directly.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from quantlab5.isolation import ledger
from quantlab5.isolation.manifests import ManifestError, verify_manifest
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text


class StageViolation(Exception):
    """A read or a transition that the stage gate forbids."""


FREEZE_KINDS = {"discovery": "DISCOVERY_FREEZE", "validation": "VALIDATION_FREEZE",
                "final_cohort": "FINAL_COHORT_FREEZE", "audit_1_report": "AUDIT_1_REPORT_FREEZE",
                "audit_2_report": "AUDIT_2_REPORT_FREEZE"}
_CHECK_TO_FREEZE = {f"{k}_freeze_verified": k for k in FREEZE_KINDS}


def stages(project) -> list[str]:
    return list(project.stage_policy["stages"])


def readable(project, stage: str) -> tuple[str, ...]:
    return tuple(project.stage_policy["readable"][stage])


def registry_hash(project) -> str:
    reg = project.partitions().get("registry")
    if not reg:
        raise StageViolation("partition registry is empty: the bootstrap partitioner has not run")
    return sha256_text(canonical_json(reg))


# --------------------------------------------------------------------------- state file

def _state_hash(st: dict) -> str:
    return sha256_text(canonical_json({k: v for k, v in st.items() if k != "state_hash"}))


def _write_state(project, st: dict) -> None:
    st["state_hash"] = _state_hash(st)
    p = project.stage_state_path
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=1), encoding="utf-8")
    tmp.replace(p)


def _read_state(project) -> dict:
    p = project.stage_state_path
    if not p.exists():
        raise StageViolation(f"no stage state at {p}; run research/s00_bootstrap.py")
    st = json.loads(p.read_text(encoding="utf-8"))
    if _state_hash(st) != st.get("state_hash"):
        raise StageViolation("STAGE_STATE.json fails its own hash: it was edited by hand")
    if st.get("stage") not in stages(project):
        raise StageViolation(f"invalid stage {st.get('stage')!r}")
    return st


def _ledger_stage_history(project) -> list[str]:
    ok, msg = ledger.verify(project.ledger_path)
    if not ok:
        raise StageViolation(f"data-access ledger failed verification: {msg}")
    return [r["stage"] for r in ledger.read(project.ledger_path) if r.get("event") == "STAGE_ENTERED"]


def _cross_check(project, st: dict) -> None:
    hist = _ledger_stage_history(project)
    order = stages(project)
    if not hist:
        raise StageViolation("the ledger records no stage entry")
    idx = [order.index(s) for s in hist]
    if idx != list(range(len(idx))):
        raise StageViolation(f"ledger stage history is not a single forward walk: {hist}")
    if hist[-1] != st["stage"]:
        raise StageViolation(f"STAGE_STATE.json says {st['stage']} but the ledger says {hist[-1]}")
    if [h["stage"] for h in st.get("history", [])] != hist:
        raise StageViolation("STAGE_STATE.json history disagrees with the ledger")


def init_state(project) -> dict:
    p = project.stage_state_path
    if p.exists():
        raise StageViolation(f"{p} already exists; the stage state is never re-initialised")
    p.parent.mkdir(parents=True, exist_ok=True)
    if project.ledger_path.exists() and ledger.read(project.ledger_path):
        raise StageViolation("a ledger already exists without a stage state; refusing to re-initialise")
    ledger.append(project.ledger_path, "LEDGER_CREATED", ledger.INFO, "QuantLabV5 ledger genesis")
    st = {"stage": "BOOTSTRAP", "registry_sha256": None,
          "freezes": {k: None for k in FREEZE_KINDS}, "final_cohort_freeze_utc": None,
          "history": [{"stage": "BOOTSTRAP", "entered_utc": datetime.now(timezone.utc).isoformat()}]}
    ledger.append(project.ledger_path, "STAGE_ENTERED", ledger.INFO, "initial stage", stage="BOOTSTRAP")
    _write_state(project, st)
    return st


# --------------------------------------------------------------------------- verification

def required_sections(project, kind: str) -> list[str]:
    return list((project.stage_policy.get("required_sections") or {}).get(kind, []))


def _ids(x) -> set:
    if isinstance(x, dict):
        return set(x)
    if isinstance(x, (list, tuple)):
        return set(x)
    raise StageViolation(f"a candidate list must be a list or a dict keyed by candidate ID, got {type(x).__name__}")


def check_no_cap(project, kind: str, sections: dict) -> None:
    """V5 NO-CANDIDATE-CAP rule on freeze contents. Raises StageViolation if anything qualifying was dropped.

    discovery:    qualifying <= candidates  (duplicates may be annotated in `duplicate_of`, never removed)
    validation:   evaluated == frozen discovery candidates; survivors <= evaluated
    final_cohort: cohort == frozen validation survivors
    """
    for key in (project.stage_policy.get("required_candidate_lists") or {}).get(kind, []):
        if key not in sections:
            raise StageViolation(f"{FREEZE_KINDS[kind]} lacks the candidate list {key!r} (it may be empty, not absent)")
        _ids(sections[key])
    if not project.stage_policy.get("no_candidate_cap", False):
        return
    from quantlab5.isolation.manifests import read_manifest
    if kind == "discovery":
        cands, qual = _ids(sections["candidates"]), _ids(sections["qualifying"])
        dropped = sorted(qual - cands)
        if dropped:
            raise StageViolation(f"NO-CAP rule: {len(dropped)} qualifying discovery candidates are not advanced "
                                 f"(e.g. {dropped[:3]})")
        dup = sections.get("duplicate_of") or {}
        if not isinstance(dup, dict) or not set(dup) <= cands:
            raise StageViolation("NO-CAP rule: `duplicate_of` must map advanced candidates to their representative")
    elif kind == "validation":
        disc = _ids(read_manifest(project.freeze_path("discovery"))["sections"]["candidates"])
        ev, surv = _ids(sections["evaluated"]), _ids(sections["survivors"])
        if ev != disc:
            raise StageViolation(f"NO-CAP rule: VALIDATION must evaluate exactly the {len(disc)} frozen discovery "
                                 f"candidates ({len(disc - ev)} missing, {len(ev - disc)} not frozen)")
        if not surv <= ev:
            raise StageViolation("NO-CAP rule: validation survivors must be evaluated candidates")
    elif kind == "final_cohort":
        surv = _ids(read_manifest(project.freeze_path("validation"))["sections"]["survivors"])
        cohort = _ids(sections["cohort"])
        if cohort != surv:
            raise StageViolation(f"NO-CAP rule: the final cohort must be exactly the {len(surv)} validation survivors "
                                 f"({len(surv - cohort)} survivors left out, {len(cohort - surv)} non-survivors added)")


def _verify_freeze(project, kind: str) -> str:
    try:
        sha = verify_manifest(project.freeze_path(kind), project.root, FREEZE_KINDS[kind],
                              required_sections(project, kind))
    except ManifestError as e:
        raise StageViolation(f"{FREEZE_KINDS[kind]} does not verify: {e}") from e
    from quantlab5.isolation.manifests import read_manifest
    check_no_cap(project, kind, read_manifest(project.freeze_path(kind))["sections"])
    return sha


def verify_registry_files(project) -> dict[str, str]:
    """Hash EVERY registered partition file (privileged: needs vault access). Used entering DISCOVERY."""
    from pathlib import Path
    out = {}
    for rec in project.partitions()["registry"]["partitions"]:
        p = Path(rec["path"])
        if not p.is_file():
            raise StageViolation(f"registered partition {rec['instrument']}/{rec['partition']} is missing")
        if file_sha256(p) != rec["sha256"]:
            raise StageViolation(f"registered partition {rec['instrument']}/{rec['partition']} hash mismatch")
        out[f"{rec['instrument']}/{rec['partition']}"] = rec["sha256"]
    return out


def verified_state(project) -> dict:
    """Read the stage state and re-verify everything it depends on. Called before EVERY read."""
    st = _read_state(project)
    _cross_check(project, st)
    if st["stage"] != "BOOTSTRAP":
        if st.get("registry_sha256") != registry_hash(project):
            raise StageViolation("config/partitions.json registry changed after it was pinned")
    for kind, pinned in st["freezes"].items():
        if pinned is not None and _verify_freeze(project, kind) != pinned:
            raise StageViolation(f"{FREEZE_KINDS[kind]} changed after it was pinned; frozen content is immutable")
    return st


def current_stage(project) -> str:
    return verified_state(project)["stage"]


def authorize(project, partition: str) -> tuple[str, bool, str]:
    """(stage, allowed, reason). Raises StageViolation only if the state itself is invalid."""
    stage = current_stage(project)
    if partition not in readable(project, stage):
        return stage, False, (f"stage {stage} may not read {partition}; readable now: "
                              f"{', '.join(readable(project, stage)) or 'nothing'}")
    return stage, True, "authorised by stage policy"


# --------------------------------------------------------------------------- transitions

def advance(project, target: str) -> dict:
    """Move exactly one stage forward after that stage's preconditions verify."""
    st = verified_state(project)
    order = stages(project)
    cur = st["stage"]
    if target not in order:
        raise StageViolation(f"unknown stage {target!r}")
    if order.index(target) != order.index(cur) + 1:
        nxt = order[order.index(cur) + 1] if cur != order[-1] else "(none)"
        ledger.append(project.ledger_path, "STAGE_TRANSITION", ledger.REFUSED,
                      f"cannot move {cur} -> {target}; only {nxt} is allowed", stage=cur, target=target)
        raise StageViolation(f"cannot move {cur} -> {target}. The only allowed next stage is {nxt}.")
    try:
        for check in project.stage_policy["preconditions"].get(target, []):
            if check == "partition_registry_verified":
                verify_registry_files(project)
                st["registry_sha256"] = registry_hash(project)
            elif check in _CHECK_TO_FREEZE:
                kind = _CHECK_TO_FREEZE[check]
                sha = _verify_freeze(project, kind)
                if st["freezes"].get(kind) is None:
                    st["freezes"][kind] = sha
                    if kind == "final_cohort":
                        from quantlab5.isolation.manifests import read_manifest
                        st["final_cohort_freeze_utc"] = read_manifest(project.freeze_path(kind))["created_utc"]
                elif st["freezes"].get(kind) != sha:
                    raise StageViolation(f"{FREEZE_KINDS[kind]} changed after it was pinned")
            else:
                raise StageViolation(f"unknown precondition {check!r}")
    except StageViolation as e:
        ledger.append(project.ledger_path, "STAGE_TRANSITION", ledger.REFUSED, str(e), stage=cur, target=target)
        raise
    st["stage"] = target
    st["history"].append({"stage": target, "entered_utc": datetime.now(timezone.utc).isoformat()})
    ledger.append(project.ledger_path, "STAGE_ENTERED", ledger.INFO, f"{cur} -> {target}", stage=target,
                  registry_sha256=st["registry_sha256"], freezes=st["freezes"],
                  final_cohort_freeze_utc=st["final_cohort_freeze_utc"])
    _write_state(project, st)
    return st
