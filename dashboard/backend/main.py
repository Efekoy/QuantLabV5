import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from dashboard.backend.db import connect, init
from dashboard.backend.git_status import git_status
from dashboard.backend.runtime import current_run, parse_events, demo

app = FastAPI(title="QuantLab Local Dashboard")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], allow_credentials=False,
                   allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["*"])


def rows(sql, args=()):
    with connect() as db:
        init(db)
        return [dict(row) for row in db.execute(sql, args)]


def one(sql, args=()):
    result = rows(sql, args)
    return result[0] if result else None


def visible(stage, protocol):
    if stage.startswith("audit") and not protocol.get("audits_revealed", False):
        return False
    if stage == "live_forward" and protocol.get("live_forward_sealed", True):
        return False
    return True


def event_log():
    frozen = [{"timestamp": None, "kind": r["kind"], "message": r["message"], "lab": r["lab_id"], "source": "FROZEN ARTIFACT"}
              for r in rows("SELECT lab_id,ts,kind,message FROM events ORDER BY id DESC LIMIT 50")]
    return (parse_events(100) + frozen)[:100]


def protocol_for(lab_id):
    record = one("SELECT state_json FROM protocols WHERE lab_id=?", (lab_id,))
    return json.loads(record["state_json"]) if record else {}


def mask_audits(item, protocol):
    if not protocol.get("audits_revealed", False):
        item["audit_1"] = "SEALED" if item.get("audit_1") else None
        item["audit_2"] = "SEALED" if item.get("audit_2") else None
    return item


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/labs")
def labs():
    return rows("SELECT * FROM labs ORDER BY CASE id WHEN 'v2' THEN 1 WHEN 'v3' THEN 2 WHEN 'v4' THEN 3 WHEN 'v5' THEN 4 WHEN 'v5.4' THEN 5 WHEN 'v6' THEN 6 ELSE 7 END,id")


@app.get("/api/labs/{lab_id}/overview")
def overview(lab_id: str):
    lab = one("SELECT * FROM labs WHERE id=?", (lab_id,))
    if not lab:
        raise HTTPException(404, "Lab not imported")
    run = one("SELECT * FROM runs WHERE lab_id=? ORDER BY id DESC LIMIT 1", (lab_id,))
    supported = rows("SELECT id,family,direction,session,management,status,trades,net_r,pf,validation_p,audit_1,audit_2 FROM strategies WHERE lab_id=? AND status='SUPPORTED' ORDER BY family,id", (lab_id,))
    protocol = protocol_for(lab_id)
    return {"lab": lab, "run": run, "supported": [mask_audits(x, protocol) for x in supported] if protocol.get("stage_frozen", False) else [],
            "class_counts": rows("SELECT status,count(*) AS count FROM strategies WHERE lab_id=? GROUP BY status", (lab_id,)) if protocol.get("stage_frozen", False) else []}


SORTS = {"id": "s.id", "family": "s.family", "status": "s.status", "direction": "s.direction", "session": "s.session",
         "trades": "s.trades", "net_r": "s.net_r", "pf": "s.pf", "expectancy_r": "s.expectancy_r",
         "max_dd_r": "s.max_dd_r", "validation_p": "s.validation_p"}


@app.get("/api/labs/{lab_id}/strategies")
def strategies(lab_id: str, page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=200), search: str = "", family: str = "",
               status: str = "", management: str = "", collection: int | None = None, watchlist: bool = False,
               sort: str = "id", direction: str = "asc"):
    if not protocol_for(lab_id).get("stage_frozen", False):
        return {"total": 0, "page": page, "size": size, "items": []}
    where = ["s.lab_id=?"]
    args = [lab_id]
    if search:
        where.append("(s.id LIKE ? OR s.family LIKE ?)")
        args += [f"%{search}%", f"%{search}%"]
    for column, value in (("family", family), ("status", status), ("management", management)):
        if value:
            where.append(f"s.{column}=?")
            args.append(value)
    if collection is not None:
        where.append("EXISTS(SELECT 1 FROM collection_members cm WHERE cm.strategy_id=s.id AND cm.collection_id=?)")
        args.append(collection)
    if watchlist:
        where.append("EXISTS(SELECT 1 FROM collection_members cm JOIN collections c ON c.id=cm.collection_id WHERE cm.strategy_id=s.id AND c.name='Watchlist')")
    clause = " AND ".join(where)
    order = SORTS.get(sort, "s.id") + (" DESC" if direction.lower() == "desc" else " ASC")
    with connect() as db:
        total = db.execute(f"SELECT count(*) FROM strategies s WHERE {clause}", args).fetchone()[0]
        data = [dict(r) for r in db.execute(f"""SELECT s.id,s.family,s.direction,s.session,s.management,s.stage,s.status,s.trades,s.net_r,s.pf,
          s.expectancy_r,s.max_dd_r,s.stress_r,s.validation_p,s.audit_1,s.audit_2,
          EXISTS(SELECT 1 FROM collection_members cm JOIN collections c ON c.id=cm.collection_id WHERE cm.strategy_id=s.id AND c.name='Watchlist') AS watched
          FROM strategies s WHERE {clause} ORDER BY {order},s.id LIMIT ? OFFSET ?""", (*args, size, (page - 1) * size))]
    protocol = protocol_for(lab_id)
    return {"total": total, "page": page, "size": size, "items": [mask_audits(x, protocol) for x in data]}


