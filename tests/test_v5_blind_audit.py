"""Evaluation-only audit keeps every frozen exact candidate."""
import numpy as np
from types import SimpleNamespace
import json

from quantlab5.search.candidate_id import candidate_id
from quantlab5.v5.inference import FixedFamilyResult
from quantlab5.v5.market_search import CandidateRecord


def _record(spec, daily):
    cid = candidate_id(spec)
    return CandidateRecord(cid, spec["stage"], spec["family"], spec["side"],
                           spec, 1., np.asarray(daily, float),
                           np.ones(len(daily), int), 100, 2, 10., 1., cid,
                           np.array([], int), np.array([], int),
                           net_r=float(np.sum(daily)),
                           expectancy_r=float(np.mean(daily)))


def test_blind_audit_evaluates_same_exact_ids_without_search(monkeypatch):
    import quantlab5.v5.audit as audit
    specs = [dict(grammar="test", stage="A", family="E01", side="long", variant=i)
             for i in (1, 2)]
    records = {candidate_id(s): _record(s, np.ones(100) if s["variant"] == 1
                                          else -np.ones(100)) for s in specs}
    monkeypatch.setattr(audit, "SignalContext", lambda market: type("C", (), {"stop": None})())
    monkeypatch.setattr(audit, "_shadow_clock_baseline", lambda *args: None)
    monkeypatch.setattr(audit, "evaluate_spec", lambda market, spec, context, costs,
                        shadow_baseline: records[candidate_id(spec)])
    monkeypatch.setattr(audit, "signal_for_spec", lambda *args: (None, None, None))
    monkeypatch.setattr(audit, "evaluate_mnq_budgets", lambda *args, **kwargs: {})
    monkeypatch.setattr(audit, "fixed_family_inference", lambda streams, **kw:
                        FixedFamilyResult(np.where(streams.mean(axis=0) > 0, 20., -20.), .002,
                                          np.where(streams.mean(axis=0) > 0, .002, 1.),
                                          np.zeros(kw["reps"])))
    costs = type("Costs", (), {"per_trade_points": lambda self, *args: 1.})()
    result = audit.evaluate_exact_cohort(SimpleNamespace(nq=None),
                                         {candidate_id(s): s for s in specs},
                                         costs, seed=615005)
    assert set(result["candidate_ids"]) == set(records)
    assert {r["classification"] for r in result["rows"].values()} == {"SUPPORTED", "REJECTED"}
    assert all(result["rows"][cid]["trades"] == 100 for cid in records)
    assert all("mnq_budget_coverage" in result["rows"][cid] for cid in records)


def test_audit_runner_reveals_only_after_both_same_cohort_results(tmp_path, monkeypatch):
    import research.run_v5_blind_audits as runner
    cid = candidate_id({"family": "E01", "stage": "A", "side": "long"})
    manifest = tmp_path / "V5_HISTORICAL_AUDIT_MANIFEST.json"
    manifest.write_text(json.dumps({"sections": {"cohort": [cid],
                                                  "specs": {cid: {"family": "E01"}},
                                                  "rules": {"same_cohort_both": True}}}))
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "AUDIT_MANIFEST", manifest)
    monkeypatch.setattr(runner, "HIDDEN", tmp_path / "reports/.blind")
    monkeypatch.setattr(runner, "A1", tmp_path / "reports/.blind/V5_AUDIT_1_RESULT.json")
    monkeypatch.setattr(runner, "A2", tmp_path / "reports/.blind/V5_AUDIT_2_RESULT.json")
    monkeypatch.setattr(runner, "BOTH", tmp_path / "BOTH_HISTORICAL_AUDITS_COMPLETE.json")
    monkeypatch.setattr(runner, "verify_manifest", lambda *args, **kwargs: True)
    monkeypatch.setattr(runner, "build_manifest", lambda kind, sections, *args, **kwargs:
                        {"kind": kind, "sections": sections})
    monkeypatch.setattr(runner, "write_manifest", lambda path, doc:
                        path.write_text(json.dumps(doc)))
    project = SimpleNamespace(freeze_path=lambda kind: tmp_path / (kind+".json"),
                              partitions=lambda: {"registry": {
                                  "historical_audit_2_last_session": {
                                      "NQ": "2026-08-10", "ES": "2026-08-14"}}})
    monkeypatch.setattr(runner, "default_project", lambda: project)
    monkeypatch.setattr(runner.CostModel, "from_project", lambda project: object())
    stage = ["FINAL_COHORT_FROZEN"]
    monkeypatch.setattr(runner, "current_stage", lambda project: stage[0])
    monkeypatch.setattr(runner, "advance", lambda project, target: stage.__setitem__(0, target))
    calls = []

    def evaluate(partition, start, end, specs, costs, seed):
        calls.append(partition)
        if partition == "HISTORICAL_AUDIT_2":
            assert runner.A1.exists()
            assert project.freeze_path("audit_1_report").exists()
            assert not runner.BOTH.exists()
            assert not (tmp_path / "reports/V5_HISTORICAL_AUDIT_1_REPORT.json").exists()
        return {"candidate_ids": [cid], "rows": {cid: {"net_r": len(calls)}}}

    monkeypatch.setattr(runner, "_evaluate", evaluate)
    runner.main()
    assert calls == ["HISTORICAL_AUDIT_1", "HISTORICAL_AUDIT_2"]
    assert runner.BOTH.exists()
    assert (tmp_path / "reports/V5_HISTORICAL_AUDIT_1_REPORT.json").exists()
    assert (tmp_path / "reports/V5_HISTORICAL_AUDIT_2_REPORT.json").exists()
