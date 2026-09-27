import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".vendor"))

import pytest
from fastapi.testclient import TestClient

from dashboard.adapters.base import LabAdapter
from dashboard.adapters.v54 import V54Adapter
from dashboard.backend import db, runtime
from dashboard.backend.git_status import parse_porcelain
from dashboard.backend.import_lab import import_v54
from dashboard.backend.main import app, visible


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    original = db.DB_PATH
    db.DB_PATH = tmp_path_factory.mktemp("dashboard") / "test.sqlite3"
    try:
        assert import_v54() == 32423
        yield TestClient(app)
    finally:
        db.DB_PATH = original


def test_generic_adapter_contract():
    assert isinstance(V54Adapter(), LabAdapter)
    assert V54Adapter().get_protocol_state()["audits_revealed"] is True


def test_import_real_funnel_and_idempotence(client):
    overview = client.get("/api/labs/v5.4/overview").json()
    assert [overview["lab"][k] for k in ("searched", "discovery", "supported", "dual_supported")] == [14220360, 32423, 4, 0]
    assert len(overview["supported"]) == 4
    assert import_v54() == 32423
    assert client.get("/api/labs/v5.4/strategies?size=1").json()["total"] == 32423


def test_strategy_status_and_audits(client):
    supported = client.get("/api/labs/v5.4/strategies?status=SUPPORTED").json()
    assert supported["total"] == 4
    assert {x["audit_1"] for x in supported["items"]} == {"INCONCLUSIVE / UNDERPOWERED"}
    assert sum(x["audit_2"] == "SUPPORTED" for x in supported["items"]) == 2


def test_sealed_result_gate():
    assert not visible("audit_1", {"audits_revealed": False})
    assert not visible("live_forward", {"live_forward_sealed": True})
    assert visible("audit_2", {"audits_revealed": True})


def test_sealed_api_masks_audit_data(client):
    candidate = "Q54-cdb1d3d22908f8612e91b90f"
    with db.connect() as connection:
        original = connection.execute("SELECT state_json FROM protocols WHERE lab_id='v5.4'").fetchone()[0]
        connection.execute("UPDATE protocols SET state_json=? WHERE lab_id='v5.4'", (json.dumps({"stage_frozen": True, "audits_revealed": False, "live_forward_sealed": True}),))
        connection.commit()
    try:
        detail = client.get(f"/api/strategies/{candidate}").json()
        assert detail["audit_1"] == "SEALED"
        assert detail["stages"]["audit_1"]["metrics"] is None
        assert client.get(f"/api/strategies/{candidate}/equity?stage=audit_1").json()["sealed"]
    finally:
        with db.connect() as connection:
            connection.execute("UPDATE protocols SET state_json=? WHERE lab_id='v5.4'", (original,))
            connection.commit()


def test_large_table_queries(client):
    page = client.get("/api/labs/v5.4/strategies?page=2&size=50&sort=net_r&direction=desc").json()
    assert len(page["items"]) == 50
    assert page["total"] == 32423
    assert page["items"][0]["net_r"] >= page["items"][-1]["net_r"]
    assert client.get("/api/labs/v5.4/strategies?family=E09&search=Q54-").json()["total"] > 0


def test_equity_curve_loading(client):
    candidate = "Q54-cdb1d3d22908f8612e91b90f"
    detail = client.get(f"/api/strategies/{candidate}").json()
    assert detail["spec"]["family"] == "E09"
    assert detail["stages"]["audit_2"]["status"] == "SUPPORTED"
    for stage in ("discovery", "validation", "audit_1", "audit_2"):
        curve = client.get(f"/api/strategies/{candidate}/equity?stage={stage}").json()
        assert len(curve["points"]) > 20
    assert client.get(f"/api/strategies/{candidate}/equity?stage=live_forward").json()["sealed"]


def test_collections_and_notes(client):
    candidate = "Q54-cdb1d3d22908f8612e91b90f"
    collection = client.post("/api/collections", json={"name": "Test favorites"}).json()
    assert client.put(f"/api/collections/{collection['id']}/members/{candidate}").status_code == 200
    assert client.get(f"/api/labs/v5.4/strategies?collection={collection['id']}").json()["total"] == 1
    assert client.put(f"/api/strategies/{candidate}/note", json={"body": "Follow this candidate"}).status_code == 200
    assert client.get(f"/api/strategies/{candidate}").json()["note"] == "Follow this candidate"
    assert client.delete(f"/api/collections/{collection['id']}/members/{candidate}").status_code == 200
    assert client.get(f"/api/labs/v5.4/strategies?collection={collection['id']}").json()["total"] == 0


def test_run_event_parsing(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "RUNTIME", tmp_path)
    (tmp_path / "events.jsonl").write_text('{"timestamp":"2026-09-27T12:00:00","kind":"checkpoint","message":"100 complete"}\ninvalid\n', encoding="utf-8")
    assert runtime.parse_events()[0]["kind"] == "checkpoint"
    (tmp_path / "current_run.json").write_text(json.dumps({"lab": "V6", "stage": "DISCOVERY", "status": "RUNNING", "evaluated": 100, "total": 200, "secret": 1}), encoding="utf-8")
    assert runtime.current_run()["evaluated"] == 100
    assert "secret" not in runtime.current_run()


def test_git_status_parsing():
    assert parse_porcelain(" M quantlab6/search.py\n?? reports/progress.json\n D old.py") == [
        {"status": "M", "path": "quantlab6/search.py"},
        {"status": "??", "path": "reports/progress.json"},
        {"status": "D", "path": "old.py"},
    ]
