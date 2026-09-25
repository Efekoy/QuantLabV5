"""The single data-access API: stage authorisation, hashing, path safety, ledgering.

All on a synthetic project (real partitioner, real stage gate, temp vault)."""
import json
import os
import stat

import numpy as np
import pandas as pd
import pytest

from quantlab5.isolation import ledger
from quantlab5.isolation.load_view import AccessRefused, load_bars, load_view
from quantlab5.isolation.stage_gate import current_stage

SEALED = ("VALIDATION", "HISTORICAL_AUDIT_1", "HISTORICAL_AUDIT_2", "LIVE_FORWARD")


def _last(p):
    return ledger.read(p.ledger_path)[-1]


def test_project_starts_at_discovery(shared_project):
    assert current_stage(shared_project) == "DISCOVERY"


def test_discovery_read_is_allowed_and_ledgered_before_return(fresh_project):
    p = fresh_project
    n0 = len(ledger.read(p.ledger_path))
    md = load_view("NQ", "DISCOVERY", "2020-09-01", "2020-09-30", ["open", "close", "volume"], project=p)
    rec = _last(p)
    assert len(ledger.read(p.ledger_path)) == n0 + 1
    assert rec["event"] == "DATA_READ" and rec["result"] == "ALLOWED"
    assert rec["instrument"] == "NQ" and rec["partition"] == "DISCOVERY"
    assert rec["columns"] == ["open", "close", "volume"]
    assert rec["requested_start"] == "2020-09-01" and rec["requested_end"] == "2020-09-30"
    assert rec["rows"] == len(md.frame) and rec["data_sha256"] == md.data_sha256
    assert rec["seq"] == md.ledger_seq
    assert list(md.frame.columns) == ["ts_event", "open", "close", "volume"]
    ts = pd.DatetimeIndex(md.frame["ts_event"]).tz_convert("America/New_York")
    assert ts.min() >= pd.Timestamp("2020-08-31 18:00", tz="America/New_York")
    assert ts.max() < pd.Timestamp("2020-09-30 18:00", tz="America/New_York")
    assert ledger.verify(p.ledger_path)[0]


@pytest.mark.parametrize("part", SEALED)
def test_sealed_partitions_are_refused_and_the_refusal_is_ledgered(fresh_project, part):
    p = fresh_project
    with pytest.raises(AccessRefused):
        load_view("NQ", part, project=p)
    rec = _last(p)
    assert rec["event"] == "DATA_READ" and rec["result"] == "REFUSED" and rec["partition"] == part
    assert "DISCOVERY may not read" in rec["reason"]


@pytest.mark.parametrize("bad", [
    {"instrument": r"..\..\Quant\data\NQ\nq_continuous_front_1m.parquet", "partition": "DISCOVERY"},
    {"instrument": "NQ", "partition": r"C:\Users\Administrator\Desktop\Quant\data\NQ\nq_continuous_front_1m.parquet"},
    {"instrument": "NQ", "partition": "../vault/VALIDATION"},
    {"instrument": "NQ", "partition": "discovery"},
    {"instrument": "nq", "partition": "DISCOVERY"},
    {"instrument": "NQ", "partition": "DISCOVERY", "columns": ["close", "../secret"]},
    {"instrument": "NQ", "partition": "DISCOVERY", "columns": ["not_a_column"]},
    {"instrument": "NQ", "partition": "DISCOVERY", "start": "2020/09/01"},
])
def test_malformed_and_path_like_requests_are_refused(fresh_project, bad):
    p = fresh_project
    with pytest.raises(AccessRefused):
        load_view(project=p, **bad)
    assert _last(p)["result"] == "REFUSED"


def test_requests_outside_the_partition_range_are_refused(fresh_project):
    p = fresh_project
    with pytest.raises(AccessRefused, match="outside"):
        load_view("NQ", "DISCOVERY", "2020-10-01", "2020-11-15", project=p)   # reaches into VALIDATION
    with pytest.raises(AccessRefused, match="after end"):
        load_view("NQ", "DISCOVERY", "2020-10-01", "2020-09-01", project=p)


