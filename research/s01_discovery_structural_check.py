"""s01 -- DISCOVERY-only STRUCTURAL data check (schema, timestamps, volume usability, rolls).

    python research/s01_discovery_structural_check.py

(Ported from QuantLabV4 research/s01_discovery_data_audit.py; V5 writes provenance/DISCOVERY_STRUCTURAL_CHECK.json.)

Reads ONLY the DISCOVERY partition, ONLY through load_view (every read is ledgered).
This is not the volume research audit. It answers "is the data structurally usable?"
and reports COUNTS only: no prices, no returns, no volume levels/distributions, no
time-of-day profiles, no charts.

Checks per instrument:
  * canonical schema present, dtypes as expected; NQ vs ES schemas identical
  * timestamps: sorted, unique, minute-aligned (load_view integrity check), UTC
  * volume: column exists, parses, integer dtype, no negatives, missing count,
    zero-volume row count
  * rolls: symbol-derived rolls == source roll_boundary flags; rolls only at session starts
  * source flags: duplicate_timestamp count
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from quantlab5.data.rolls import check_roll_boundary_flags  # noqa: E402
from quantlab5.data.schema import CANONICAL_SCHEMA  # noqa: E402
from quantlab5.data.volume_qc import schemas_consistent, volume_structure  # noqa: E402
from quantlab5.isolation.load_view import load_view  # noqa: E402
from quantlab5.isolation.stage_gate import current_stage  # noqa: E402
from quantlab5.project import default_project  # noqa: E402

EXPECTED_PANDAS = {"open": "float64", "high": "float64", "low": "float64", "close": "float64", "volume": "int64",
                   "instrument_id": "int64", "rtype": "int16", "publisher_id": "int16", "roll_boundary": "bool",
                   "duplicate_timestamp": "bool", "source_duplicate_count": "int32"}


def audit(project, inst: str) -> dict:
    md = load_view(inst, "DISCOVERY", project=project, purpose="s01 structural data audit (counts only)")
    df = md.frame
    dtypes = {c: str(df[c].dtype) for c in df.columns}
    bars = md.bars()                        # runs the full integrity check incl. volume
    ts = np.asarray(bars.ts)
    rep = {
        "rows": int(len(df)), "sessions": int(len(np.unique(bars.sday))),
        "ledger_seq": md.ledger_seq, "data_sha256": md.data_sha256,
        "columns_present": sorted(df.columns), "missing_canonical_columns":
            sorted(set(CANONICAL_SCHEMA) - set(df.columns)),
        "dtypes": dtypes,
        "dtype_mismatches": {c: dtypes.get(c) for c, t in EXPECTED_PANDAS.items() if dtypes.get(c) != t},
        "timestamps": {"tz": str(df["ts_event"].dt.tz), "strictly_increasing": bool((np.diff(ts) > 0).all()),
                       "minute_aligned": bool((ts % 60_000_000_000 == 0).all())},
        "volume": volume_structure(df),
        "rolls": check_roll_boundary_flags(bars.seg, df["roll_boundary"].to_numpy(bool), bars.sday),
        "source_duplicate_timestamp_rows": int(df["duplicate_timestamp"].sum()),
        "null_counts_by_column": {c: int(df[c].isna().sum()) for c in df.columns},
    }
    return rep


def main() -> None:
    project = default_project()
    stage = current_stage(project)
    if stage != "DISCOVERY":
        raise SystemExit(f"s01 runs at DISCOVERY only (stage is {stage})")
    out = {"created_utc": datetime.now(timezone.utc).isoformat(), "stage": stage, "partition": "DISCOVERY",
           "note": "structural counts only; no price or volume statistics", "instruments": {}}
    for inst in ("NQ", "ES"):
        out["instruments"][inst] = audit(project, inst)
    ok, probs = schemas_consistent({k: v["dtypes"] for k, v in out["instruments"].items()})
    out["nq_es_schema_consistent"] = ok
    out["nq_es_schema_problems"] = probs
    out["volume_checks_pass"] = all(v["volume"]["passes"] for v in out["instruments"].values())
    dst = project.root / "provenance" / "DISCOVERY_STRUCTURAL_CHECK.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, indent=1), encoding="utf-8")
    for inst, r in out["instruments"].items():
        v = r["volume"]
        print(f"[s01] {inst}: rows={r['rows']:,} sessions={r['sessions']} volume dtype={v['dtype']} "
              f"unparseable={v['unparseable']} negative={v['negative']} missing={v['missing']} "
              f"zero_volume_rows={v['zero_volume_rows']} non_integral={v['non_integral']} passes={v['passes']}; "
              f"rolls derived={r['rolls']['derived_rolls']} flagged={r['rolls']['flagged_rolls']} "
              f"match={r['rolls']['flag_matches_derived']} at_session_start={r['rolls']['rolls_only_at_session_start']}; "
              f"dtype mismatches={r['dtype_mismatches']}; dup-ts flags={r['source_duplicate_timestamp_rows']}")
    print(f"[s01] NQ/ES schema consistent: {ok} {probs}")
    print(f"[s01] wrote {dst}")


if __name__ == "__main__":
    main()
