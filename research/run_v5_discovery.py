"""One frozen exploratory V5 search on real DISCOVERY after v5-prereg verifies."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json

import numpy as np

from quantlab5.data.market import load_market
from quantlab5.engine.costs import CostModel
from quantlab5.isolation.manifests import build_manifest, write_manifest
from quantlab5.isolation.prereg_gate import prereg_ready
from quantlab5.isolation.stage_gate import current_stage
from quantlab5.project import ROOT, default_project
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v5.market_search import adaptive_search, coverage_for_trace
from quantlab5.v5.signals import SignalContext

READS_MARKET_DATA = True
REPORT = ROOT / "reports/V5_DISCOVERY_EXECUTABLE.json"
SUMMARY = ROOT / "V5_DISCOVERY_REPORT.md"
FREEZE = ROOT / "V5_DISCOVERY_FREEZE.json"


def _record(r, years):
    periods = {}
    for name, lo, hi in (("2010-2012", 2010, 2012),
                         ("2013-2015", 2013, 2015),
                         ("2016-2018", 2016, 2018)):
        mask = (years >= lo) & (years <= hi)
        periods[name] = {"net_r": float(r.daily_r[mask].sum()),
                         "trades": int(r.daily_count[mask].sum()),
                         "mean_daily_r": float(r.daily_r[mask].mean()) if mask.any() else 0.0}
    return {"candidate_id": r.candidate_id, "spec": r.spec, "stage": r.stage,
            "family": r.family, "side": r.side, "trades": r.trades,
            "active_years": r.active_years, "net_r": r.net_r,
            "expectancy_r": r.expectancy_r, "profit_factor": r.profit_factor,
            "max_drawdown_r": r.max_drawdown_r, "daily_hac_t": r.statistic,
            "stress_net_r": r.stress_net_r, "matched_excess_r": r.matched_excess_r,
            "signal_hash": r.signal_hash, "subperiods": periods,
            "daily_r": r.daily_r.tolist(), "daily_count": r.daily_count.tolist(),
            "entry_indices": r.entry_indices.tolist(),
            "trade_sides": r.trade_sides.tolist(),
            "exit_indices": r.exit_indices.tolist() if r.exit_indices is not None else []}


def main():
    ok, reason = prereg_ready(ROOT)
    if not ok:
        raise RuntimeError(reason)
    project = default_project()
    if current_stage(project) != "DISCOVERY":
        raise RuntimeError("real V5 discovery requires DISCOVERY stage")
    if REPORT.exists() or SUMMARY.exists() or FREEZE.exists() or project.freeze_path("discovery").exists():
        raise RuntimeError("real V5 discovery already has an output; no rerun/selection")
    market = load_market("DISCOVERY", "2010-06-08", "2018-12-31",
                         purpose="V5_FROZEN_EXPLORATORY_DISCOVERY")
    costs = CostModel.from_project(project)
    trace = adaptive_search(market, costs)
    context = SignalContext(market)
    years = np.asarray(context.session_days).astype("datetime64[D]").astype("datetime64[Y]").astype(int)+1970
    records = {r.candidate_id: _record(r, years) for r in trace.records}
    coverage = {cid: {str(b): asdict(row) for b, row in data.items()}
                for cid, data in coverage_for_trace(market, trace, costs).items()}
    report = {"kind": "V5_FROZEN_EXPLORATORY_DISCOVERY", "created_utc": datetime.now(timezone.utc).isoformat(),
              "prereg_sha256": file_sha256(ROOT/"V5_PREREGISTRATION_FREEZE.json"),
              "market_hashes": {"NQ": market.nq.content_hash(), "ES": market.es.content_hash()},
              "records": records, "record_order": [r.candidate_id for r in trace.records],
              "stage_a_family_p": trace.stage_a_family_p,
              "stage_a_reference": "centered common-day stream bootstrap 500/block20/HAC20/seed515001",
              "expanded_families": trace.expanded_families,
              "b_winner_ids": trace.b_winner_ids,
              "qualifying_ids": trace.qualifying_ids,
              "nominee_ids": trace.nominee_ids,
              "exact_duplicate_of": trace.exact_duplicate_of,
              "behavior_duplicate_of": trace.behavior_duplicate_of,
              "pair_similarities": [asdict(x) for x in trace.pair_similarities],
              "mnq_budget_coverage": coverage,
              "candidate_count": len(trace.records),
              "qualifier_count": len(trace.qualifying_ids),
              "real_discovery_inferential_claim": False}
    REPORT.write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False)+"\n",
                      encoding="utf-8")
    SUMMARY.write_text(
        "# V5 exploratory DISCOVERY report\n\n"
        f"Evaluated {len(trace.records)} deterministic Q5 candidates across "
        f"{len(trace.expanded_families)} expanded families; "
        f"{len(trace.qualifying_ids)} met the frozen economic/stability gate. "
        "All qualifiers advance without rank or correlation cutoff. "
        "This period is exploratory, not confirmatory.\n\n"
        "Complete per-candidate specifications, daily streams, subperiods, "
        "duplicate/overlap annotations, and $250/$300/$350/$400 coverage are in "
        "`reports/V5_DISCOVERY_EXECUTABLE.json`.\n", encoding="utf-8")
    specs = {cid: records[cid]["spec"] for cid in trace.qualifying_ids}
    body = {"kind": "V5_DISCOVERY_COHORT_FREEZE", "status": "FROZEN",
            "report_sha256": file_sha256(REPORT), "prereg_sha256": report["prereg_sha256"],
            "qualifying_ids": list(trace.qualifying_ids), "specs": specs,
            "evaluated_ids_sha256": sha256_text("\n".join(report["record_order"])),
            "no_cap": len(specs) == len(trace.qualifying_ids)}
    FREEZE.write_text(json.dumps({**body, "body_sha256": sha256_text(canonical_json(body))},
                                 sort_keys=True, indent=2)+"\n", encoding="utf-8")
    sections = {"validation_rules": "V5_HOLDOUT_CONFIRMATION_PROTOCOL_FREEZE.json",
                "selection_process": "all frozen economic/stability qualifiers; no top-N or correlation deletion",
                "candidates": specs, "qualifying": list(trace.qualifying_ids),
                "duplicate_of": {cid: trace.behavior_duplicate_of[cid]
                                 for cid in specs if cid in trace.behavior_duplicate_of}}
    manifest = build_manifest("DISCOVERY_FREEZE", sections, ROOT,
                              files=("V5_DISCOVERY_FREEZE.json", "V5_DISCOVERY_REPORT.md",
                                     "reports/V5_DISCOVERY_EXECUTABLE.json",
                                     "V5_HOLDOUT_CONFIRMATION_PROTOCOL_FREEZE.json"))
    write_manifest(project.freeze_path("discovery"), manifest)
    print(f"Discovery freeze written: {len(trace.records)} evaluated, {len(specs)} qualify")


if __name__ == "__main__":
    main()
