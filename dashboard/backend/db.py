import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.getenv("QUANTLAB_DASHBOARD_DB", Path(__file__).resolve().parents[1] / "database" / "dashboard.sqlite3"))


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS labs(id TEXT PRIMARY KEY,name TEXT,version TEXT,root_path TEXT,status TEXT,current_stage TEXT,searched INTEGER,discovery INTEGER,supported INTEGER,dual_supported INTEGER,live_forward_sealed INTEGER);
    CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,lab_id TEXT,name TEXT,stage TEXT,status TEXT,evaluated INTEGER,total INTEGER,checkpoint INTEGER,source TEXT);
    CREATE TABLE IF NOT EXISTS strategies(id TEXT PRIMARY KEY,lab_id TEXT,family TEXT,direction TEXT,session TEXT,management TEXT,stage TEXT,status TEXT,trades INTEGER,net_r REAL,pf REAL,expectancy_r REAL,max_dd_r REAL,stress_r REAL,validation_p REAL,audit_1 TEXT,audit_2 TEXT,spec_json TEXT,discovery_json TEXT,validation_json TEXT,source_line INTEGER);
    CREATE INDEX IF NOT EXISTS idx_strategy_lab_status ON strategies(lab_id,status);
    CREATE INDEX IF NOT EXISTS idx_strategy_family ON strategies(lab_id,family);
    CREATE INDEX IF NOT EXISTS idx_strategy_net ON strategies(lab_id,net_r);
    CREATE TABLE IF NOT EXISTS stage_results(strategy_id TEXT,stage TEXT,status TEXT,metrics_json TEXT,source TEXT,PRIMARY KEY(strategy_id,stage));
    CREATE TABLE IF NOT EXISTS equity_points(strategy_id TEXT,stage TEXT,point_index INTEGER,cumulative_r REAL,drawdown_r REAL,PRIMARY KEY(strategy_id,stage,point_index));
    CREATE TABLE IF NOT EXISTS relationships(strategy_id TEXT,related_id TEXT,kind TEXT,value REAL,PRIMARY KEY(strategy_id,related_id,kind));
    CREATE TABLE IF NOT EXISTS collections(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS collection_members(collection_id INTEGER,strategy_id TEXT,PRIMARY KEY(collection_id,strategy_id),FOREIGN KEY(collection_id) REFERENCES collections(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS notes(strategy_id TEXT PRIMARY KEY,body TEXT NOT NULL,updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,lab_id TEXT,ts TEXT,kind TEXT,message TEXT,source TEXT UNIQUE);
    CREATE TABLE IF NOT EXISTS checkpoints(id INTEGER PRIMARY KEY AUTOINCREMENT,run_id TEXT,ts TEXT,evaluated INTEGER,source TEXT UNIQUE);
    CREATE TABLE IF NOT EXISTS protocols(lab_id TEXT PRIMARY KEY,state_json TEXT);
    """)
    db.execute("INSERT OR IGNORE INTO collections(name) VALUES ('Watchlist')")
    for lab_id, name, version in (("v2", "V2", "V2"), ("v3", "V3", "V3"), ("v4", "V4", "V4"),
                                  ("v5", "V5", "V5"), ("v6", "V6 Future", "V6")):
        db.execute("""INSERT OR IGNORE INTO labs(id,name,version,status,current_stage)
                      VALUES (?,?,?,'NOT IMPORTED','AWAITING ADAPTER')""", (lab_id, name, version))
    db.commit()
