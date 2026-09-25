"""Hash-chained ledger: any edit, deletion, insertion, reordering or truncation is detected."""
import json

import pytest

from quantlab5.isolation import ledger


@pytest.fixture()
def lg(tmp_path):
    p = tmp_path / "L.jsonl"
    for i in range(6):
        ledger.append(p, "DATA_READ", ledger.ALLOWED if i % 2 else ledger.REFUSED, f"r{i}", instrument="NQ",
                      partition="DISCOVERY", columns=["close"], requested_start="2012-01-01",
                      requested_end="2012-12-31")
    return p


def _lines(p):
    return p.read_text(encoding="utf-8").splitlines()


def _write(p, lines):
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_intact_chain_verifies_and_has_required_fields(lg):
    ok, msg = ledger.verify(lg)
    assert ok, msg
    for i, r in enumerate(ledger.read(lg)):
        for k in ("timestamp_utc", "command", "pid", "user", "instrument", "partition", "columns",
                  "requested_start", "requested_end", "result", "reason", "previous_record_hash", "record_hash"):
            assert k in r
        assert r["seq"] == i
    recs = ledger.read(lg)
    assert recs[0]["previous_record_hash"] == ledger.GENESIS
    assert all(recs[i]["previous_record_hash"] == recs[i - 1]["record_hash"] for i in range(1, len(recs)))


def test_editing_an_old_record_breaks_verification(lg):
    lines = _lines(lg)
    rec = json.loads(lines[2])
    rec["result"] = "ALLOWED" if rec["result"] == "REFUSED" else "REFUSED"
    lines[2] = json.dumps(rec, sort_keys=True, separators=(",", ":"))
    _write(lg, lines)
    ok, msg = ledger.verify(lg)
    assert not ok and "line 3" in msg


def test_editing_and_rehashing_one_record_still_breaks_the_chain(lg):
    from quantlab5.isolation.ledger import _record_hash
    lines = _lines(lg)
    rec = json.loads(lines[1])
    rec["partition"] = "VALIDATION"
    rec["record_hash"] = _record_hash(rec)          # attacker recomputes this record's own hash
    lines[1] = json.dumps(rec)
    _write(lg, lines)
    ok, msg = ledger.verify(lg)
    assert not ok and "line 3" in msg                # the NEXT record no longer links to it


@pytest.mark.parametrize("mutation", ["delete", "insert", "swap", "truncate_middle"])
def test_structural_tampering_is_detected(lg, mutation):
    lines = _lines(lg)
    if mutation == "delete":
        del lines[3]
    elif mutation == "insert":
        lines.insert(2, lines[1])
    elif mutation == "swap":
        lines[2], lines[3] = lines[3], lines[2]
    else:
        lines = lines[:2] + lines[4:]
    _write(lg, lines)
    assert not ledger.verify(lg)[0]


def test_tail_truncation_is_detected_against_an_anchor(lg):
    anchor = ledger.head(lg)
    _write(lg, _lines(lg)[:-2])
    assert ledger.verify(lg)[0]                      # a clean prefix alone looks valid...
    ok, msg = ledger.verify(lg, anchor)              # ...but not against the anchor a freeze pinned
    assert not ok and "truncated" in msg


def test_append_refuses_when_the_last_record_was_edited(lg):
    lines = _lines(lg)
    rec = json.loads(lines[-1])
    rec["reason"] = "edited"
    lines[-1] = json.dumps(rec)
    _write(lg, lines)
    with pytest.raises(ledger.LedgerError):
        ledger.append(lg, "DATA_READ", ledger.ALLOWED, "x")


def test_unwritable_ledger_location_fails_loudly(tmp_path):
    with pytest.raises(ledger.LedgerError):
        ledger.append(tmp_path / "missing_dir" / "L.jsonl", "DATA_READ", ledger.ALLOWED, "x")


def test_concurrent_appends_keep_a_single_chain(tmp_path):
    import threading
    p = tmp_path / "L.jsonl"

    def work(k):
        for i in range(15):
            ledger.append(p, "DATA_READ", ledger.ALLOWED, f"t{k}-{i}")

    ts = [threading.Thread(target=work, args=(k,)) for k in range(4)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    ok, msg = ledger.verify(p)
    assert ok, msg
    assert len(ledger.read(p)) == 60
