"""LIVE_FORWARD: no ingestion before the final cohort freeze; nothing from before the freeze, ever."""
from datetime import datetime, timezone

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from conftest import RAW_SCHEMA, canonical_raw_frame
from quantlab5.isolation.forward import ForwardRejected, accepted_records, ingest_forward
from quantlab5.isolation.load_view import AccessRefused, load_view
from quantlab5.synthetic.markets import synthetic_bars
from test_stage_gate import _to


def _file(tmp_path, name, start, end, seed=1):
    df = synthetic_bars(start, end, seed=seed, base=12000.0, symbol="NQ")
    f = tmp_path / name
    pq.write_table(pa.Table.from_pandas(canonical_raw_frame(df), schema=RAW_SCHEMA, preserve_index=False), f)
    return f


def _freeze_time(p):
    import json
    return json.loads(p.stage_state_path.read_text())["final_cohort_freeze_utc"]


def test_inbox_exists_but_nothing_is_accepted_before_final_cohort_freeze(fresh_project, tmp_path):
    from datetime import date
    p = fresh_project
    assert p.forward_inbox.is_dir()
    f = _file(tmp_path, "future.parquet", date(2031, 1, 6), date(2031, 1, 7))
    with pytest.raises(ForwardRejected, match="no FINAL_COHORT_FREEZE"):
        ingest_forward(p, "NQ", f)
    assert accepted_records(p) == []


def test_rows_from_sessions_before_the_freeze_are_rejected_whole(fresh_project, tmp_path):
    from datetime import date
    p = fresh_project
    _to(p, "FINAL_COHORT_FROZEN")
    # freeze time is "now"; a file of sessions in the past must be rejected entirely
    f = _file(tmp_path, "past.parquet", date(2021, 6, 1), date(2021, 6, 2))
    with pytest.raises(ForwardRejected, match="before the final cohort freeze"):
        ingest_forward(p, "NQ", f)
    # a session that STARTED before the freeze is rejected even if it ends after it
    now = pd.Timestamp(datetime.now(timezone.utc)).tz_convert("America/New_York")
    today = now.date()
    straddle = _file(tmp_path, "straddle.parquet", today - pd.Timedelta(days=3), today + pd.Timedelta(days=3))
    with pytest.raises(ForwardRejected):     # includes sessions that opened before the freeze
        ingest_forward(p, "NQ", straddle)
    assert accepted_records(p) == []


def test_post_freeze_sessions_are_accepted_and_readable_only_at_true_forward(fresh_project, tmp_path):
    from datetime import date
    p = fresh_project
    _to(p, "FINAL_COHORT_FROZEN")
    f1 = _file(tmp_path, "f1.parquet", date(2031, 1, 6), date(2031, 1, 7))
    info = ingest_forward(p, "NQ", f1)
    assert info["rows"] > 0 and info["first_session"] == "2031-01-06"
    with pytest.raises(ForwardRejected, match="overlaps"):
        ingest_forward(p, "NQ", f1)
    with pytest.raises(AccessRefused):
        load_view("NQ", "LIVE_FORWARD", project=p)     # FINAL_COHORT_FROZEN cannot read forward data
    _to(p, "LIVE_FORWARD")
    md = load_view("NQ", "LIVE_FORWARD", project=p)
    assert len(md.frame) == info["rows"]
    ts = pd.DatetimeIndex(md.frame["ts_event"]).as_unit("ns").asi8
    assert ts.min() >= pd.Timestamp(_freeze_time(p)).value


def test_tampered_accepted_forward_file_is_refused(fresh_project, tmp_path):
    import os
    import stat
    from datetime import date
    p = fresh_project
    _to(p, "FINAL_COHORT_FROZEN")
    ingest_forward(p, "NQ", _file(tmp_path, "f1.parquet", date(2031, 1, 6), date(2031, 1, 6)))
    _to(p, "LIVE_FORWARD")
    acc = next(p.forward_accepted.glob("NQ_LIVE_FORWARD_*.parquet"))
    os.chmod(acc, stat.S_IWRITE | stat.S_IREAD)
    with open(acc, "ab") as fh:
        fh.write(b"x")
    with pytest.raises(AccessRefused, match="altered"):
        load_view("NQ", "LIVE_FORWARD", project=p)
