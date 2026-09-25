"""s00 -- PRIVILEGED one-time bootstrap: vault, partitions, registry, provenance, stage.

    python research/s00_bootstrap.py

(Ported from QuantLabV4 research/s00_bootstrap.py. V5 changes: V5 partitions and vault; the vault must
lie outside the project; each source file must match the SHA-256 that V4 verified; each V5 partition
is cross-checked against the V4 registry by HASH and row count only -- V4's partition files are never
opened.)

Must run as the administrator (it reads the raw full-history files and writes the
vault). It refuses to run twice. It prints only row counts, session/timestamp
boundaries and hashes -- never prices, volumes or any statistic of them.

Steps
  1. create the vault outside the project, restricted by NTFS ACL to Administrators+SYSTEM
  2. initialise the stage state (BOOTSTRAP) and the hash-chained ledger
  3. stream-partition NQ and ES into DISCOVERY (project) + 3 sealed partitions (vault)
  4. write the registry (config/partitions.json) and a vault copy; provenance/SOURCE_DATA.json
  5. prepare the LIVE_FORWARD inbox (empty; no historical data)
  6. advance BOOTSTRAP -> DISCOVERY (verifies every partition hash)
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from quantlab5.bootstrap.partitioner import HISTORICAL, partition_instrument  # noqa: E402
from quantlab5.data.schema import check_arrow_schema  # noqa: E402
from quantlab5.isolation import ledger  # noqa: E402
from quantlab5.isolation.forward import ensure_layout  # noqa: E402
from quantlab5.isolation.manifests import make_read_only  # noqa: E402
from quantlab5.isolation.stage_gate import advance, current_stage, init_state  # noqa: E402
from quantlab5.project import default_project  # noqa: E402
from quantlab5.util.hashing import file_sha256  # noqa: E402

# The source files V4 verified (QuantLabV4 V4_BOOTSTRAP_REPORT.md and its registry).
V4_VERIFIED_SOURCE_SHA256 = {
    "NQ": "63b8f16dd1da0a35f2fdfdc9039686ffc8db0ada84333bfc7cd85f8f28d013e7",
    "ES": "4a5dcac73b45f8097164e1242447fb490e6b2d52b4012cbe1ee3890f2d76edb2",
}
V4_REGISTRY = ROOT.parent / "QuantLabV4" / "config" / "partitions.json"
V4_NAME = {"DISCOVERY": "DISCOVERY", "VALIDATION": "CONFIRMATION", "HISTORICAL_AUDIT_1": "FINAL_HISTORICAL_HOLDOUT",
           "HISTORICAL_AUDIT_2": "SEALED_2026_AUDIT"}


def harden_vault(vault: Path) -> dict:
    """Remove inherited ACEs; grant only BUILTIN\\Administrators and SYSTEM (full control)."""
    cmd = ["icacls", str(vault), "/inheritance:r", "/grant:r", "*S-1-5-32-544:(OI)(CI)F", "*S-1-5-18:(OI)(CI)F"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    acl = subprocess.run(["icacls", str(vault)], capture_output=True, text=True).stdout
    return {"command": " ".join(cmd), "returncode": r.returncode, "acl_after": acl.strip().splitlines()}


def v4_crosscheck(records: list[dict]) -> list[dict]:
    """Compare each V5 partition with the V4 partition of the same period, by registry HASH / row count only."""
    v4 = {(r["instrument"], r["partition"]): r
          for r in json.loads(V4_REGISTRY.read_text(encoding="utf-8"))["registry"]["partitions"]}
    out = []
    for r in records:
        o = v4.get((r["instrument"], V4_NAME[r["partition"]]))
        out.append({"v5": f"{r['instrument']}/{r['partition']}", "v4": f"{r['instrument']}/{V4_NAME[r['partition']]}",
                    "v5_sha256": r["sha256"], "v4_sha256": o and o["sha256"],
                    "v5_rows": r["rows"], "v4_rows": o and o["rows"],
                    "v5_data_sessions": [r["first_data_session"], r["last_data_session"]],
                    "v4_data_sessions": o and [o["first_data_session"], o["last_data_session"]],
                    "identical_file": bool(o) and o["sha256"] == r["sha256"],
                    "same_rows": bool(o) and o["rows"] == r["rows"]})
    return out


def main() -> None:
    project = default_project()
    t0 = datetime.now(timezone.utc).isoformat()
    parts = project.partitions()
    if parts.get("registry"):
        raise SystemExit("registry already written; the bootstrap partitioner runs exactly once")
    vault = project.vault
    if vault.resolve() == project.root.resolve() or project.root.resolve() in vault.resolve().parents:
        raise SystemExit(f"{vault} is inside the project; the vault must be outside it")
    for inst, raw in project.raw_sources().items():
        if file_sha256(raw) != V4_VERIFIED_SOURCE_SHA256[inst]:
            raise SystemExit(f"{inst} source {raw} does not match the SHA-256 verified by V4; refusing")
    if vault.exists() and any(vault.iterdir()):
        raise SystemExit(f"{vault} exists and is not empty; refusing to reuse it")
    for rel in (project.root / "ledgers" / "DATA_ACCESS_LEDGER.jsonl", project.stage_state_path):
        if rel.exists():
            raise SystemExit(f"{rel} already exists")

    print(f"[s00] bootstrap start {t0}")
    vault.mkdir(parents=True, exist_ok=True)
    acl = harden_vault(vault)
    print(f"[s00] vault {vault} created; icacls returncode {acl['returncode']}")
    for name in HISTORICAL[1:]:             # VALIDATION, HISTORICAL_AUDIT_1, HISTORICAL_AUDIT_2
        (vault / name).mkdir(exist_ok=True)
    project.discovery_dir.mkdir(parents=True, exist_ok=True)

    init_state(project)
    ledger.append(project.ledger_path, "BOOTSTRAP_PARTITION", ledger.INFO,
                  "privileged bootstrap partitioner started (not a research read)",
                  raw_sources={k: str(v) for k, v in project.raw_sources().items()})

    sources, records = {}, []
    sess_cfg = project.sessions
    for inst, raw in sorted(project.raw_sources().items()):
        print(f"[s00] partitioning {inst} from {raw}")
        src, recs = partition_instrument(project, inst, raw, parts["definitions"],
                                         sess_cfg.get("complete_session_last_bar", "16:59"))
        sources[inst] = src
        records.extend(recs)
        print(f"[s00] {inst}: {src['rows_placed']:,} of {src['rows']:,} rows placed; excluded {src['excluded_rows']}; "
              f"last complete session {src['last_complete_session']} "
              f"(final session in file complete: {src['final_session_complete']})")

    schemas = {k: v["schema"] for k, v in sources.items()}
    consistent = len({json.dumps(s, sort_keys=True) for s in schemas.values()}) == 1
    xcheck = v4_crosscheck(records)
    for x in xcheck:
        print(f"[s00] {x['v5']:24s} vs V4 {x['v4']:28s} identical file: {x['identical_file']}  "
              f"same rows: {x['same_rows']}")
    registry = {"created_utc": datetime.now(timezone.utc).isoformat(), "tool": "research/s00_bootstrap.py",
                "vault": str(vault), "sources": sources, "partitions": records,
                "schemas_identical_across_instruments": consistent,
                "historical_audit_2_last_session": {k: v["last_complete_session"] for k, v in sources.items()},
                "joint_last_complete_session": min(v["last_complete_session"] for v in sources.values()),
                "v4_crosscheck": xcheck}
    parts["registry"] = registry
    (project.config_path("partitions.json")).write_text(json.dumps(parts, indent=1), encoding="utf-8")
    vm = vault / "VAULT_MANIFEST.json"
    vm.write_text(json.dumps(parts, indent=1), encoding="utf-8")
    make_read_only(vm)

    prov = {"bootstrap_started_utc": t0, "sources": sources, "vault_acl": acl,
            "v4_verified_source_sha256": V4_VERIFIED_SOURCE_SHA256,
            "schema_check": {k: check_arrow_schema(pq.ParquetFile(v["path"]).schema_arrow)
                             for k, v in sources.items()},
            "schemas_identical_across_instruments": consistent, "v4_crosscheck": xcheck}
    (project.root / "provenance" / "SOURCE_DATA.json").write_text(json.dumps(prov, indent=1), encoding="utf-8")

    ensure_layout(project)
    (project.forward_inbox / "README.txt").write_text(
        "QuantLabV5 LIVE_FORWARD inbox. Drop canonical-schema parquet files here. Nothing is accepted until a\n"
        "V5 FINAL_COHORT_FREEZE is pinned; only sessions starting at/after the freeze timestamp are accepted.\n",
        encoding="utf-8")
    ledger.append(project.ledger_path, "BOOTSTRAP_PARTITION", ledger.INFO, "partitions written",
                  partitions={f"{r['instrument']}/{r['partition']}": r["sha256"] for r in records},
                  v4_identical={x["v5"]: x["identical_file"] for x in xcheck})

    advance(project, "DISCOVERY")
    print(f"[s00] stage now {current_stage(project)}")
    print("[s00] done")


if __name__ == "__main__":
    main()
