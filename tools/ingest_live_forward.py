"""Ingest genuinely post-freeze NQ/ES 1-minute data into the V5 LIVE_FORWARD vault. (Ported from QuantLabV4.)

    python tools/ingest_live_forward.py NQ path/to/nq_new_sessions.parquet
    python tools/ingest_live_forward.py ES path/to/es_new_sessions.parquet

The file must use the canonical schema (ts_event UTC, open/high/low/close, int volume, symbol, ...). Every row must
belong to a session that STARTED at or after the V5 FINAL_COHORT_FREEZE timestamp (not yet set); otherwise the
whole file is refused. Accepted files are hashed, made read-only, recorded in FORWARD_MANIFEST.jsonl and in the
data-access ledger. Tested by tests/test_forward.py.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from quantlab5.isolation.forward import ingest_forward  # noqa: E402
from quantlab5.project import default_project  # noqa: E402

if __name__ == "__main__":
    print(ingest_forward(default_project(), sys.argv[1], Path(sys.argv[2])))