@app.get("/api/strategies/{strategy_id}")
def strategy(strategy_id: str):
    row = one("SELECT * FROM strategies WHERE id=?", (strategy_id,))
    if not row:
        raise HTTPException(404, "Strategy not found")
    protocol = protocol_for(row["lab_id"])
    if not protocol.get("stage_frozen", False):
        raise HTTPException(403, "Strategy results sealed until stage freeze")
    mask_audits(row, protocol)
    for key in ("spec_json", "discovery_json", "validation_json"):
        row[key.removesuffix("_json")] = json.loads(row.pop(key))
    stage_rows = rows("SELECT stage,status,metrics_json FROM stage_results WHERE strategy_id=?", (strategy_id,))
    row["stages"] = {r["stage"]: {"status": r["status"], "metrics": json.loads(r["metrics_json"])} if visible(r["stage"], protocol)
                     else {"status": "SEALED", "metrics": None} for r in stage_rows}
    row["protocol"] = protocol
    row["collections"] = rows("SELECT c.id,c.name FROM collections c JOIN collection_members m ON c.id=m.collection_id WHERE m.strategy_id=? ORDER BY c.name", (strategy_id,))
    row["note"] = (one("SELECT body FROM notes WHERE strategy_id=?", (strategy_id,)) or {}).get("body", "")
    row["related"] = rows("SELECT r.related_id,r.kind,r.value,s.family,s.management FROM relationships r JOIN strategies s ON s.id=r.related_id WHERE r.strategy_id=?", (strategy_id,))
    return row


@app.get("/api/strategies/{strategy_id}/equity")
def equity(strategy_id: str, stage: str):
    strategy_row = one("SELECT lab_id FROM strategies WHERE id=?", (strategy_id,))
    if not strategy_row:
        raise HTTPException(404, "Strategy not found")
    protocol = protocol_for(strategy_row["lab_id"])
    if not protocol.get("stage_frozen", False):
        return {"sealed": True, "points": []}
    if not visible(stage, protocol):
        return {"sealed": True, "points": []}
    return {"sealed": False, "points": rows("SELECT point_index AS x,cumulative_r AS r,drawdown_r AS dd FROM equity_points WHERE strategy_id=? AND stage=? ORDER BY point_index", (strategy_id, stage))}


@app.get("/api/collections")
def collections():
    return rows("SELECT c.id,c.name,count(m.strategy_id) AS count FROM collections c LEFT JOIN collection_members m ON c.id=m.collection_id GROUP BY c.id ORDER BY c.name")


class CollectionIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)


@app.post("/api/collections")
def create_collection(body: CollectionIn):
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Name required")
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO collections(name) VALUES (?)", (name,))
        db.commit()
        return dict(db.execute("SELECT id,name FROM collections WHERE name=?", (name,)).fetchone())


@app.put("/api/collections/{collection_id}/members/{strategy_id}")
def add_member(collection_id: int, strategy_id: str):
    with connect() as db:
        if not db.execute("SELECT 1 FROM collections WHERE id=?", (collection_id,)).fetchone() or not db.execute("SELECT 1 FROM strategies WHERE id=?", (strategy_id,)).fetchone():
            raise HTTPException(404)
        db.execute("INSERT OR IGNORE INTO collection_members VALUES (?,?)", (collection_id, strategy_id))
        db.commit()
    return {"ok": True}


@app.delete("/api/collections/{collection_id}/members/{strategy_id}")
def remove_member(collection_id: int, strategy_id: str):
    with connect() as db:
        db.execute("DELETE FROM collection_members WHERE collection_id=? AND strategy_id=?", (collection_id, strategy_id))
        db.commit()
    return {"ok": True}


class NoteIn(BaseModel):
    body: str = Field(max_length=20000)


@app.put("/api/strategies/{strategy_id}/note")
def put_note(strategy_id: str, body: NoteIn):
    with connect() as db:
        if not db.execute("SELECT 1 FROM strategies WHERE id=?", (strategy_id,)).fetchone():
            raise HTTPException(404)
        db.execute("INSERT INTO notes(strategy_id,body) VALUES (?,?) ON CONFLICT(strategy_id) DO UPDATE SET body=excluded.body,updated_at=CURRENT_TIMESTAMP", (strategy_id, body.body))
        db.commit()
    return {"ok": True}


@app.get("/api/runs")
def runs():
    return rows("SELECT * FROM runs ORDER BY id DESC")


@app.get("/api/activity")
def activity():
    return event_log()


@app.get("/api/git")
def git():
    return git_status()


@app.get("/api/runtime")
def runtime():
    return demo.state() or current_run()


@app.post("/api/demo/start")
def start_demo(duration: int = Query(45, ge=5, le=600)):
    demo.start(duration)
    return demo.state()


@app.post("/api/demo/stop")
def stop_demo():
    demo.stop()
    return {"ok": True}


@app.get("/api/stream")
async def stream():
    async def updates():
        last = ""
        while True:
            payload = json.dumps({"run": demo.state() or current_run(), "events": event_log()[:20]}, sort_keys=True)
            if payload != last:
                yield f"data: {payload}\n\n"
                last = payload
            await asyncio.sleep(2)
    return StreamingResponse(updates(), media_type="text/event-stream")
