"""Stage machine: strictly monotonic, freeze prerequisites, stage-dependent access.
(Ported from QuantLabV4 tests/test_stage_gate.py with V5 stage/partition names; V5 additions at the end:
required freeze sections, the NO-CANDIDATE-CAP rule, and the second historical audit.)"""
import json
import os
import stat

import pytest

from quantlab5.isolation import ledger
from quantlab5.isolation.freezes import create_freeze
from quantlab5.isolation.load_view import AccessRefused, load_view
from quantlab5.isolation.stage_gate import StageViolation, advance, current_stage, stages

DISC = {"candidates": ["Q5-aaaa", "Q5-bbbb"], "qualifying": ["Q5-aaaa", "Q5-bbbb"],
        "validation_rules": {"t_min": 1.5}, "selection_process": "synthetic test selection"}
VAL = {"evaluated": ["Q5-aaaa", "Q5-bbbb"], "survivors": ["Q5-aaaa"], "validation_rules_sha256": "0" * 64}
COHORT = {"cohort": ["Q5-aaaa"], "parameters": {"Q5-aaaa": {"n": 5}}, "sizing_rules": {"kind": "fixed_dollar",
          "risk_usd": 300}, "prop_selection_rules": {"rule": "synthetic"}, "risk_rules": {"max_open_risk": 600},
          "portfolio_rules": {"weights": "equal"}, "selection_process": "synthetic test selection"}


def _to(p, target):
    """Walk forward to `target`, creating the required freezes on the way (synthetic test content)."""
    order = stages(p)
    while current_stage(p) != target:
        nxt = order[order.index(current_stage(p)) + 1]
        if nxt == "DISCOVERY_FROZEN":
            create_freeze(p, "discovery", DISC)
        elif nxt == "VALIDATION_FROZEN":
            create_freeze(p, "validation", VAL)
        elif nxt == "FINAL_COHORT_FROZEN":
            create_freeze(p, "final_cohort", COHORT)
        elif nxt == "HISTORICAL_AUDIT_2":
            create_freeze(p, "audit_1_report", {"report": "synthetic audit-1 report", "sealed": True})
        elif nxt == "LIVE_FORWARD":
            create_freeze(p, "audit_2_report", {"report": "synthetic audit-2 report", "sealed": True})
        advance(p, nxt)


def test_stage_list_is_the_specified_order(shared_project):
    assert stages(shared_project) == ["BOOTSTRAP", "DISCOVERY", "DISCOVERY_FROZEN", "VALIDATION",
                                      "VALIDATION_FROZEN", "FINAL_COHORT_FROZEN", "HISTORICAL_AUDIT_1",
                                      "HISTORICAL_AUDIT_2", "LIVE_FORWARD"]


def test_cannot_skip_or_move_backwards(fresh_project):
    p = fresh_project
    for bad in ("VALIDATION", "HISTORICAL_AUDIT_1", "LIVE_FORWARD", "BOOTSTRAP", "DISCOVERY", "NOPE"):
        with pytest.raises(StageViolation):
            advance(p, bad)
    assert current_stage(p) == "DISCOVERY"
    refused = [r for r in ledger.read(p.ledger_path) if r["event"] == "STAGE_TRANSITION"]
    assert refused and all(r["result"] == "REFUSED" for r in refused)


def test_discovery_frozen_requires_a_verified_discovery_freeze(fresh_project):
    p = fresh_project
    with pytest.raises(StageViolation, match="DISCOVERY_FREEZE"):
        advance(p, "DISCOVERY_FROZEN")
    create_freeze(p, "discovery", dict(DISC, candidates=["Q5-x"], qualifying=["Q5-x"]))
    advance(p, "DISCOVERY_FROZEN")
    assert current_stage(p) == "DISCOVERY_FROZEN"
    with pytest.raises(AccessRefused):
        load_view("NQ", "VALIDATION", project=p)       # still DISCOVERY-only


def test_validation_stage_reads_validation_but_never_either_historical_audit(fresh_project):
    p = fresh_project
    _to(p, "VALIDATION")
    md = load_view("NQ", "VALIDATION", project=p)
    assert len(md.frame) > 0
    load_view("ES", "DISCOVERY", "2020-09-01", "2020-09-02", project=p)
    for part in ("HISTORICAL_AUDIT_1", "HISTORICAL_AUDIT_2", "LIVE_FORWARD"):
        with pytest.raises(AccessRefused):
            load_view("NQ", part, project=p)


def test_final_cohort_freeze_needs_all_required_sections(fresh_project):
    p = fresh_project
    _to(p, "VALIDATION_FROZEN")
    bad = dict(COHORT)
    bad["sizing_rules"] = {}
    with pytest.raises(StageViolation, match="sizing_rules"):
        create_freeze(p, "final_cohort", bad)
    with pytest.raises(StageViolation):
        advance(p, "FINAL_COHORT_FROZEN")
    with pytest.raises(AccessRefused):
        load_view("NQ", "HISTORICAL_AUDIT_1", project=p)


