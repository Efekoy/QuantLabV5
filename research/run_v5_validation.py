"""Confirm every frozen DISCOVERY qualifier in the 2019–2022 holdout."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from types import SimpleNamespace

from quantlab5.data.market import load_market
from quantlab5.engine.costs import CostModel
from quantlab5.isolation.manifests import (build_manifest, read_manifest,
                                           verify_manifest, write_manifest)
from quantlab5.isolation.stage_gate import advance, current_stage
from quantlab5.project import ROOT, default_project
from quantlab5.search.candidate_id import candidate_id
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v5.holdout_confirmation import Confirmation, confirm_frozen_candidates
from quantlab5.v5.market_search import SearchTrace, coverage_for_trace

READS_MARKET_DATA = True
DISCOVERY = ROOT / "V5_DISCOVERY_FREEZE.json"
DISCOVERY_REPORT = ROOT / "reports/V5_DISCOVERY_EXECUTABLE.json"
REPORT = ROOT / "reports/V5_VALIDATION_EXECUTABLE.json"
SUMMARY = ROOT / "V5_VALIDATION_REPORT.md"
FREEZE = ROOT / "V5_VALIDATION_FREEZE.json"
COHORT = ROOT / "V5_SCIENTIFIC_COHORT_FREEZE.json"


def _discovery(project):
    verify_manifest(project.freeze_path("discovery"), ROOT, "DISCOVERY_FREEZE",
                    ("validation_rules", "selection_process"))
    doc = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    body = {k: v for k, v in doc.items() if k != "body_sha256"}
    if sha256_text(canonical_json(body)) != doc.get("body_sha256"):
        raise RuntimeError("DISCOVERY freeze body hash mismatch")
    if file_sha256(DISCOVERY_REPORT) != doc["report_sha256"]:
        raise RuntimeError("DISCOVERY report differs from frozen hash")
    specs = doc["specs"]
    ids = tuple(doc["qualifying_ids"])
    if len(ids) != len(set(ids)) or set(ids) != set(specs):
        raise RuntimeError("frozen discovery qualifier set mismatch")
    if any(candidate_id(specs[cid]) != cid for cid in ids):
        raise RuntimeError("frozen discovery Q5 ID mismatch")
    return ids, specs


def main():
    project = default_project()
    ids, specs = _discovery(project)
    stage = current_stage(project)
    if stage == "DISCOVERY_FROZEN":
        advance(project, "VALIDATION")
    elif stage != "VALIDATION":
        raise RuntimeError(f"validation cannot run at {stage}")
    if any(p.exists() for p in (REPORT, SUMMARY, FREEZE, COHORT, project.freeze_path("validation"))):
        raise RuntimeError("validation output already exists; no retesting or reselection")
    discovery = SimpleNamespace(
        records=tuple(SimpleNamespace(candidate_id=cid, spec=specs[cid]) for cid in ids),
        qualifying_ids=ids, nominee_ids=())
    if ids:
        market = load_market("VALIDATION", "2019-01-02", "2022-12-30",
                             purpose="V5_FROZEN_HOLDOUT_CONFIRMATION")
        costs = CostModel.from_project(project)
        result = confirm_frozen_candidates(market, discovery, costs)
    else:
        market = None
        costs = None
        result = Confirmation((), {}, {}, {}, (), {}, 0, ())
    if tuple(r.candidate_id for r in result.evaluated) != ids:
        raise RuntimeError("validation failed to evaluate the whole frozen candidate list")
    discovery_rows = json.loads(DISCOVERY_REPORT.read_text(encoding="utf-8"))["records"]
    rows = {}
    for r in result.evaluated:
        cid = r.candidate_id
        rows[cid] = {
            "spec": r.spec, "discovery": {key: discovery_rows[cid][key] for key in
                                    ("trades", "expectancy_r", "profit_factor",
                                     "net_r", "max_drawdown_r")},
            "validation": {"trades": r.trades, "active_years": r.active_years,
                           "net_r": r.net_r, "expectancy_r": r.expectancy_r,
                           "profit_factor": r.profit_factor,
                           "max_drawdown_r": r.max_drawdown_r,
                           "stress_net_r": r.stress_net_r,
                           "matched_excess_r": r.matched_excess_r,
                           "daily_r": r.daily_r.tolist(),
                           "daily_count": r.daily_count.tolist(),
                           "unadjusted_hac_p": result.unadjusted_p[cid],
                           "adjusted_p": result.adjusted_p[cid],
                           "upper95_mean_daily_r": result.upper95_mean_daily_r[cid],
                           "classification": result.classification[cid]}}
    if ids:
        trace = SearchTrace(result.evaluated, {}, (), {}, (), {}, {}, (), 0., {}, ids)
        coverage = {cid: {str(b): asdict(v) for b, v in data.items()}
                    for cid, data in coverage_for_trace(market, trace, costs).items()}
    else:
        coverage = {}
    report = {"kind": "V5_EXACT_CANDIDATE_HOLDOUT_VALIDATION",
              "created_utc": datetime.now(timezone.utc).isoformat(),
              "discovery_freeze_sha256": file_sha256(DISCOVERY),
              "holdout_protocol_sha256": file_sha256(ROOT/"V5_HOLDOUT_CONFIRMATION_PROTOCOL_FREEZE.json"),
              "candidate_ids": list(ids), "rows": rows,
              "mnq_budget_coverage": coverage,
              "bootstrap_reps": result.bootstrap_reps,
              "unresolved_ids": list(result.unresolved_ids),
              "survivor_ids": list(result.survivor_ids),
              "class_counts": {label: sum(x == label for x in result.classification.values())
                               for label in ("SUPPORTED", "INCONCLUSIVE / UNDERPOWERED", "REJECTED")}}
    REPORT.write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False)+"\n",
                      encoding="utf-8")
    SUMMARY.write_text(
        "# V5 2019–2022 validation report\n\n"
        f"Tested all {len(ids)} frozen DISCOVERY qualifiers unchanged. "
        f"SUPPORTED: {report['class_counts']['SUPPORTED']}; "
        f"INCONCLUSIVE / UNDERPOWERED: {report['class_counts']['INCONCLUSIVE / UNDERPOWERED']}; "
        f"REJECTED: {report['class_counts']['REJECTED']}. "
        "The exact-candidate common-day Romano-Wolf result governs support. "
        "Complete per-candidate outcomes are in `reports/V5_VALIDATION_EXECUTABLE.json`.\n",
        encoding="utf-8")
    body = {"kind": "V5_VALIDATION_COHORT_FREEZE", "status": "FROZEN",
            "discovery_freeze_sha256": file_sha256(DISCOVERY),
            "report_sha256": file_sha256(REPORT),
            "evaluated_ids": list(ids), "survivor_ids": list(result.survivor_ids),
            "classifications": result.classification,
            "survivor_specs": {cid: specs[cid] for cid in result.survivor_ids}}
    FREEZE.write_text(json.dumps({**body, "body_sha256": sha256_text(canonical_json(body))},
                                 sort_keys=True, indent=2)+"\n", encoding="utf-8")
    sections = {"validation_rules_sha256": file_sha256(ROOT/"V5_HOLDOUT_CONFIRMATION_PROTOCOL_FREEZE.json"),
                "evaluated": list(ids), "survivors": list(result.survivor_ids)}
    manifest = build_manifest("VALIDATION_FREEZE", sections, ROOT,
                              files=("V5_VALIDATION_FREEZE.json", "V5_VALIDATION_REPORT.md",
                                     "reports/V5_VALIDATION_EXECUTABLE.json"))
    write_manifest(project.freeze_path("validation"), manifest)
    cohort_body = {"kind": "V5_SCIENTIFIC_COHORT_FREEZE", "status": "FROZEN",
                   "validation_freeze_sha256": file_sha256(FREEZE),
                   "candidate_ids": list(result.survivor_ids),
                   "specs": {cid: specs[cid] for cid in result.survivor_ids}}
    COHORT.write_text(json.dumps({**cohort_body,
                                  "body_sha256": sha256_text(canonical_json(cohort_body))},
                                 sort_keys=True, indent=2)+"\n", encoding="utf-8")
    print(f"Validation freeze written: {len(ids)} evaluated, {len(result.survivor_ids)} supported")


if __name__ == "__main__":
    main()
