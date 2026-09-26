"""Restricted one-shot DISCOVERY nuisance calibration. No strategy evaluation.

The only market read is through load_view inside calibration_scope. Output is
limited to calendar/roll templates and unconditional OHLCV nuisance summaries.
No signed lagged return, conditional future return, or candidate result is made.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np

from quantlab5.isolation.calibration_gate import (FREEZE, calibration_scope,
                                                 close_calibration_scope)
from quantlab5.isolation import ledger
from quantlab5.isolation.load_view import load_view
from quantlab5.project import ROOT, default_project
from quantlab5.util.hashing import file_sha256

READS_MARKET_DATA = True
START, END = "2010-06-08", "2018-12-31"
COLUMNS = ["open", "high", "low", "close", "volume", "symbol"]
OUT = ROOT / "V5_DISCOVERY_NUISANCE_CALIBRATION.json"
CALENDAR = ROOT / "reports" / "V5_DISCOVERY_CALENDAR_TEMPLATE.npz"


def _by_clock(sm: np.ndarray, values: np.ndarray) -> dict[str, list]:
    order = np.argsort(sm, kind="stable")
    sorted_clock = sm[order]
    bounds = np.searchsorted(sorted_clock, np.arange(1381))
    median = np.zeros(1380)
    p90 = np.zeros(1380)
    zero = np.ones(1380)
    count = np.zeros(1380, np.int64)
    for clock in range(1380):
        v = values[order[bounds[clock]:bounds[clock+1]]]
        v = v[np.isfinite(v)]
        count[clock] = len(v)
        if len(v):
            median[clock] = np.median(v)
            p90[clock] = np.quantile(v, .9)
            zero[clock] = np.mean(v == 0)
    return {"count": count.tolist(), "median": median.tolist(),
            "p90": p90.tolist(), "zero_fraction": zero.tolist()}


def _lag_corr(x: np.ndarray, gid: np.ndarray, lag: int) -> float:
    ok = (gid[lag:] == gid[:-lag]) & np.isfinite(x[lag:]) & np.isfinite(x[:-lag])
    if np.count_nonzero(ok) < 3:
        return 0.0
    a, b = x[lag:][ok], x[:-lag][ok]
    return float(np.corrcoef(a, b)[0, 1]) if np.std(a) > 0 and np.std(b) > 0 else 0.0


def _summarize(md) -> tuple[dict, dict]:
    b = md.bars()
    o, h, l, c, v = (np.asarray(getattr(b, k), float) for k in ("o", "h", "l", "c", "v"))
    sm, day = np.asarray(b.sm, int), np.asarray(b.sday, int)
    symbols = md.frame["symbol"].astype(str).to_numpy()
    seg = np.cumsum(np.r_[True, symbols[1:] != symbols[:-1]]).astype(np.int32)
    body = np.abs(c-o)
    range_ = h-l
    wick = np.maximum(range_-body, 0) / 2
    gap = np.zeros(len(o))
    boundary = np.r_[True, (day[1:] != day[:-1]) | (seg[1:] != seg[:-1])]
    gap[1:] = np.abs(o[1:]-c[:-1])
    gap_samples = gap[boundary]
    gid = np.cumsum(boundary)
    summary = {
        "rows": int(b.n), "first_timestamp_ns": int(b.ts[0]),
        "last_timestamp_ns": int(b.ts[-1]), "median_price": float(np.median(c)),
        "body_abs_points_by_clock": _by_clock(sm, body),
        "range_points_by_clock": _by_clock(sm, range_),
        "wick_points_by_clock": _by_clock(sm, wick),
        "volume_by_clock": _by_clock(sm, v),
        "absolute_gap_points_quantiles": np.quantile(gap_samples, [0, .5, .9, .99, 1]).tolist(),
        "abs_body_log_lag_correlation": {str(k): _lag_corr(np.log1p(body), gid, k)
                                         for k in (1, 5, 30, 60, 390)},
        "volume_log_lag_correlation": {str(k): _lag_corr(np.log1p(v), gid, k)
                                       for k in (1, 5, 30, 60, 390)},
        "roll_session_days": np.unique(day[np.r_[False, seg[1:] != seg[:-1]]]).tolist(),
    }
    template = {"ts": np.asarray(b.ts, np.int64), "segment": seg}
    return summary, template


def _joint_sign_agreement(nq, es) -> dict:
    n, e = nq.bars(), es.bars()
    nt, et = np.asarray(n.ts), np.asarray(e.ts)
    pos = np.searchsorted(et, nt)
    valid = pos < len(et)
    valid[valid] &= et[pos[valid]] == nt[valid]
    ix = np.flatnonzero(valid)
    nb = np.sign(np.asarray(n.c)[ix] - np.asarray(n.o)[ix])
    eb = np.sign(np.asarray(e.c)[pos[ix]] - np.asarray(e.o)[pos[ix]])
    na = np.log1p(np.abs(np.asarray(n.c)[ix] - np.asarray(n.o)[ix]))
    ea = np.log1p(np.abs(np.asarray(e.c)[pos[ix]] - np.asarray(e.o)[pos[ix]]))
    both = (nb != 0) & (eb != 0)
    return {"same_sign_fraction": float(np.mean(nb[both] == eb[both])),
            "nonzero_joint_bars": int(np.count_nonzero(both)),
            "abs_body_log_correlation": float(np.corrcoef(na, ea)[0, 1])}


def main() -> None:
    project = default_project()
    if OUT.exists() or CALENDAR.exists():
        raise RuntimeError("nuisance calibration outputs already exist")
    with calibration_scope():
        opened = ledger.append(project.ledger_path, "CALIBRATION_NUISANCE_ACCESS_OPEN",
                               reason="one-shot pinned nuisance worker")
        nq = load_view("NQ", "DISCOVERY", START, END, COLUMNS, project=project,
                       purpose="CALIBRATION_NUISANCE_ACCESS")
        es = load_view("ES", "DISCOVERY", START, END, COLUMNS, project=project,
                       purpose="CALIBRATION_NUISANCE_ACCESS")
        nq_summary, nq_template = _summarize(nq)
        es_summary, es_template = _summarize(es)
        joint = _joint_sign_agreement(nq, es)
        np.savez_compressed(CALENDAR, nq_ts=nq_template["ts"], nq_segment=nq_template["segment"],
                            es_ts=es_template["ts"], es_segment=es_template["segment"])
        artifact = {
            "kind": "V5_DISCOVERY_NUISANCE_CALIBRATION", "status": "COMPLETE",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "worker_code_sha256": file_sha256(Path(__file__)),
            "precalibration_science_freeze_sha256": file_sha256(ROOT / FREEZE),
            "partition_sha256": {"NQ": nq.partition_sha256, "ES": es.partition_sha256},
            "access_ledger_sequences": [nq.ledger_seq, es.ledger_seq],
            "calibration_open_ledger_sequence": opened["seq"],
            "permitted_statistics_produced": ["calendar timestamps and segment masks",
                "time-of-day observation counts and unconditional absolute body/range/wick/volume quantiles",
                "absolute session-gap quantiles", "absolute-body and volume lag dependence",
                "contemporaneous NQ/ES sign and absolute-body dependence"],
            "preserved": ["calendar", "DST", "roll locations", "missing-minute patterns",
                          "time-of-day OHLCV magnitudes", "contemporaneous NQ/ES sign association"],
            "destroyed_in_generated_worlds": ["real price levels", "real return directions",
                                            "serial directional dependence", "direction-volume predictive alignment"],
            "exposed_to_main_research": ["nuisance summary", "calendar and segment template",
                                         "joint same-minute sign agreement"],
            "kept_hidden_inside_worker": ["raw OHLCV", "signed return sequence",
                                          "signed conditional/path statistics"],
            "calendar_template_sha256": file_sha256(CALENDAR),
            "null_world_seed_manifest": {
                "stage_a_reference": [1000, 1018],
                "adaptive_null_reference": [2000, 2499],
                "all_null_test": [3000, 3199],
                "nuisance_fit": [9001, 9002, 9003],
                "plants": "100000 + cell_index*1000 + replication; validation uses 500000 + discovery seed",
            },
            "NQ": nq_summary, "ES": es_summary, "joint": joint,
        }
        OUT.write_text(json.dumps(artifact, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        ledger.append(project.ledger_path, "CALIBRATION_NUISANCE_ACCESS_CLOSED",
                      reason="worker output hashes and nuisance artifact written",
                      artifact_sha256=file_sha256(OUT), calendar_sha256=file_sha256(CALENDAR))
        close_calibration_scope()


if __name__ == "__main__":
    main()
