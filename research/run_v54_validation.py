"""Exact, no-cap V5.4 2019–2022 holdout and frozen Holm confirmation."""
from __future__ import annotations

import json
import os

import numpy as np

from quantlab5.data.market import load_market
from quantlab5.engine.costs import CostModel
from quantlab5.project import ROOT, default_project
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v5.market_search import _shadow_clock_baseline
from quantlab5.v54.access import _frozen_file
from quantlab5.v54.engine import evaluate
from quantlab5.v54.events import EventCache
from quantlab5.v54.inference import (holm_adjust, validation_evidence,
                                      validation_label)
from quantlab5.v54.prereg_gate import ready
from quantlab5.v54.universe import id_for


READS_MARKET_DATA = True
WORK = ROOT/"reports/v54"
SOURCE = WORK/"qualifier_details.jsonl"
RAW = WORK/"validation_raw.jsonl"
PROGRESS = WORK/"validation_progress.json"
RESULT = ROOT/"reports/V5_4_VALIDATION_RESULTS.jsonl"
REPORT = ROOT/"V5_4_VALIDATION_REPORT.md"
FREEZE = ROOT/"V5_4_VALIDATION_FREEZE.json"
COHORT = ROOT/"V5_4_SCIENTIFIC_COHORT_FREEZE.json"


def _atomic(path, obj):
    temp = path.with_suffix(path.suffix+".tmp")
    temp.write_text(json.dumps(obj, sort_keys=True, indent=2, allow_nan=False)+"\n",
                    encoding="utf-8")
    temp.replace(path)


def _source_rows():
    with SOURCE.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def _checkpoint(expected_count):
    source_sha = file_sha256(SOURCE)
    if PROGRESS.exists():
        p = json.loads(PROGRESS.read_text(encoding="utf-8"))
        if p["source_sha256"] != source_sha or p["expected_count"] != expected_count:
            raise RuntimeError("V5.4 validation checkpoint differs from discovery freeze")
        if not RAW.exists() or RAW.stat().st_size < p["committed_bytes"]:
            raise RuntimeError("V5.4 validation raw output lost committed bytes")
        with RAW.open("r+b") as f:
            f.truncate(p["committed_bytes"])
        return p
    if RAW.exists():
        raise RuntimeError("validation raw output exists without checkpoint")
    p = {"kind": "V5_4_EXACT_VALIDATION_PROGRESS", "source_sha256": source_sha,
         "expected_count": expected_count, "completed": 0, "committed_bytes": 0}
    _atomic(PROGRESS, p)
    return p


def _evaluate_one(market, cache, costs, shadow, discovery):
    spec = discovery["spec"]
    if id_for(spec) != discovery["candidate_id"]:
        raise RuntimeError("V5.4 frozen Q54 ID/specification mismatch")
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
    inference = validation_evidence(daily)
    return {"candidate_id": discovery["candidate_id"], "spec": spec,
            "discovery": {k: discovery[k] for k in (
                "trades", "net_r", "stress_net_r", "expectancy_r",
                "profit_factor", "max_drawdown_r", "matched_excess_r",
                "core_neighbor_positive_fraction")},
            "validation": {"trades": int(metrics[0]), "net_r": float(metrics[1]),
                           "stress_net_r": float(metrics[2]),
                           "expectancy_r": float(metrics[3]),
                           "profit_factor": float(metrics[4]) if np.isfinite(metrics[4]) else None,
                           "max_drawdown_r": float(metrics[5]),
                           "active_years": int(metrics[6]),
                           "subperiod_net_r": [float(x) for x in metrics[7:10]],
                           "matched_excess_r": float(metrics[13]),
                           "trade_entry_indices": entry.tolist(),
                           "trade_exit_indices": exit_.tolist(),
                           "daily_net_r": daily.tolist(), **inference}}


def _raw_validation(market, costs, expected_count):
    p = _checkpoint(expected_count)
    if p["completed"] == expected_count:
        return
    cache = EventCache(market)
    shadow = _shadow_clock_baseline(
        market, cache.context.stop,
        costs.per_trade_points("MNQ", "baseline"))
    with RAW.open("ab") as f:
        for i, discovery in enumerate(_source_rows()):
            if i < p["completed"]:
                continue
            result = _evaluate_one(market, cache, costs, shadow, discovery)
            raw = (json.dumps(result, sort_keys=True, allow_nan=False)+"\n").encode("utf-8")
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
            p.update(completed=i+1, committed_bytes=f.tell())
            _atomic(PROGRESS, p)
            if (i+1) % 100 == 0:
                print(f"V5.4 validation tested {i+1:,}/{expected_count:,}", flush=True)
    if p["completed"] != expected_count:
        raise RuntimeError("V5.4 validation failed to test every frozen qualifier")