def test_audit_1_opens_only_after_final_cohort_freeze_and_freeze_is_then_immutable(fresh_project):
    p = fresh_project
    _to(p, "FINAL_COHORT_FROZEN")
    with pytest.raises(AccessRefused):
        load_view("NQ", "HISTORICAL_AUDIT_1", project=p)
    advance(p, "HISTORICAL_AUDIT_1")
    assert len(load_view("NQ", "HISTORICAL_AUDIT_1", project=p).frame) > 0
    with pytest.raises(AccessRefused):
        load_view("NQ", "HISTORICAL_AUDIT_2", project=p)
    # tamper with the pinned final cohort -> every read (even DISCOVERY) now refused
    f = p.freeze_path("final_cohort")
    os.chmod(f, stat.S_IWRITE | stat.S_IREAD)
    doc = json.loads(f.read_text())
    doc["sections"]["cohort"].append("Q5-sneaky")
    f.write_text(json.dumps(doc))
    with pytest.raises(AccessRefused):
        load_view("NQ", "DISCOVERY", project=p)


def test_full_walk_to_live_forward_records_freeze_time(fresh_project):
    p = fresh_project
    _to(p, "LIVE_FORWARD")
    st = json.loads(p.stage_state_path.read_text())
    assert st["final_cohort_freeze_utc"]
    assert [h["stage"] for h in st["history"]] == stages(p)
    load_view("NQ", "HISTORICAL_AUDIT_2", project=p)
    with pytest.raises(StageViolation):
        advance(p, "HISTORICAL_AUDIT_2")                          # never backwards, even at the end
    ok, msg = ledger.verify(p.ledger_path)
    assert ok, msg


def test_discovery_freeze_edit_after_pinning_blocks_reads(fresh_project):
    p = fresh_project
    create_freeze(p, "discovery", dict(DISC, candidates=["Q5-x"], qualifying=["Q5-x"]))
    advance(p, "DISCOVERY_FROZEN")
    f = p.freeze_path("discovery")
    os.chmod(f, stat.S_IWRITE | stat.S_IREAD)
    f.write_text(f.read_text().replace("Q5-x", "Q5-y"))
    with pytest.raises(AccessRefused):
        load_view("NQ", "DISCOVERY", project=p)


def test_freezes_are_written_once(fresh_project):
    from quantlab5.isolation.manifests import ManifestError
    p = fresh_project
    create_freeze(p, "discovery", dict(DISC, candidates=["Q5-x"], qualifying=["Q5-x"]))
    with pytest.raises(ManifestError):
        create_freeze(p, "discovery", dict(DISC, candidates=["Q5-y"], qualifying=["Q5-y"]))


def test_state_cannot_be_reinitialised(fresh_project):
    from quantlab5.isolation.stage_gate import init_state
    with pytest.raises(StageViolation):
        init_state(fresh_project)


def test_audit_2_cannot_open_before_the_audit_1_report_is_frozen(fresh_project):
    p = fresh_project
    _to(p, "HISTORICAL_AUDIT_1")
    with pytest.raises(StageViolation, match="AUDIT_1_REPORT_FREEZE"):
        advance(p, "HISTORICAL_AUDIT_2")
    with pytest.raises(AccessRefused):
        load_view("NQ", "HISTORICAL_AUDIT_2", project=p)
    create_freeze(p, "audit_1_report", {"report": "x"})
    advance(p, "HISTORICAL_AUDIT_2")
    assert len(load_view("NQ", "HISTORICAL_AUDIT_2", project=p).frame) > 0


def test_state_file_without_newer_freeze_keys_still_advances(fresh_project):
    """(V4 regression, kept) a state file lacking a newer freeze key must still advance."""
    from quantlab5.isolation.stage_gate import _state_hash
    p = fresh_project
    st = json.loads(p.stage_state_path.read_text())
    del st["freezes"]["audit_2_report"]
    st["state_hash"] = _state_hash(st)
    p.stage_state_path.write_text(json.dumps(st))
    _to(p, "LIVE_FORWARD")
    assert current_stage(p) == "LIVE_FORWARD"


# ----------------------------------------------------------------------------- V5 additions

def test_live_forward_cannot_open_before_the_audit_2_report_is_frozen(fresh_project):
    p = fresh_project
    _to(p, "HISTORICAL_AUDIT_2")
    with pytest.raises(StageViolation, match="AUDIT_2_REPORT_FREEZE"):
        advance(p, "LIVE_FORWARD")
    with pytest.raises(AccessRefused):
        load_view("NQ", "LIVE_FORWARD", project=p)


@pytest.mark.parametrize("stage", ["DISCOVERY", "DISCOVERY_FROZEN", "VALIDATION", "VALIDATION_FROZEN",
                                   "FINAL_COHORT_FROZEN"])
