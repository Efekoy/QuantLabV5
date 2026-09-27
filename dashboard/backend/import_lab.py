import argparse
import json
import math
from datetime import datetime
from dashboard.adapters.v54 import V54Adapter, ROOT, rows
from dashboard.backend.db import connect, init


def compact(metrics):
    return {k: v for k, v in metrics.items() if not isinstance(v, list)}


def write_curve(db, candidate_id, stage, returns):
    db.execute("DELETE FROM equity_points WHERE strategy_id=? AND stage=?", (candidate_id, stage))
    cumulative = peak = 0.0
    points = []
    for index, value in enumerate(returns):
        cumulative += value
        peak = max(peak, cumulative)
        if value or index == 0 or index == len(returns) - 1:
            points.append((candidate_id, stage, index, cumulative, peak - cumulative))
    db.executemany("INSERT INTO equity_points VALUES (?,?,?,?,?)", points)


def import_v54():
    adapter = V54Adapter()
    meta, run, protocol = adapter.get_lab_metadata(), adapter.get_run_status(), adapter.get_protocol_state()
    audits = adapter.get_stage_results
    cohort = set(json.loads((ROOT / "V5_4_SCIENTIFIC_COHORT_FREEZE.json").read_text())["candidate_ids"])
    db = connect()
    init(db)
    db.execute("INSERT OR REPLACE INTO labs VALUES (?,?,?,?,?,?,?,?,?,?,?)", tuple(meta.values()))
    db.execute("INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?,?,?,?)", tuple(run.values()))
    db.execute("INSERT OR REPLACE INTO protocols VALUES (?,?)", (adapter.id, json.dumps(protocol)))
    count = 0
    cohort_daily = {}
    for line, record in enumerate(adapter.get_strategies(), 1):
        spec, disc, val = record["spec"], record["discovery"], record["validation"]
        cid = record["candidate_id"]
        audit = audits(cid) if cid in cohort else {}
        db.execute("""INSERT OR REPLACE INTO strategies VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                   (cid, adapter.id, spec["family"], spec["direction"], spec["session"], spec["management"]["template"],
                    "VALIDATION", val["classification"], val.get("trades"), val.get("net_r"), val.get("profit_factor"),
                    val.get("expectancy_r"), val.get("max_drawdown_r"), val.get("stress_net_r"), val.get("holm_adjusted_p"),
                    (audit.get("audit_1") or {}).get("classification"), (audit.get("audit_2") or {}).get("classification"),
                    json.dumps(spec), json.dumps(disc), json.dumps(compact(val)), line))
        if cid in cohort:
            cohort_daily[cid] = val.get("daily_net_r", [])
            write_curve(db, cid, "validation", val.get("daily_net_r", []))
            db.execute("INSERT OR REPLACE INTO stage_results VALUES (?,?,?,?,?)",
                       (cid, "validation", val["classification"], json.dumps(compact(val)), "reports/V5_4_VALIDATION_RESULTS.jsonl"))
            for stage, result in audit.items():
                if result:
                    db.execute("INSERT OR REPLACE INTO stage_results VALUES (?,?,?,?,?)",
                               (cid, stage, result["classification"], json.dumps(result), "reports/V5_4_HISTORICAL_AUDIT_RESULTS.json"))
        count += 1
        if count % 1000 == 0:
            db.commit()
    for stage, path in (("audit_1", "reports/v54/phase1_sealed.jsonl"), ("audit_2", "reports/v54/phase2_sealed.jsonl")):
        for result in rows(path):
            if result["candidate_id"] in cohort:
                write_curve(db, result["candidate_id"], stage, result["daily_net_r"])
    for result in rows("reports/v54/qualifier_details.jsonl"):
        if result["candidate_id"] in cohort:
            write_curve(db, result["candidate_id"], "discovery", result["trade_net_r"])
    for left, a in cohort_daily.items():
        for right, b in cohort_daily.items():
            if left == right or len(a) != len(b) or not a:
                continue
            ma, mb = sum(a) / len(a), sum(b) / len(b)
            numerator = sum((x - ma) * (y - mb) for x, y in zip(a, b))
            denominator = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
            correlation = numerator / denominator if denominator else None
            db.execute("INSERT OR REPLACE INTO relationships VALUES (?,?,?,?)", (left, right, "validation_daily_r_correlation", correlation))
    for relative, kind, message in (
        ("V5_4_DISCOVERY_FREEZE.json", "discovery_frozen", "32,423 discovery qualifiers frozen"),
        ("V5_4_VALIDATION_FREEZE.json", "validation_frozen", "Four validation-supported candidates frozen"),
        ("V5_4_AUDIT_1_REPORT_FREEZE.json", "audit_sealed", "Historical audit 1 sealed"),
        ("V5_4_AUDIT_2_REPORT_FREEZE.json", "audit_sealed", "Historical audit 2 sealed"),
        ("V5_4_COMPLETE_RESEARCH_FREEZE.json", "research_complete", "Dual-audit supported: zero; live forward sealed"),
    ):
        path = ROOT / relative
        timestamp = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
        db.execute("INSERT OR REPLACE INTO events(lab_id,ts,kind,message,source) VALUES (?,?,?,?,?)",
                   (adapter.id, timestamp, kind, message, relative))
    db.commit()
    db.close()
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lab", required=True)
    args = parser.parse_args()
    if args.lab.lower() not in ("v5.4", "v54"):
        parser.error("Registered import adapters: v5.4")
    print(f"Imported {import_v54():,} V5.4 strategies")


if __name__ == "__main__":
    main()
