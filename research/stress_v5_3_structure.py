"""Deterministic structural-only stress of complete V5.3 NQ/ES null markets."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os

import numpy as np

from quantlab5.project import ROOT
from quantlab5.util.hashing import file_sha256
from quantlab5.v5_3.range_null import RangeSeparatedNull

READS_MARKET_DATA = False
OUT = ROOT / "reports/V5_3_STRUCTURAL_STRESS.json"
SEEDS = tuple(range(1000)) + (1002,)


def _save(doc: dict) -> None:
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, OUT)


def _check(world: dict, tape: dict) -> float:
    minimum = float("inf")
    for inst, prefix in (("NQ", "nq"), ("ES", "es")):
        b = world[inst]
        if not np.array_equal(b.ts, tape[f"{prefix}_ts"]):
            raise ValueError(f"{inst} calendar differs from frozen tape")
        if not np.all(np.diff(b.ts) > 0):
            raise ValueError(f"{inst} timestamps are not monotonic")
        for name in ("o", "h", "l", "c", "v"):
            x = np.asarray(getattr(b, name))
            if not np.isfinite(x).all():
                raise ValueError(f"{inst} {name} contains nonfinite values")
        if np.min(b.v) < 0:
            raise ValueError(f"{inst} negative volume")
        if not (np.all(b.h >= np.maximum(b.o, b.c))
                and np.all(b.l <= np.minimum(b.o, b.c))
                and np.all(b.h >= b.l)):
            raise ValueError(f"{inst} OHLC ordering invalid")
        minimum = min(minimum, *(float(np.min(getattr(b, name)))
                                 for name in ("o", "h", "l", "c")))
    if minimum <= 0:
        raise ValueError("nonpositive OHLC value")
    return minimum


def main() -> None:
    artifact = ROOT / "V5_1_DISCOVERY_NUISANCE_CALIBRATION.json"
    tape = ROOT / "reports/V5_1_NUISANCE_TAPE.npz"
    fingerprints = {"generator_code_sha256": file_sha256(ROOT / "quantlab5/v5_3/range_null.py"),
                    "artifact_sha256": file_sha256(artifact), "tape_sha256": file_sha256(tape)}
    if OUT.exists():
        doc = json.loads(OUT.read_text(encoding="utf-8"))
        if doc.get("fingerprints") != fingerprints or doc.get("seed_policy") != "0..999 plus 1002":
            raise RuntimeError("structural stress checkpoint belongs to different inputs")
    else:
        doc = {"kind": "V5_3_STRUCTURAL_VALIDITY_STRESS", "status": "RUNNING",
               "fingerprints": fingerprints, "seed_policy": "0..999 plus 1002",
               "target_worlds": len(SEEDS), "completed_worlds": 0, "invalid_worlds": 0,
               "numerical_overflow_or_underflow_events": 0,
               "ohlc_invariant_failures": 0, "minimum_price": None, "failures": []}
    generator = RangeSeparatedNull(artifact, tape)
    # Generated timestamp arrays are checked against these immutable tape
    # arrays in every world, so their synchronization needs one full check.
    joint_count = int(np.intersect1d(generator.tape["nq_ts"],
                                      generator.tape["es_ts"]).size)
    if joint_count < 1_000_000:
        raise RuntimeError("frozen NQ/ES nuisance calendars are not synchronized")
    doc["joint_timestamp_count"] = joint_count
    for seed in SEEDS[doc["completed_worlds"]:]:
        try:
            with np.errstate(over="raise", under="raise", invalid="raise", divide="raise"):
                world = generator.generate_seed(seed)
                minimum = _check(world, generator.tape)
            doc["minimum_price"] = min(doc["minimum_price"], minimum) if doc["minimum_price"] is not None else minimum
        except (ValueError, FloatingPointError, OverflowError) as exc:
            doc["invalid_worlds"] += 1
            if isinstance(exc, (FloatingPointError, OverflowError)):
                doc["numerical_overflow_or_underflow_events"] += 1
            else:
                doc["ohlc_invariant_failures"] += 1
            doc["failures"].append({"seed": seed, "type": type(exc).__name__, "message": str(exc)})
        doc["completed_worlds"] += 1
        if doc["completed_worlds"] % 10 == 0 or doc["completed_worlds"] == len(SEEDS):
            _save(doc)
        if doc["invalid_worlds"]:
            doc["status"] = "FAIL_STRUCTURAL_VALIDITY"
            _save(doc)
            raise SystemExit("V5.3 generator produced a structurally invalid world")
    doc["status"] = "PASS"
    doc["completed_utc"] = datetime.now(timezone.utc).isoformat()
    _save(doc)


if __name__ == "__main__":
    main()