def _classify(expected_count):
    if RESULT.exists() or REPORT.exists() or FREEZE.exists() or COHORT.exists():
        raise RuntimeError("V5.4 validation classification already exists")
    ps = []
    with RAW.open("r", encoding="utf-8") as f:
        for line in f:
            ps.append(json.loads(line)["validation"]["unadjusted_one_sided_p"])
    if len(ps) != expected_count:
        raise RuntimeError("V5.4 raw validation row count mismatch")
    adjusted = holm_adjust(np.asarray(ps, float))
    supported = []
    counts = {label: 0 for label in ("SUPPORTED", "INCONCLUSIVE / UNDERPOWERED", "REJECTED")}
    with RAW.open("r", encoding="utf-8") as source, RESULT.open("w", encoding="utf-8") as target:
        for p_adj, line in zip(adjusted, source):
            row = json.loads(line)
            v = row["validation"]
            label = validation_label(adjusted_p=float(p_adj), trades=v["trades"],
                                     active_years=v["active_years"],
                                     mean_daily_net_r=v["mean_daily_net_r"],
                                     stress_net_r=v["stress_net_r"],
                                     matched_excess_r=v["matched_excess_r"],
                                     upper95_mean_daily_net_r=v["upper95_mean_daily_net_r"])
            v["holm_adjusted_p"] = float(p_adj)
            v["classification"] = label
            counts[label] += 1
            if label == "SUPPORTED":
                supported.append((row["candidate_id"], row["spec"]))
            target.write(json.dumps(row, sort_keys=True, allow_nan=False)+"\n")
    REPORT.write_text(
        "# V5.4 exact-candidate 2019–2022 historical holdout validation\n\n"
        f"Tested all {expected_count:,} frozen discovery qualifiers. "
        f"SUPPORTED={counts['SUPPORTED']:,}; "
        f"INCONCLUSIVE / UNDERPOWERED={counts['INCONCLUSIVE / UNDERPOWERED']:,}; "
        f"REJECTED={counts['REJECTED']:,}. "
        "One-sided daily HAC inference uses Holm FWER correction over the exact "
        "frozen hypothesis set. Every supported Q54 rule survives without a cap.\n",
        encoding="utf-8")
    body = {"kind": "V5_4_VALIDATION_FREEZE", "status": "FROZEN",
            "discovery_freeze_sha256": file_sha256(ROOT/"V5_4_DISCOVERY_FREEZE.json"),
            "evaluated_count": expected_count, "supported_count": len(supported),
            "class_counts": counts, "no_top_n_cap": True,
            "files_sha256": {rel: file_sha256(ROOT/rel) for rel in (
                "reports/V5_4_VALIDATION_RESULTS.jsonl", "V5_4_VALIDATION_REPORT.md")}}
    _atomic(FREEZE, {**body, "body_sha256": sha256_text(canonical_json(body))})
    cohort_body = {"kind": "V5_4_SCIENTIFIC_COHORT_FREEZE", "status": "FROZEN",
                   "validation_freeze_sha256": file_sha256(FREEZE),
                   "candidate_ids": [cid for cid, _ in supported],
                   "specs": {cid: spec for cid, spec in supported},
                   "portfolio_selection": "none; individual MNQ coverage only",
                   "no_top_n_cap": True}
    _atomic(COHORT, {**cohort_body,
                     "body_sha256": sha256_text(canonical_json(cohort_body))})
    print(f"V5.4 validation frozen: {expected_count:,} tested, {len(supported):,} supported")


def main():
    ok, reason = ready(ROOT)
    if not ok:
        raise RuntimeError(reason)
    ok, reason = _frozen_file(ROOT, "V5_4_DISCOVERY_FREEZE.json", "v5.4-discovery")
    if not ok:
        raise RuntimeError(reason)
    doc = json.loads((ROOT/"V5_4_DISCOVERY_FREEZE.json").read_text(encoding="utf-8"))
    n = int(doc["qualifier_count"])
    if n:
        market = load_market("VALIDATION", "2019-01-02", "2022-12-30",
                             purpose="V5_4_FROZEN_VALIDATION")
        _raw_validation(market, CostModel.from_project(default_project()), n)
    else:
        if not RAW.exists():
            RAW.write_text("", encoding="utf-8")
    _classify(n)


if __name__ == "__main__":
    main()