def test_historical_audits_are_sealed_until_the_final_cohort_is_frozen_and_entered(fresh_project, stage):
    p = fresh_project
    _to(p, stage)
    for part in ("HISTORICAL_AUDIT_1", "HISTORICAL_AUDIT_2", "LIVE_FORWARD"):
        with pytest.raises(AccessRefused):
            load_view("NQ", part, project=p)
    if stage in ("DISCOVERY", "DISCOVERY_FROZEN"):
        with pytest.raises(AccessRefused):
            load_view("NQ", "VALIDATION", project=p)


def test_discovery_freeze_requires_validation_rules(fresh_project):
    p = fresh_project
    with pytest.raises(StageViolation, match="validation_rules"):
        create_freeze(p, "discovery", dict(DISC, validation_rules={}))
    with pytest.raises(StageViolation, match="qualifying"):
        create_freeze(p, "discovery", {k: v for k, v in DISC.items() if k != "qualifying"})
    assert not p.freeze_path("discovery").exists()


def test_no_cap_discovery_every_qualifying_candidate_advances(fresh_project):
    p = fresh_project
    qual = [f"Q5-{i:04x}" for i in range(70)]
    with pytest.raises(StageViolation, match="NO-CAP"):          # an arbitrary top-5 cut is refused
        create_freeze(p, "discovery", dict(DISC, qualifying=qual, candidates=qual[:5]))
    assert not p.freeze_path("discovery").exists()
    create_freeze(p, "discovery", dict(DISC, qualifying=qual, candidates=qual,
                                       duplicate_of={q: qual[0] for q in qual[1:10]}))   # duplicates annotated only
    advance(p, "DISCOVERY_FROZEN")


def test_no_cap_duplicates_are_annotations_of_advanced_candidates(fresh_project):
    p = fresh_project
    with pytest.raises(StageViolation, match="duplicate_of"):
        create_freeze(p, "discovery", dict(DISC, duplicate_of={"Q5-notadvanced": "Q5-aaaa"}))


def test_no_cap_validation_must_evaluate_every_frozen_candidate(fresh_project):
    p = fresh_project
    _to(p, "VALIDATION")
    with pytest.raises(StageViolation, match="NO-CAP"):
        create_freeze(p, "validation", dict(VAL, evaluated=["Q5-aaaa"]))
    with pytest.raises(StageViolation, match="NO-CAP"):
        create_freeze(p, "validation", dict(VAL, survivors=["Q5-zzzz"]))


@pytest.mark.parametrize("n", [7, 70])
def test_no_cap_final_cohort_is_exactly_all_validation_survivors(fresh_project, n):
    p = fresh_project
    many = [f"Q5-{i:04x}" for i in range(n + 3)]
    surv = many[:n]
    create_freeze(p, "discovery", dict(DISC, candidates=many, qualifying=many))
    advance(p, "DISCOVERY_FROZEN")
    advance(p, "VALIDATION")
    create_freeze(p, "validation", dict(VAL, evaluated=many, survivors=surv))
    advance(p, "VALIDATION_FROZEN")
    for cut in (surv[:5], surv + ["Q5-extra"], many):
        with pytest.raises(StageViolation, match="NO-CAP"):
            create_freeze(p, "final_cohort", dict(COHORT, cohort=cut))
    create_freeze(p, "final_cohort", dict(COHORT, cohort=surv, parameters={s: {"n": 1} for s in surv}))
    advance(p, "FINAL_COHORT_FROZEN")
    advance(p, "HISTORICAL_AUDIT_1")
    assert len(load_view("NQ", "HISTORICAL_AUDIT_1", project=p).frame) > 0


def test_zero_survivors_is_recordable_but_cannot_open_the_audits(fresh_project):
    p = fresh_project
    _to(p, "VALIDATION")
    create_freeze(p, "validation", dict(VAL, survivors=[]))       # an honest "nothing survived"
    advance(p, "VALIDATION_FROZEN")
    with pytest.raises(StageViolation):
        create_freeze(p, "final_cohort", dict(COHORT, cohort=[]))
    with pytest.raises(StageViolation):
        advance(p, "FINAL_COHORT_FROZEN")


def test_no_cap_is_rechecked_on_every_read(fresh_project):
    """A pinned freeze re-signed after a cut (valid body hash) is refused on the next read."""
    from quantlab5.isolation.manifests import body_hash
    p = fresh_project
    _to(p, "DISCOVERY_FROZEN")
    f = p.freeze_path("discovery")
    os.chmod(f, stat.S_IWRITE | stat.S_IREAD)
    doc = json.loads(f.read_text())
    doc["sections"]["candidates"] = doc["sections"]["candidates"][:1]
    doc["body_sha256"] = body_hash(doc)
    f.write_text(json.dumps(doc))
    with pytest.raises(AccessRefused):
        load_view("NQ", "DISCOVERY", project=p)


def test_final_cohort_freeze_requires_prop_risk_and_portfolio_rules(fresh_project):
    p = fresh_project
    _to(p, "VALIDATION_FROZEN")
    for sec in ("prop_selection_rules", "risk_rules", "portfolio_rules"):
        with pytest.raises(StageViolation, match=sec):
            create_freeze(p, "final_cohort", dict(COHORT, **{sec: {}}))
