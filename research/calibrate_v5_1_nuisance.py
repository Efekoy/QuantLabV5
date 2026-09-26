"""Restricted V5.1 worker: unsigned paired nuisance tape, no strategy calls."""
from __future__ import annotations

from datetime import datetime, timezone
import json

import numpy as np

from quantlab5.isolation import ledger
from quantlab5.isolation.load_view import load_view
from quantlab5.project import ROOT, default_project
from quantlab5.util.hashing import file_sha256
from quantlab5.v5_1.access import FREEZE, LEDGER, close, scope

READS_MARKET_DATA = True
OUT = ROOT / "V5_1_DISCOVERY_NUISANCE_CALIBRATION.json"
TAPE = ROOT / "reports/V5_1_NUISANCE_TAPE.npz"
START, END = "2010-06-08", "2018-12-31"
COLUMNS = ["open", "high", "low", "close", "volume", "symbol"]


def _pack(md, prefix: str) -> tuple[dict[str, np.ndarray], np.ndarray]:
    b = md.bars()
    o, h, l, c = (np.asarray(getattr(b, x), float) for x in ("o", "h", "l", "c"))
    previous = np.r_[o[0], c[:-1]]
    gap = o - previous
    body = c - o
    relation = np.sign(gap)*np.sign(body)
    symbols = md.frame["symbol"].astype(str).to_numpy()
    segment = np.cumsum(np.r_[True, symbols[1:] != symbols[:-1]]).astype(np.int32)
    arr = {
        f"{prefix}_ts": np.asarray(b.ts, np.int64),
        f"{prefix}_segment": segment,
        f"{prefix}_gap_ticks": np.rint(np.abs(gap)/.25).astype(np.int32),
        f"{prefix}_body_ticks": np.rint(np.abs(body)/.25).astype(np.int32),
        f"{prefix}_up_wick_ticks": np.rint((h-np.maximum(o,c))/.25).astype(np.int32),
        f"{prefix}_down_wick_ticks": np.rint((np.minimum(o,c)-l)/.25).astype(np.int32),
        f"{prefix}_volume": np.asarray(b.v, np.int32),
        f"{prefix}_gap_body_relation": relation.astype(np.int8),
    }
    return arr, np.sign(body).astype(np.int8)


def _joint_sign(nq_ts, es_ts, nq_sign, es_sign, nq_body, es_body) -> dict:
    pos = np.searchsorted(es_ts, nq_ts)
    valid = pos < len(es_ts)
    valid[valid] &= es_ts[pos[valid]] == nq_ts[valid]
    ni = np.flatnonzero(valid)
    ei = pos[ni]
    both = (nq_sign[ni] != 0) & (es_sign[ei] != 0)
    ni, ei = ni[both], ei[both]
    same = nq_sign[ni] == es_sign[ei]
    state = np.log1p(nq_body[ni].astype(float) + es_body[ei].astype(float))
    cuts = np.quantile(state, [.25, .5, .75])
    bucket = np.searchsorted(cuts, state, side="right")
    global_rate = float(np.mean(same))
    conditional = [float(np.mean(same[bucket == k])) if np.any(bucket == k)
                   else global_rate for k in range(4)]
    return {"same_sign_fraction": global_rate,
            "same_sign_by_joint_magnitude_quartile": conditional,
            "joint_magnitude_quartile_cuts": cuts.tolist(),
            "nonzero_joint_bars": int(len(ni))}


def main() -> None:
    if OUT.exists() or TAPE.exists():
        raise RuntimeError("V5.1 nuisance outputs already exist")
    project = default_project()
    with scope():
        opened = ledger.append(LEDGER, "V5_1_CALIBRATION_OPEN",
                               reason="pinned one-shot unsigned nuisance worker")
        views = {}
        for inst in ("NQ", "ES"):
            md = load_view(inst, "DISCOVERY", START, END, COLUMNS, project=project,
                           purpose="V5_1_CALIBRATION_NUISANCE_ACCESS")
            ledger.append(LEDGER, "DATA_READ", ledger.ALLOWED,
                          "V5_1_CALIBRATION_NUISANCE_ACCESS", instrument=inst,
                          partition="DISCOVERY", start=START, end=END,
                          columns=COLUMNS, rows=len(md.frame),
                          partition_sha256=md.partition_sha256,
                          data_sha256=md.data_sha256,
                          parent_v5_ledger_sequence=md.ledger_seq)
            views[inst] = md
        nq, nq_sign = _pack(views["NQ"], "nq")
        es, es_sign = _pack(views["ES"], "es")
        joint = _joint_sign(nq["nq_ts"], es["es_ts"], nq_sign, es_sign,
                            nq["nq_body_ticks"], es["es_body_ticks"])
        np.savez_compressed(TAPE, **nq, **es)
        artifact = {
            "kind": "V5_1_DISCOVERY_NUISANCE_CALIBRATION", "status": "COMPLETE",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "worker_code_sha256": file_sha256(__file__),
            "protocol_freeze_sha256": file_sha256(FREEZE),
            "v5_failed_archive_tag": "v5-calibration-failed",
            "partition_sha256": {k: v.partition_sha256 for k, v in views.items()},
            "median_price": {k: float(np.median(v.frame["close"].to_numpy(float)))
                             for k, v in views.items()},
            "tape_sha256": file_sha256(TAPE),
            "fresh_ledger_open_sequence": opened["seq"],
            "joint_sign": joint,
            "permitted_output": ["exact calendar and contract-segment masks",
                 "paired unsigned gap, body, wick and volume sequences",
                 "within-bar gap/body sign relation without absolute direction",
                 "contemporaneous NQ/ES sign agreement by unsigned magnitude state",
                 "instrument median price level"],
            "hidden": ["raw OHLCV prices", "absolute return signs",
                       "candidate outcomes and rankings"],
            "destroyed_by_null": ["historical absolute directional sign sequence",
                                  "serial and future-conditioned directional predictability"],
            "seed_policy": {"fidelity": [9101, 9102, 9103],
                            "stage_a_reference": [1000, 1018],
                            "adaptive_null_reference": [2000, 2499],
                            "all_null_test": [3000, 3199],
                            "plants": "100000 + cell_index*1000 + replication"},
        }
        OUT.write_text(json.dumps(artifact, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        ledger.append(LEDGER, "V5_1_CALIBRATION_CLOSED",
                      reason="unsigned tape and artifact hashed; direct access closed",
                      artifact_sha256=file_sha256(OUT), tape_sha256=file_sha256(TAPE))
        close()


if __name__ == "__main__":
    main()
