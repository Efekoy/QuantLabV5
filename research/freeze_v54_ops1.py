"""Document the WinError 5 checkpoint-replace retry without changing V5.4 science."""
from __future__ import annotations

import json

from quantlab5.isolation import ledger
from quantlab5.project import ROOT, default_project
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text
from quantlab5.v54.prereg_gate import ready


OUT = ROOT / "V5_4_OPERATIONAL_AMENDMENT_1.json"


def main():
    if OUT.exists():
        raise RuntimeError("operational amendment already exists")
    ok, reason = ready(ROOT)
    if not ok:
        raise RuntimeError(reason)
    progress = json.loads((ROOT / "reports/v54/progress.json").read_text(encoding="utf-8"))
    if progress["completed_rows"] != progress["completed_signal_configs"] * 198:
        raise RuntimeError("checkpoint group/row count inconsistent")
    project = default_project()
    ok, reason = ledger.verify(project.ledger_path)
    if not ok:
        raise RuntimeError(reason)
    body = {
        "kind": "V5_4_OPERATIONAL_AMENDMENT_1", "status": "FROZEN",
        "reason": "Transient WinError 5 replacing checkpoint progress.json on Windows",
        "change": "Retry the identical Path.replace operation; no scientific module or data rule changed",
        "preregistration_freeze_sha256": file_sha256(ROOT / "V5_4_PREREGISTRATION_FREEZE.json"),
        "frozen_runner_sha256": file_sha256(ROOT / "research/run_v54_discovery.py"),
        "wrapper_sha256": file_sha256(ROOT / "research/v54_windows_atomic_retry.py"),
        "amendment_builder_sha256": file_sha256(ROOT / "research/freeze_v54_ops1.py"),
        "last_complete_checkpoint_rows_before_amendment": progress["completed_rows"],
        "ledger_anchor_before_amendment": ledger.head(project.ledger_path),
        "no_outcome_inspection_for_change": True,
        "no_change_to_strategy_universe_inference_or_costs": True,
    }
    OUT.write_text(json.dumps({**body, "body_sha256": sha256_text(canonical_json(body))},
                              sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("V5.4 operational amendment 1 prepared")


if __name__ == "__main__":
    main()
