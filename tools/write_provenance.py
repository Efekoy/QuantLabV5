"""Write/refresh provenance manifests (no market data is read). (Ported from QuantLabV4; V5: V4 copy record.)

    python tools/write_provenance.py

  provenance/ENVIRONMENT.json          Python, platform, package versions, pip-freeze hash
  provenance/CONFIG_HASHES.json        SHA-256 of every config file
  provenance/V4_COPIED_FILES_FINAL.json  final hashes of every file copied from V4 (+ modified-after-port flag)
  provenance/TEST_RESULTS.xml          JUnit XML of a full pytest run
  provenance/TEST_ENVIRONMENT.json     test counts/outcomes, pytest version, results hash
"""
from __future__ import annotations

import importlib.metadata as md
import json
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from quantlab5.project import CONFIG_FILES  # noqa: E402
from quantlab5.util.hashing import file_sha256, sha256_text  # noqa: E402

PKGS = ("numpy", "pandas", "pyarrow", "numba", "llvmlite", "PyYAML", "pytest")


def main() -> None:
    prov = ROOT / "provenance"
    now = datetime.now(timezone.utc).isoformat()
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout
    env = {"written_utc": now, "python": sys.version, "executable": sys.executable,
           "platform": platform.platform(), "machine": platform.machine(), "processor": platform.processor(),
           "packages": {p: md.version(p) for p in PKGS}, "pip_freeze_sha256": sha256_text(freeze),
           "pip_freeze": freeze.splitlines()}
    (prov / "ENVIRONMENT.json").write_text(json.dumps(env, indent=1), encoding="utf-8")

    cfg = {"written_utc": now, "files": {f"config/{f}": file_sha256(ROOT / "config" / f) for f in CONFIG_FILES}}
    (prov / "CONFIG_HASHES.json").write_text(json.dumps(cfg, indent=1), encoding="utf-8")

    v4 = json.loads((prov / "V4_COPIED_FILES.json").read_text(encoding="utf-8"))
    v4root = Path(v4["v4_root"])
    final = {"written_utc": now, "v4_root": v4["v4_root"], "v4_git_head": v4["v4_git_head"],
             "note": "source_sha256 = V4 original (committed, unmodified at v4_git_head); destination_sha256_at_copy = "
                     "byte-identical copy; destination_sha256_after_rename = after the mechanical quantlab4->quantlab5 "
                     "rename/re-homing; destination_sha256_final = now. changed_beyond_rename = V5 adaptation "
                     "(see docs/INHERITED_FROM_V4.md)", "files": []}
    for r in v4["files"]:
        dst = ROOT / r["destination"]
        fin = file_sha256(dst)
        final["files"].append({**r, "destination_sha256_final": fin,
                               "byte_identical_to_v4": fin == r["source_sha256"],
                               "changed_beyond_rename": fin != r["destination_sha256_after_rename"],
                               "source_still_matches": file_sha256(v4root / r["source"]) == r["source_sha256"]})
    final["summary"] = {"files": len(final["files"]),
                        "byte_identical_to_v4": sum(f["byte_identical_to_v4"] for f in final["files"]),
                        "rename_only": sum(not f["byte_identical_to_v4"] and not f["changed_beyond_rename"]
                                           for f in final["files"]),
                        "changed_beyond_rename": sum(f["changed_beyond_rename"] for f in final["files"])}
    (prov / "V4_COPIED_FILES_FINAL.json").write_text(json.dumps(final, indent=1), encoding="utf-8")

    xml = prov / "TEST_RESULTS.xml"
    r = subprocess.run([sys.executable, "-m", "pytest", f"--junitxml={xml}", "-o", "junit_suite_name=quantlab5"],
                       cwd=ROOT, capture_output=True, text=True)
    suite = ET.parse(xml).getroot()
    suite = suite if suite.tag == "testsuite" else suite.find("testsuite")
    cases = suite.findall("testcase")
    per_file: dict[str, int] = {}
    for c in cases:
        f = c.get("classname", "").split(".")[-1]
        per_file[f] = per_file.get(f, 0) + 1
    tenv = {"written_utc": now, "pytest": md.version("pytest"), "exit_code": r.returncode,
            "tests": int(suite.get("tests")), "failures": int(suite.get("failures")),
            "errors": int(suite.get("errors")), "skipped": int(suite.get("skipped")),
            "time_s": float(suite.get("time")), "tests_per_module": dict(sorted(per_file.items())),
            "junit_sha256": file_sha256(xml), "summary_line": r.stdout.strip().splitlines()[-1]}
    (prov / "TEST_ENVIRONMENT.json").write_text(json.dumps(tenv, indent=1), encoding="utf-8")
    print(json.dumps({k: tenv[k] for k in ("tests", "failures", "errors", "skipped", "exit_code", "summary_line")}))
    if r.returncode != 0:
        raise SystemExit(f"TEST SUITE FAILED: {tenv['summary_line']}")


if __name__ == "__main__":
    main()