def test_registry_pointing_at_raw_source_is_refused(fresh_project):
    p = fresh_project
    cfg = p.config_path("partitions.json")
    doc = json.loads(cfg.read_text())
    rec = [r for r in doc["registry"]["partitions"] if r["instrument"] == "NQ" and r["partition"] == "DISCOVERY"][0]
    rec["path"] = str(p.raw_sources()["NQ"])
    cfg.write_text(json.dumps(doc))
    with pytest.raises(AccessRefused):
        load_view("NQ", "DISCOVERY", project=p)
    assert "registry changed" in _last(p)["reason"]   # the pinned registry hash catches the edit first


def test_tampered_partition_is_rejected(fresh_project):
    p = fresh_project
    f = p.discovery_dir / "NQ_DISCOVERY.parquet"
    os.chmod(f, stat.S_IWRITE | stat.S_IREAD)
    with open(f, "r+b") as fh:          # flip one byte in the middle of the file
        fh.seek(f.stat().st_size // 2)
        b = fh.read(1)
        fh.seek(-1, 1)
        fh.write(bytes([b[0] ^ 0xFF]))
    with pytest.raises(AccessRefused, match="SHA-256"):
        load_view("NQ", "DISCOVERY", project=p)
    assert _last(p)["result"] == "REFUSED"


def test_intentionally_corrupted_partition_is_rejected(fresh_project):
    """A partition replaced by a VALID parquet file with different contents (one volume changed)."""
    import pyarrow.parquet as pq
    p = fresh_project
    f = p.discovery_dir / "ES_DISCOVERY.parquet"
    tbl = pq.read_table(f).to_pandas()
    tbl.loc[100, "volume"] += 1
    os.chmod(f, stat.S_IWRITE | stat.S_IREAD)
    tbl.to_parquet(f, index=False)
    with pytest.raises(AccessRefused, match="SHA-256"):
        load_view("ES", "DISCOVERY", project=p)


def test_returned_data_is_a_safe_copy(fresh_project):
    p = fresh_project
    a = load_view("NQ", "DISCOVERY", "2020-09-01", "2020-09-02", project=p)
    a.frame.loc[:, "close"] = -1.0
    b = load_view("NQ", "DISCOVERY", "2020-09-01", "2020-09-02", project=p)
    assert (b.frame["close"] > 0).all()
    bars = b.bars()
    with pytest.raises(ValueError):
        bars.c[0] = 0.0                     # engine arrays are read-only


def test_volume_is_returned_as_first_class_column(shared_project):
    bars = load_bars("ES", "DISCOVERY", "2020-09-01", "2020-09-04", project=shared_project)
    assert bars.v.dtype == np.float64 and np.isfinite(bars.v).all() and bars.source == "real:DISCOVERY"


def test_stage_state_edit_is_detected_and_blocks_reads(fresh_project):
    p = fresh_project
    st = json.loads(p.stage_state_path.read_text())
    st["stage"] = "VALIDATION"
    p.stage_state_path.write_text(json.dumps(st))
    with pytest.raises(AccessRefused, match="stage state invalid"):
        load_view("NQ", "VALIDATION", project=p)


def test_stage_state_forged_with_valid_hash_is_caught_by_the_ledger(fresh_project):
    from quantlab5.isolation.stage_gate import _state_hash
    p = fresh_project
    st = json.loads(p.stage_state_path.read_text())
    st["stage"] = "VALIDATION"
    st["history"].append({"stage": "VALIDATION", "entered_utc": "x"})
    st["state_hash"] = _state_hash(st)
    p.stage_state_path.write_text(json.dumps(st))
    with pytest.raises(AccessRefused, match="ledger"):
        load_view("NQ", "VALIDATION", project=p)


def test_every_attempt_is_recorded(fresh_project):
    p = fresh_project
    before = len(ledger.data_reads(p.ledger_path))
    load_view("NQ", "DISCOVERY", "2020-09-01", "2020-09-01", project=p)
    for part in ("VALIDATION", "HISTORICAL_AUDIT_2"):
        with pytest.raises(AccessRefused):
            load_view("ES", part, project=p)
    reads = ledger.data_reads(p.ledger_path)[before:]
    assert [r["result"] for r in reads] == ["ALLOWED", "REFUSED", "REFUSED"]
    assert ledger.verify(p.ledger_path)[0]


def _bypass_pin(monkeypatch):
    """Simulate a compromised registry pin, to test the path defences behind it."""
    import quantlab5.isolation.load_view as lv
    monkeypatch.setattr(lv, "authorize", lambda project, partition: ("DISCOVERY", True, "test bypass"))


def _point(p, inst, part, new_path, new_sha=None):
    cfg = p.config_path("partitions.json")
    doc = json.loads(cfg.read_text())
    rec = [r for r in doc["registry"]["partitions"] if r["instrument"] == inst and r["partition"] == part][0]
    rec["path"] = str(new_path)
    if new_sha:
        rec["sha256"] = new_sha
    cfg.write_text(json.dumps(doc))


def test_raw_full_history_file_is_refused_even_if_registry_pin_is_bypassed(fresh_project, monkeypatch):
    from quantlab5.util.hashing import file_sha256
    p = fresh_project
    _bypass_pin(monkeypatch)
    raw = p.raw_sources()["NQ"]
    _point(p, "NQ", "DISCOVERY", raw, file_sha256(raw))
    with pytest.raises(AccessRefused, match="escapes|full-history|file name"):
        load_view("NQ", "DISCOVERY", project=p)


def test_registry_path_traversal_into_vault_is_refused(fresh_project, monkeypatch):
    p = fresh_project
    _bypass_pin(monkeypatch)
    target = p.discovery_dir / ".." / ".." / ".." / "vault" / "VALIDATION" / "NQ_VALIDATION.parquet"
    _point(p, "NQ", "DISCOVERY", target)
    with pytest.raises(AccessRefused, match="escapes"):
        load_view("NQ", "DISCOVERY", project=p)


def test_dtypes_come_from_arrow_schema_not_embedded_pandas_metadata(fresh_project):
    """Regression: the real NQ source embeds pandas metadata declaring roll_boundary as nullable
    'boolean' while ES does not; load_view must return identical canonical dtypes for both."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    p = fresh_project
    f = p.discovery_dir / "NQ_DISCOVERY.parquet"
    tbl = pq.read_table(f)
    df = tbl.to_pandas()
    df["roll_boundary"] = df["roll_boundary"].astype("boolean")
    os.chmod(f, stat.S_IWRITE | stat.S_IREAD)
    pq.write_table(pa.Table.from_pandas(df, schema=tbl.schema.remove_metadata(), preserve_index=False)
                   .replace_schema_metadata(pa.Table.from_pandas(df, preserve_index=False).schema.metadata), f)
    cfg = p.config_path("partitions.json")
    doc = json.loads(cfg.read_text())
    from quantlab5.util.hashing import file_sha256
    for r in doc["registry"]["partitions"]:
        if r["instrument"] == "NQ" and r["partition"] == "DISCOVERY":
            r["sha256"] = file_sha256(f)
    cfg.write_text(json.dumps(doc))
    import quantlab5.isolation.load_view as lv
    import pytest as _pt
    mp = _pt.MonkeyPatch()
    mp.setattr(lv, "authorize", lambda project, partition: ("DISCOVERY", True, "test bypass of registry pin"))
    try:
        nq = load_view("NQ", "DISCOVERY", "2020-09-01", "2020-09-02", project=p).frame
        es = load_view("ES", "DISCOVERY", "2020-09-01", "2020-09-02", project=p).frame
    finally:
        mp.undo()
    assert str(nq["roll_boundary"].dtype) == str(es["roll_boundary"].dtype) == "bool"
    assert {c: str(nq[c].dtype) for c in nq} == {c: str(es[c].dtype) for c in es}
