"""Report whether OS-level data isolation is ACTIVE for the account running this script.

    python tools/check_isolation.py            (run as the research account)

For every sealed partition file in the vault and every raw full-history source file it
attempts to OPEN the file (no bytes are read). Isolation is ACTIVE only if Windows
denies every one of those opens AND the DISCOVERY partition still loads through
load_view. Output: provenance/ISOLATION_CHECK_<user>.json. Exit code 0 = active.
(Ported from QuantLabV4 tools/check_isolation.py; V5 also probes the earlier labs' vaults.)

This script never reads sealed data; it only tests whether the OS would allow it.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from quantlab5.isolation import ledger  # noqa: E402
from quantlab5.project import default_project  # noqa: E402


def _try_open(p: Path) -> str:
    try:
        with open(p, "rb"):
            return "OPENABLE"
    except PermissionError:
        return "DENIED"
    except FileNotFoundError:
        return "NOT_FOUND_OR_HIDDEN"
    except OSError as e:
        return f"ERROR:{e.__class__.__name__}"


def main() -> int:
    project = default_project()
    user = os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"
    reg = json.loads((ROOT / "config" / "partitions.json").read_text(encoding="utf-8"))["registry"]
    checks = {}
    for r in reg["partitions"]:
        if r["location"] == "vault":
            checks[f"vault:{r['instrument']}/{r['partition']}"] = _try_open(Path(r["path"]))
    for k, s in reg["sources"].items():
        checks[f"raw:{k}"] = _try_open(Path(s["path"]))
    checks["vault_manifest"] = _try_open(project.vault / "VAULT_MANIFEST.json")
    for d in project.paths.get("prior_lab_data") or ():
        for f in sorted(Path(d).rglob("*.parquet"))[:20] if Path(d).is_dir() else ():
            checks[f"prior_lab:{f}"] = _try_open(f)
    sealed_denied = all(v != "OPENABLE" for v in checks.values())
    try:
        from quantlab5.isolation.load_view import load_view
        md = load_view("NQ", "DISCOVERY", "2010-06-08", "2010-06-08", ["close"], project=project,
                       purpose="isolation check: discovery must remain readable")
        discovery_ok = len(md.frame) > 0
    except Exception as e:           # noqa: BLE001
        discovery_ok = False
        checks["discovery_error"] = repr(e)[:300]
    active = bool(sealed_denied and discovery_ok)
    out = {"checked_utc": datetime.now(timezone.utc).isoformat(), "user": user, "checks": checks,
           "sealed_and_raw_all_denied": sealed_denied, "discovery_readable": discovery_ok,
           "os_isolation_active_for_this_account": active}
    dst = ROOT / "provenance" / f"ISOLATION_CHECK_{user}.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, indent=1), encoding="utf-8")
    try:
        ledger.append(project.ledger_path, "ISOLATION_CHECK", ledger.INFO,
                      f"os isolation active for {user}: {active}", checks=checks)
    except Exception:                # noqa: BLE001
        pass
    for k, v in checks.items():
        print(f"  {k:45s} {v}")
    print(f"OS isolation ACTIVE for account '{user}': {active}")
    return 0 if active else 1


if __name__ == "__main__":
    raise SystemExit(main())
