"""Evaluate both frozen historical audits before revealing either result.

Run phase1, commit/tag v5.4-audit1, then phase2 and reveal. The phase1 command
prints no outcomes; its sealed JSONL is pinned by its freeze before phase2.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

from quantlab5.data.market import load_market
from quantlab5.engine.costs import CostModel
from quantlab5.project import ROOT, default_project
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v5.market_search import _shadow_clock_baseline
from quantlab5.v54.access import _frozen_file
from quantlab5.v54.engine import evaluate
from quantlab5.v54.events import EventCache
from quantlab5.v54.inference import holm_adjust, validation_evidence
from quantlab5.v54.universe import id_for


READS_MARKET_DATA = True
WORK = ROOT / "reports/v54"
MANIFEST = ROOT / "V5_4_HISTORICAL_AUDIT_MANIFEST.json"
COHORT = ROOT / "V5_4_SCIENTIFIC_COHORT_FREEZE.json"
PHASES = {
    "phase1": ("HISTORICAL_AUDIT_1", "V5_4_BLIND_AUDIT_1",
               "V5_4_AUDIT_1_REPORT_FREEZE.json", "audit_1"),
    "phase2": ("HISTORICAL_AUDIT_2", "V5_4_BLIND_AUDIT_2",
               "V5_4_AUDIT_2_REPORT_FREEZE.json", "audit_2"),
}


def _atomic(path, doc):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(doc, sort_keys=True, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")
    temp.replace(path)


def _contract():
    ok, reason = _frozen_file(ROOT, MANIFEST.name, "v5.4-cohort")
    if not ok:
        raise RuntimeError(reason)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cohort = json.loads(COHORT.read_text(encoding="utf-8"))
    ids = manifest["candidate_ids"]
    if (file_sha256(COHORT) != manifest["cohort_sha256"]
            or sha256_text(canonical_json(cohort["specs"])) != manifest["specs_sha256"]
            or ids != cohort["candidate_ids"]
            or len(ids) != len(set(ids))):
        raise RuntimeError("V5.4 cohort differs from the frozen audit contract")
    for cid in ids:
        if id_for(cohort["specs"][cid]) != cid:
            raise RuntimeError("V5.4 Q54 ID/spec mismatch in audit cohort")
    return manifest, cohort


def _one(market, cache, costs, shadow, cid, spec):
    config = {k: spec[k] for k in ("family", "lookback", "threshold",
                                    "direction", "session", "filters", "entry")}
    events = cache.events(config, spec["management"]["stop"])
    metrics, entry, exit_, net_r = evaluate(
        market, events, spec["management"],
        baseline_cost_points=costs.per_trade_points("MNQ", "baseline"),
        stress_cost_points=costs.per_trade_points("MNQ", "stress"),
        shadow_baseline=shadow, capture=True)
    daily = np.zeros(len(cache.context.session_days), float)
    if len(entry):
        np.add.at(daily, cache.context.session_inverse[entry], net_r)
    return {"candidate_id": cid, "spec_sha256": sha256_text(canonical_json(spec)),
            "trades": int(metrics[0]), "net_r": float(metrics[1]),
            "stress_net_r": float(metrics[2]), "expectancy_r": float(metrics[3]),
            "profit_factor": float(metrics[4]) if np.isfinite(metrics[4]) else None,
            "max_drawdown_r": float(metrics[5]), "active_years": int(metrics[6]),
            "matched_excess_r": float(metrics[13]),
            "daily_net_r": daily.tolist(), "trade_entry_indices": entry.tolist(),
            "trade_exit_indices": exit_.tolist()}


def run_phase(name):
    if name not in PHASES:
        raise ValueError(name)
    manifest, cohort = _contract()
    if name == "phase2":
        ok, reason = _frozen_file(ROOT, "V5_4_AUDIT_1_REPORT_FREEZE.json", "v5.4-audit1")
        if not ok:
            raise RuntimeError(reason)
    partition, purpose, freeze_name, interval_key = PHASES[name]
    out = WORK / f"{name}_sealed.jsonl"
    progress = WORK / f"{name}_progress.json"
    freeze = ROOT / freeze_name
    if freeze.exists():
        raise RuntimeError(f"{name} was already frozen")
    ids = cohort["candidate_ids"]
    if progress.exists():
        p = json.loads(progress.read_text(encoding="utf-8"))
        if p["manifest_sha256"] != file_sha256(MANIFEST) or p["expected"] != len(ids):
            raise RuntimeError(f"{name} checkpoint differs from audit contract")
        if not out.exists() or out.stat().st_size < p["committed_bytes"]:
            raise RuntimeError(f"{name} sealed output lost committed bytes")
        with out.open("r+b") as f:
            f.truncate(p["committed_bytes"])
    else:
        if out.exists():
            raise RuntimeError(f"{name} output exists without checkpoint")
        p = {"manifest_sha256": file_sha256(MANIFEST), "expected": len(ids),
             "completed": 0, "committed_bytes": 0}
        _atomic(progress, p)
    market = None
    cache = None
    costs = CostModel.from_project(default_project())
    shadow = None
    if ids and p["completed"] < len(ids):
        start, end = manifest[interval_key]
        market = load_market(partition, start, end, purpose=purpose)
        cache = EventCache(market)
        shadow = _shadow_clock_baseline(
            market, cache.context.stop, costs.per_trade_points("MNQ", "baseline"))
    with out.open("ab") as f:
        for i in range(p["completed"], len(ids)):
            cid = ids[i]
            row = _one(market, cache, costs, shadow, cid, cohort["specs"][cid])
            f.write((json.dumps(row, sort_keys=True, allow_nan=False) + "\n").encode("utf-8"))
            f.flush()
            os.fsync(f.fileno())
            p.update(completed=i + 1, committed_bytes=f.tell())
            _atomic(progress, p)
    if p["completed"] != len(ids):
        raise RuntimeError(f"{name} did not evaluate the full cohort")
    body = {"kind": f"V5_4_{name.upper()}_SEALED_FREEZE", "status": "FROZEN",
            "manifest_sha256": file_sha256(MANIFEST), "cohort_sha256": file_sha256(COHORT),
            "candidate_ids": ids, "evaluated_count": len(ids),
            "data_read": bool(ids),
            "files_sha256": {str(out.relative_to(ROOT)).replace("\\", "/"): file_sha256(out)}}
    _atomic(freeze, {**body, "body_sha256": sha256_text(canonical_json(body))})
    print(f"V5.4 {name} sealed; {len(ids):,} cohort candidates evaluated")


def reveal():
    manifest, cohort = _contract()
    for name, tag in (("V5_4_AUDIT_1_REPORT_FREEZE.json", "v5.4-audit1"),
                      ("V5_4_AUDIT_2_REPORT_FREEZE.json", "v5.4-audit2")):
        ok, reason = _frozen_file(ROOT, name, tag)
        if not ok:
            raise RuntimeError(reason)
    out = ROOT / "V5_4_BOTH_HISTORICAL_AUDITS_COMPLETE.json"
    report = ROOT / "V5_4_HISTORICAL_AUDITS_REPORT.md"
    results_path = ROOT / "reports/V5_4_HISTORICAL_AUDIT_RESULTS.json"
    if out.exists() or report.exists() or results_path.exists():
        raise RuntimeError("both-audit reveal already exists")
    summaries = {}
    ids = cohort["candidate_ids"]
    for phase in PHASES:
        path = WORK / f"{phase}_sealed.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        if [row["candidate_id"] for row in rows] != ids:
            raise RuntimeError("different cohort or order in historical audits")
        for row in rows:
            spec = cohort["specs"][row["candidate_id"]]
            if row["spec_sha256"] != sha256_text(canonical_json(spec)):
                raise RuntimeError("historical audit specification changed")
        summaries[phase] = rows
    labels = {}
    for phase, rows in summaries.items():
        evidence = [validation_evidence(np.asarray(row["daily_net_r"], float))
                    for row in rows]
        adjusted = holm_adjust(np.asarray(
            [x["unadjusted_one_sided_p"] for x in evidence], float))
        phase_labels = {}
        for row, ev, p_adj in zip(rows, evidence, adjusted):
            if (p_adj <= .05 and row["trades"] >= 20
                    and ev["mean_daily_net_r"] > 0
                    and row["stress_net_r"] > 0 and row["matched_excess_r"] > 0):
                label = "SUPPORTED"
            elif ev["upper95_mean_daily_net_r"] < 0:
                label = "REJECTED"
            else:
                label = "INCONCLUSIVE / UNDERPOWERED"
            phase_labels[row["candidate_id"]] = {
                "classification": label, "holm_adjusted_p": float(p_adj),
                **ev, **{k: row[k] for k in ("trades", "net_r", "stress_net_r",
                                             "expectancy_r", "profit_factor",
                                             "max_drawdown_r", "active_years",
                                             "matched_excess_r")}}
        labels[phase] = phase_labels
    _atomic(results_path, {"kind": "V5_4_SIMULTANEOUS_AUDIT_RESULTS",
                           "candidate_ids": ids, "audits": labels})
    dual_supported = [cid for cid in ids
                      if all(labels[phase][cid]["classification"] == "SUPPORTED"
                             for phase in PHASES)]
    body = {"kind": "V5_4_BOTH_HISTORICAL_AUDITS_COMPLETE", "status": "FROZEN",
            "manifest_sha256": file_sha256(MANIFEST), "candidate_ids": ids,
            "audit_1_freeze_sha256": file_sha256(ROOT / "V5_4_AUDIT_1_REPORT_FREEZE.json"),
            "audit_2_freeze_sha256": file_sha256(ROOT / "V5_4_AUDIT_2_REPORT_FREEZE.json"),
            "simultaneous_reveal": True,
            "results_sha256": file_sha256(results_path),
            "dual_supported_ids": dual_supported,
            "audit_1_positive_after_cost": sum(x["net_r"] > 0 for x in summaries["phase1"]),
            "audit_2_positive_after_cost": sum(x["net_r"] > 0 for x in summaries["phase2"]),
            "dual_positive_after_cost_ids": [a["candidate_id"] for a, b in
                zip(summaries["phase1"], summaries["phase2"])
                if a["net_r"] > 0 and b["net_r"] > 0]}
    _atomic(out, {**body, "body_sha256": sha256_text(canonical_json(body))})
    report.write_text(
        "# V5.4 simultaneous historical audit reveal\n\n"
        f"Exact supported cohort: {len(ids):,}. Audit 1 positive after cost: "
        f"{body['audit_1_positive_after_cost']:,}; Audit 2 positive after cost: "
        f"{body['audit_2_positive_after_cost']:,}; dual positive: "
        f"{len(body['dual_positive_after_cost_ids']):,}; dual SUPPORTED: "
        f"{len(dual_supported):,}.\n\n"
        "These are historical audits, not prospective live-forward evidence. "
        "Both exact-candidate files are in reports/v54/.\n", encoding="utf-8")
    print("V5.4 both historical audits revealed together")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in (*PHASES, "reveal"):
        raise SystemExit("usage: python -m research.run_v54_blind_audits phase1|phase2|reveal")
    if sys.argv[1] == "reveal":
        reveal()
    else:
        run_phase(sys.argv[1])
