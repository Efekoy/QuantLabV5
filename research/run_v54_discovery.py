"""Checkpointable full V5.4 DEVELOPMENT search; no family gate and no cap.

Only call after the v5.4-prereg tag verifies. Each completed signal group writes
all 198 management rows before its progress marker advances. An interrupted
uncommitted group is overwritten on resume; committed groups are never rerun.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import os

import numpy as np

from quantlab5.data.market import load_market
from quantlab5.engine.costs import CostModel
from quantlab5.isolation import ledger
from quantlab5.project import ROOT, default_project
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v5.market_search import _shadow_clock_baseline
from quantlab5.v54.engine import evaluate
from quantlab5.v54.events import EventCache
from quantlab5.v54.inference import discovery_qualifies
from quantlab5.v54.prereg_gate import ready
from quantlab5.v54.universe import (CORE, DIRECTIONS, ENTRIES, SESSIONS,
                                     core_neighbor_indices, counts, filters_for,
                                     id_for, managements, signal_configs, spec_at)


READS_MARKET_DATA = True
WORK = ROOT / "reports/v54"
ROWS = WORK / "first_pass.npy"
PROGRESS = WORK / "progress.json"
QUALIFIERS = WORK / "qualifying_rows.npy"
DETAIL = WORK / "qualifier_details.jsonl"
DETAIL_PROGRESS = WORK / "qualifier_detail_progress.json"
DONE = WORK / "first_pass_complete.json"
FREEZE = ROOT / "V5_4_DISCOVERY_FREEZE.json"
SUMMARY = ROOT / "V5_4_DISCOVERY_REPORT.md"
DTYPE = np.dtype([
    ("candidate_id", "S28"), ("trades", "i4"), ("active_years", "u1"),
    ("net_r", "f8"), ("stress_net_r", "f8"), ("expectancy_r", "f8"),
    ("profit_factor", "f8"), ("max_drawdown_r", "f8"),
    ("matched_excess_r", "f8"),
    ("subperiod_1", "f8"), ("subperiod_2", "f8"), ("subperiod_3", "f8"),
    ("subperiod_trades_1", "i4"), ("subperiod_trades_2", "i4"),
    ("subperiod_trades_3", "i4"),
])


def _atomic_json(path: Path, obj: dict):
    temp = path.with_suffix(path.suffix+".tmp")
    temp.write_text(json.dumps(obj, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    temp.replace(path)


def _configs():
    for family in CORE:
        yield from signal_configs(family)


def _initial(total: int, prereg_sha: str, universe_sha: str):
    WORK.mkdir(parents=True, exist_ok=True)
    if PROGRESS.exists():
        p = json.loads(PROGRESS.read_text(encoding="utf-8"))
        if (p["total_specs"] != total or p["prereg_sha256"] != prereg_sha
                or p["universe_sha256"] != universe_sha
                or p["completed_rows"] != p["completed_signal_configs"]*len(managements())):
            raise RuntimeError("V5.4 checkpoint differs from the frozen universe")
        mm = np.load(ROWS, mmap_mode="r+")
        if mm.dtype != DTYPE or len(mm) != total:
            raise RuntimeError("V5.4 first-pass row store shape/dtype changed")
        if p["completed_rows"]:
            lo = p["completed_rows"]-len(managements())
            if sha256(mm[lo:p["completed_rows"]].tobytes()).hexdigest() != p["last_chunk_sha256"]:
                raise RuntimeError("V5.4 last committed checkpoint chunk changed")
        return mm, p
    if ROWS.exists():
        raise RuntimeError("first-pass row store exists without a checkpoint")
    mm = np.lib.format.open_memmap(ROWS, mode="w+", dtype=DTYPE, shape=(total,))
    p = {"kind": "V5_4_BROAD_DISCOVERY_PROGRESS", "status": "RUNNING",
         "total_specs": total, "completed_signal_configs": 0,
         "completed_rows": 0, "prereg_sha256": prereg_sha,
         "universe_sha256": universe_sha, "last_chunk_sha256": None}
    _atomic_json(PROGRESS, p)
    return mm, p


def _record(spec, metrics):
    row = np.zeros((), dtype=DTYPE)
    row["candidate_id"] = id_for(spec).encode("ascii")
    row["trades"] = int(metrics[0])
    row["net_r"] = metrics[1]
    row["stress_net_r"] = metrics[2]
    row["expectancy_r"] = metrics[3]
    row["profit_factor"] = metrics[4]
    row["max_drawdown_r"] = metrics[5]
    row["active_years"] = int(metrics[6])
    for j in range(3):
        row[f"subperiod_{j+1}"] = metrics[7+j]
        row[f"subperiod_trades_{j+1}"] = int(metrics[10+j])
    row["matched_excess_r"] = metrics[13]
    return row


def first_pass(market, costs, *, limit_signal_configs: int | None = None):
    """The limit exists only for synthetic tests; real main() always passes None."""
    c = counts()
    prereg_sha = file_sha256(ROOT/"V5_4_PREREGISTRATION_FREEZE.json")
    universe_sha = file_sha256(ROOT/"V5_4_SEARCH_UNIVERSE.json")
    mm, progress = _initial(c["total_specs"], prereg_sha, universe_sha)
    cache = EventCache(market)
    baseline = costs.per_trade_points("MNQ", "baseline")
    stress = costs.per_trade_points("MNQ", "stress")
    shadow = _shadow_clock_baseline(market, cache.context.stop, baseline)
    management = managements()
    previous_family = None
    for group, config in enumerate(_configs()):
        if group < progress["completed_signal_configs"]:
            continue
        if limit_signal_configs is not None and group >= limit_signal_configs:
            break
        if config["family"] != previous_family:
            cache.context.cache.clear()
            previous_family = config["family"]
        prepared = cache.signal_events(config)
        events = {stop: cache.events(config, stop, prepared)
                  for stop in {m.stop for m in management}}
        block = np.zeros(len(management), dtype=DTYPE)
        for j, choice in enumerate(management):
            spec = {"grammar": "V5_4_G1", **config,
                    "management": choice.as_dict()}
            metrics = evaluate(market, events[choice.stop], spec["management"],
                               baseline_cost_points=baseline,
                               stress_cost_points=stress,
                               shadow_baseline=shadow)[0]
            block[j] = _record(spec, metrics)
        lo = group*len(management)
        mm[lo:lo+len(management)] = block
        mm.flush()
        progress.update(completed_signal_configs=group+1,
                        completed_rows=lo+len(management),
                        last_chunk_sha256=sha256(block.tobytes()).hexdigest())
        _atomic_json(PROGRESS, progress)
        if (group+1) % 100 == 0:
            print(f"V5.4 completed {progress['completed_rows']:,}/{c['total_specs']:,}", flush=True)
    return mm, progress


def preliminary_qualifying_rows(mm) -> np.ndarray:
    """Scan every row in bounded chunks; return every exact economic qualifier."""
    chunks = []
    for lo in range(0, len(mm), 100_000):
        x = mm[lo:lo+100_000]
        mask = ((x["trades"] >= 120) & (x["active_years"] >= 6)
                & (x["net_r"] > 0) & (x["stress_net_r"] > 0)
                & (x["matched_excess_r"] > 0))
        chunks.append(np.flatnonzero(mask).astype(np.int64)+lo)
    return np.concatenate(chunks) if chunks else np.empty(0, np.int64)


def _outcome_distributions(mm):
    """Vectorized full-universe counts without storing a Python row per rule."""
    c = counts()
    families = tuple(CORE)
    boundaries = np.cumsum([c["family_signal_configs"][f] for f in families])
    management = managements()
    templates = tuple(sorted({m.template for m in management}))
    template_code = np.array([templates.index(m.template) for m in management], np.int64)
    accum = {name: {"evaluated": np.zeros(size, np.int64),
                    "profitable_after_cost": np.zeros(size, np.int64),
                    "stress_positive": np.zeros(size, np.int64),
                    "profit_factor_gt_1": np.zeros(size, np.int64)}
             for name, size in (("family", len(families)), ("management_template", len(templates)),
                                ("session", len(SESSIONS)), ("direction", len(DIRECTIONS)))}
    nmanagement = len(management)
    for lo in range(0, len(mm), 100_000):
        hi = min(lo+100_000, len(mm))
        x = mm[lo:hi]
        rows = np.arange(lo, hi, dtype=np.int64)
        groups = rows//nmanagement
        family_code = np.searchsorted(boundaries, groups, side="right")
        starts = np.r_[0, boundaries[:-1]]
        local = groups-starts[family_code]
        session_code = (local//(len(filters_for("E01"))*len(ENTRIES))) % len(SESSIONS)
        direction_code = (local//(len(SESSIONS)*len(filters_for("E01"))*len(ENTRIES))) % len(DIRECTIONS)
        codes = {"family": family_code,
                 "management_template": template_code[rows % nmanagement],
                 "session": session_code, "direction": direction_code}
        masks = {"evaluated": np.ones(len(x), bool),
                 "profitable_after_cost": x["net_r"] > 0,
                 "stress_positive": x["stress_net_r"] > 0,
                 "profit_factor_gt_1": x["profit_factor"] > 1}
        for name, code in codes.items():
            for metric, mask in masks.items():
                accum[name][metric] += np.bincount(code[mask],
                                                    minlength=len(accum[name][metric]))
    names = {"family": families, "management_template": templates,
             "session": SESSIONS, "direction": DIRECTIONS}
    return {axis: {str(value): {metric: int(vector[i]) for metric, vector in vals.items()}
                   for i, value in enumerate(names[axis])}
            for axis, vals in accum.items()}


def finalize_first_pass(mm, progress):
    if progress["completed_rows"] != progress["total_specs"]:
        return
    if DONE.exists():
        doc = json.loads(DONE.read_text(encoding="utf-8"))
        if (doc["row_file_sha256"] != file_sha256(ROWS)
                or doc["qualifier_row_file_sha256"] != file_sha256(QUALIFIERS)):
            raise RuntimeError("completed V5.4 first pass differs from frozen hashes")
        return
    if QUALIFIERS.exists():
        raise RuntimeError("qualifier rows exist without a completion marker")
    qualifiers = preliminary_qualifying_rows(mm)
    np.save(QUALIFIERS, qualifiers)
    summaries = {}
    for key in ("net_r", "stress_net_r", "expectancy_r"):
        summaries[f"positive_{key}"] = int(sum(np.count_nonzero(
            mm[lo:lo+100_000][key] > 0) for lo in range(0, len(mm), 100_000)))
    body = {"kind": "V5_4_FIRST_PASS_COMPLETE", "specifications_evaluated": len(mm),
            "qualifier_count": len(qualifiers), "qualifier_row_file_sha256": file_sha256(QUALIFIERS),
            "row_file_sha256": file_sha256(ROWS), "summary_counts": summaries,
            "outcome_distributions": _outcome_distributions(mm),
            "prereg_sha256": progress["prereg_sha256"]}
    _atomic_json(DONE, body)
    progress["status"] = "FIRST_PASS_COMPLETE"
    _atomic_json(PROGRESS, progress)


def _budget_coverage(market, events, management, costs, shadow):
    from quantlab5.v54.events import Events
    out = {}
    units = 2 if management["partial_r"] is not None else 1
    friction = costs.per_trade("MNQ", "baseline")
    baseline = costs.per_trade_points("MNQ", "baseline")
    stress = costs.per_trade_points("MNQ", "stress")
    for budget in (250, 300, 350, 400):
        feasible = units*(2.0*events.stop_dist+friction) <= budget
        eligible = Events(events.entry_idx[feasible], events.side[feasible],
                          events.stop_dist[feasible], events.flat_bar,
                          events.family, events.signal_config,
                          events.mechanism_state, events.years)
        metrics = evaluate(market, eligible, management,
                           baseline_cost_points=baseline,
                           stress_cost_points=stress,
                           shadow_baseline=shadow)[0]
        out[str(budget)] = {"minimum_integer_mnq_contracts": units,
                            "valid_events": int(len(events.entry_idx)),
                            "risk_floor_skips": int(np.count_nonzero(~feasible)),
                            "budget_eligible_events": int(np.count_nonzero(feasible)),
                            "executed_trades": int(metrics[0]),
                            "executed_over_valid": float(metrics[0]/len(events.entry_idx))
                            if len(events.entry_idx) else 0.0,
                            "net_r": float(metrics[1]),
                            "stress_net_r": float(metrics[2])}
    return out


def _detail_record(index, mm, market, cache, costs, shadow):
    spec = spec_at(int(index))
    config = {k: spec[k] for k in ("family", "lookback", "threshold", "direction",
                                    "session", "filters", "entry")}
    events = cache.events(config, spec["management"]["stop"])
    baseline = costs.per_trade_points("MNQ", "baseline")
    stress = costs.per_trade_points("MNQ", "stress")
    metrics, entry, exit_, net_r = evaluate(
        market, events, spec["management"],
        baseline_cost_points=baseline, stress_cost_points=stress,
        shadow_baseline=shadow, capture=True)
    expected = mm[index]
    check = _record(spec, metrics)
    if check.tobytes() != expected.tobytes():
        raise RuntimeError(f"V5.4 qualifier {index} failed exact first-pass reproduction")
    neighbors = core_neighbor_indices(spec)
    neighbor_stats = [{"row": j, "candidate_id": mm[j]["candidate_id"].decode(),
                       "net_r": float(mm[j]["net_r"]),
                       "stress_net_r": float(mm[j]["stress_net_r"])} for j in neighbors]
    support = sum(x["net_r"] > 0 and x["stress_net_r"] > 0 for x in neighbor_stats)
    return {"row": int(index), "candidate_id": id_for(spec), "spec": spec,
            "trades": int(metrics[0]), "net_r": float(metrics[1]),
            "stress_net_r": float(metrics[2]),
            "expectancy_r": float(metrics[3]),
            "profit_factor": float(metrics[4]) if np.isfinite(metrics[4]) else None,
            "max_drawdown_r": float(metrics[5]), "active_years": int(metrics[6]),
            "subperiod_net_r": [float(x) for x in metrics[7:10]],
            "subperiod_trades": [int(x) for x in metrics[10:13]],
            "matched_excess_r": float(metrics[13]),
            "core_neighbor_count": len(neighbors),
            "core_neighbor_positive_baseline_and_stress": support,
            "core_neighbor_positive_fraction": support/len(neighbors) if neighbors else None,
            "core_neighbors": neighbor_stats,
            "mnq_budget_coverage": _budget_coverage(market, events,
                                                     spec["management"], costs, shadow),
            "trade_entry_indices": entry.tolist(),
            "trade_exit_indices": exit_.tolist(),
            "trade_net_r": net_r.tolist()}


def finalize_qualifiers(mm, market, costs):
    if not DONE.exists():
        return
    qualifiers = np.load(QUALIFIERS)
    if FREEZE.exists() or SUMMARY.exists():
        if FREEZE.exists() and SUMMARY.exists():
            return
        raise RuntimeError("V5.4 discovery freeze/report is incomplete")
    if DETAIL_PROGRESS.exists():
        p = json.loads(DETAIL_PROGRESS.read_text(encoding="utf-8"))
        if p["qualifier_file_sha256"] != file_sha256(QUALIFIERS):
            raise RuntimeError("qualifier list changed during detail resume")
        if not DETAIL.exists() or DETAIL.stat().st_size < p["committed_bytes"]:
            raise RuntimeError("qualifier detail file lost committed bytes")
        with DETAIL.open("r+b") as f:
            f.truncate(p["committed_bytes"])
    else:
        if DETAIL.exists():
            raise RuntimeError("qualifier details exist without a checkpoint")
        p = {"kind": "V5_4_QUALIFIER_DETAIL_PROGRESS", "completed": 0,
             "committed_bytes": 0,
             "qualifier_file_sha256": file_sha256(QUALIFIERS)}
        _atomic_json(DETAIL_PROGRESS, p)
    cache = EventCache(market)
    baseline = costs.per_trade_points("MNQ", "baseline")
    shadow = _shadow_clock_baseline(market, cache.context.stop, baseline)
    with DETAIL.open("ab") as f:
        for k in range(p["completed"], len(qualifiers)):
            record = _detail_record(int(qualifiers[k]), mm, market, cache, costs, shadow)
            raw = (json.dumps(record, sort_keys=True, allow_nan=False)+"\n").encode("utf-8")
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
            p.update(completed=k+1, committed_bytes=f.tell(),
                     last_record_sha256=sha256(raw).hexdigest())
            _atomic_json(DETAIL_PROGRESS, p)
            if (k+1) % 100 == 0:
                print(f"V5.4 detailed {k+1:,}/{len(qualifiers):,} qualifiers", flush=True)
    if p["completed"] != len(qualifiers):
        return
    SUMMARY.write_text(
        "# V5.4 broad DEVELOPMENT/DISCOVERY result\n\n"
        f"Evaluated all {len(mm):,} frozen unique specifications across all 30 original families. "
        f"{len(qualifiers):,} met the frozen five-part economic screen; every one was "
        "rerun exactly and advanced without rank or correlation deletion. "
        "This period is development data, not confirmation.\n\n"
        "Complete compact results, all qualifier trades, neighborhood scores, "
        "and four-budget MNQ diagnostics are under `reports/v54/`.\n", encoding="utf-8")
    body = {"kind": "V5_4_BROAD_DISCOVERY_FREEZE", "status": "FROZEN",
            "prereg_sha256": file_sha256(ROOT/"V5_4_PREREGISTRATION_FREEZE.json"),
            "evaluated_specifications": len(mm),
            "qualifier_count": len(qualifiers),
            "no_top_n_cap": True,
            "files_sha256": {rel: file_sha256(ROOT/rel) for rel in (
                "reports/v54/first_pass.npy", "reports/v54/first_pass_complete.json",
                "reports/v54/qualifying_rows.npy",
                "reports/v54/qualifier_details.jsonl",
                "V5_4_DISCOVERY_REPORT.md")}}
    _atomic_json(FREEZE, {**body, "body_sha256": sha256_text(canonical_json(body))})


def main():
    ok, why = ready(ROOT)
    if not ok:
        raise RuntimeError(why)
    project = default_project()
    reads = ledger.data_reads(project.ledger_path)
    if any(x["result"] == ledger.ALLOWED and x["partition"] != "DISCOVERY"
           for x in reads):
        raise RuntimeError("2019+ was opened before V5.4 discovery")
    market = load_market("DISCOVERY", "2010-06-08", "2018-12-31",
                         purpose="V5_4_FROZEN_BROAD_DISCOVERY")
    costs = CostModel.from_project(project)
    mm, progress = first_pass(market, costs)
    finalize_first_pass(mm, progress)
    finalize_qualifiers(mm, market, costs)


if __name__ == "__main__":
    main()
