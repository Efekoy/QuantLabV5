"""V5 bootstrap additions: partition spec, real registry/stage checks (metadata only), prior-lab separation,
earlier-lab data refusal, behavioural-duplicate annotation, resume/checkpoint, NQ/ES synchronisation."""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

from conftest import PROJECT

V5_SPEC = {"DISCOVERY": ("2010-06-08", "2018-12-31"), "VALIDATION": ("2019-01-02", "2022-12-30"),
           "HISTORICAL_AUDIT_1": ("2023-01-03", "2025-12-31"),
           "HISTORICAL_AUDIT_2": ("2026-01-02", "LATEST_COMPLETE_SESSION_AT_BOOTSTRAP")}
V4_VERIFIED = {"NQ": "63b8f16dd1da0a35f2fdfdc9039686ffc8db0ada84333bfc7cd85f8f28d013e7",
               "ES": "4a5dcac73b45f8097164e1242447fb490e6b2d52b4012cbe1ee3890f2d76edb2"}


def _real_partitions() -> dict:
    return json.loads((PROJECT / "config" / "partitions.json").read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------- partition spec

def test_partition_definitions_are_the_v5_specification():
    d = _real_partitions()["definitions"]
    assert {k: (v["first_session"], v["last_session"]) for k, v in d.items() if k in V5_SPEC} == V5_SPEC
    assert d["LIVE_FORWARD"]["first_session"] == "AFTER_FINAL_COHORT_FREEZE"
    assert d["DISCOVERY"]["location"] == "project"
    assert all(d[k]["location"] == "vault" for k in ("VALIDATION", "HISTORICAL_AUDIT_1", "HISTORICAL_AUDIT_2",
                                                     "LIVE_FORWARD"))


def test_stage_policy_only_discovery_is_readable_at_discovery_and_audits_open_after_final_cohort():
    sp = yaml.safe_load((PROJECT / "config" / "stage_policy.yaml").read_text())
    assert sp["readable"]["DISCOVERY"] == ["DISCOVERY"]
    order = sp["stages"]
    for part in ("HISTORICAL_AUDIT_1", "HISTORICAL_AUDIT_2"):
        first = min(order.index(s) for s, r in sp["readable"].items() if part in r)
        assert first > order.index("FINAL_COHORT_FROZEN")
    assert min(order.index(s) for s, r in sp["readable"].items() if "VALIDATION" in r) > order.index("DISCOVERY_FROZEN")
    assert sp["no_candidate_cap"] is True
    for sec in ("prop_selection_rules", "risk_rules", "portfolio_rules"):
        assert sec in sp["required_sections"]["final_cohort"]
    assert "validation_rules" in sp["required_sections"]["discovery"]


def test_vault_is_outside_the_project():
    vault = Path(yaml.safe_load((PROJECT / "config" / "paths.yaml").read_text())["vault"]).resolve()
    assert PROJECT.resolve() not in vault.parents and vault != PROJECT.resolve()


# ----------------------------------------------------------------------------- real registry (metadata only)

REAL = _real_partitions().get("registry")
needs_registry = pytest.mark.skipif(not REAL, reason="bootstrap partitioner has not run yet")


@needs_registry
def test_real_sources_are_the_v4_verified_files():
    assert {k: v["sha256"] for k, v in REAL["sources"].items()} == V4_VERIFIED
    for s in REAL["sources"].values():
        assert s["rows_placed"] + s["excluded_rows"]["unassigned"] == s["rows"]
        assert s["excluded_rows"]["unassigned"] == s["excluded_rows"]["incomplete_final_session"]


@needs_registry
def test_real_partitions_follow_the_spec_and_do_not_overlap():
    recs = REAL["partitions"]
    for inst in ("NQ", "ES"):
        mine = {r["partition"]: r for r in recs if r["instrument"] == inst}
        assert set(mine) == set(V5_SPEC)
        for name, (a, b) in V5_SPEC.items():
            r = mine[name]
            assert r["first_session"] == a and r["first_data_session"] >= a
            if b[0].isdigit():
                assert r["last_session"] == b and r["last_data_session"] <= b
            assert r["rows"] > 0 and r["roll_session_label_mismatches"] == 0
            assert r["location"] == ("project" if name == "DISCOVERY" else "vault")
        ordered = [mine[n] for n in V5_SPEC]
        for x, y in zip(ordered, ordered[1:]):
            assert x["last_timestamp_utc"] < y["first_timestamp_utc"]
        assert sum(r["rows"] for r in ordered) == REAL["sources"][inst]["rows_placed"]


@needs_registry
def test_real_discovery_partition_hash_and_stage_state():
    from quantlab5.isolation import ledger
    from quantlab5.isolation.stage_gate import registry_hash, verified_state
    from quantlab5.project import default_project
    from quantlab5.util.hashing import file_sha256
    p = default_project()
    for r in REAL["partitions"]:
        if r["partition"] == "DISCOVERY":
            assert file_sha256(Path(r["path"])) == r["sha256"]          # in-project file only; vault not opened
    st = verified_state(p)                                             # state hash + ledger cross-check + pins
    assert st["registry_sha256"] == registry_hash(p)
    order = p.stage_policy["stages"]
    assert order.index(st["stage"]) >= order.index("DISCOVERY")
    if st["stage"] == "DISCOVERY":
        allowed = [r for r in ledger.data_reads(p.ledger_path) if r["result"] == "ALLOWED"]
        assert all(r["partition"] == "DISCOVERY" for r in allowed)


# ----------------------------------------------------------------------------- prior labs

def test_prior_labs_manifest_verifies_and_holds_no_importable_code():
    man = json.loads((PROJECT / "provenance" / "PRIOR_LABS_MANIFEST.json").read_text())
    n = 0
    for lab in man["labs"].values():
        for r in lab["files"]:
            if "destination" not in r:
                continue
            p = PROJECT / r["destination"]
            assert hashlib.sha256(p.read_bytes()).hexdigest() == r["destination_sha256"], r["destination"]
            raw = gzip.decompress(p.read_bytes()) if r.get("gzipped") else p.read_bytes()
            assert hashlib.sha256(raw).hexdigest() == r["source_sha256"], r["destination"]
            n += 1
    assert n > 50
    assert not list((PROJECT / "docs" / "prior_labs").rglob("*.py"))
    assert not list((PROJECT / "docs" / "prior_labs").rglob("*.parquet"))


def test_load_view_refuses_files_in_an_earlier_labs_data_store(fresh_project, monkeypatch):
    import quantlab5.isolation.load_view as lv
    p = fresh_project
    cfg = p.config_path("paths.yaml")
    doc = yaml.safe_load(cfg.read_text())
    doc["prior_lab_data"] = [str(p.discovery_dir)]           # pretend DISCOVERY sits in an earlier lab's store
    cfg.write_text(yaml.safe_dump(doc))
    monkeypatch.setattr(lv, "authorize", lambda project, partition: ("DISCOVERY", True, "test bypass"))
    with pytest.raises(lv.AccessRefused, match="earlier lab"):
        lv.load_view("NQ", "DISCOVERY", project=p)


# ----------------------------------------------------------------------------- behavioural duplicates

def test_behavioural_clustering_only_annotates_duplicates():
    from quantlab5.search.clustering import correlation_clusters, duplicate_annotations
    rng = np.random.default_rng(0)
    base = rng.standard_normal(500)
    streams = {"a": base, "b": base + 1e-3 * rng.standard_normal(500), "c": rng.standard_normal(500),
               "d": base * 2.0}
    cl = correlation_clusters(streams, 0.9)
    dup = duplicate_annotations(cl)
    assert dup == {"b": "a", "d": "a"}
    members = {m for ms in cl.values() for m in ms}
    assert members == set(streams)                            # nobody is removed


# ----------------------------------------------------------------------------- resume / checkpoint

def test_world_runner_resumes_only_from_verified_outputs(tmp_path):
    sys.path.insert(0, str(PROJECT / "research"))
    try:
        import run_worlds as RW
    finally:
        sys.path.remove(str(PROJECT / "research"))
    body = {"global_max_t": 1.5, "families": {"RET": {"n_pass": 0}}}
    good = dict(body, summary_sha256=hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest())
    f = tmp_path / "w.json"
    assert not RW._ok(f)                                       # missing -> recompute
    f.write_text(json.dumps(good))
    assert RW._ok(f)                                           # verified -> skipped on resume
    f.write_text(json.dumps(dict(good, global_max_t=9.9)))
    assert not RW._ok(f)                                       # tampered -> recomputed
    f.write_text("{truncated")
    assert not RW._ok(f)                                       # interrupted write -> recomputed


def test_resume_state_tracks_steps_and_output_hashes(fresh_project):
    from quantlab5 import research_log as RL
    p = fresh_project
    (p.root / "results").mkdir(exist_ok=True)
    (p.root / "results" / "a.json").write_text("{}")
    RL.mark_done(p, "step_a", {"results/a.json": ""}, next_action="step_b")
    RL.mark_done(p, "step_a", {"results/a.json": ""})         # idempotent
    st = RL.load_resume(p)
    assert st["completed"] == ["step_a"] and st["next_action"] == "step_b" and st["stage"] == "DISCOVERY"
    (p.root / "results" / "a.json").write_text('{"x": 1}')
    assert RL.verify_outputs(p) == {"results/a.json": False}


# ----------------------------------------------------------------------------- NQ/ES synchronisation

def test_nq_es_market_is_synchronised_minute_by_minute(shared_project):
    from quantlab5.data.market import load_market
    m = load_market("DISCOVERY", "2020-09-01", "2020-09-10", project=shared_project, purpose="sync test")
    assert m.nq.n > 0 and m.es.n > 0
    ok = np.asarray(m.evalid)
    pos = np.searchsorted(m.es.ts, m.nq.ts)
    pos = np.minimum(pos, m.es.n - 1)
    same = np.asarray(m.es.ts)[pos] == np.asarray(m.nq.ts)
    assert np.array_equal(ok, same)                            # valid exactly where ES has the same minute
    assert np.array_equal(np.asarray(m.ec)[ok], np.asarray(m.es.c)[pos[ok]])
    assert np.isnan(np.asarray(m.ec)[~ok]).all()               # never forward-filled
    assert np.array_equal(np.unique(m.nq.sday), np.unique(m.es.sday))
