"""Add compact per-candidate and operational detail to the completed report."""
from __future__ import annotations

from datetime import datetime, timezone
import json

import numpy as np

from quantlab5.isolation import ledger
from quantlab5.project import ROOT, default_project


REPORT = ROOT / "V5_4_COMPLETE_RESEARCH_REPORT.md"


def main():
    original = REPORT.read_text(encoding="utf-8")
    if "## Per-candidate historical evidence" in original:
        raise RuntimeError("complete report already enriched")
    cohort = json.loads((ROOT / "V5_4_SCIENTIFIC_COHORT_FREEZE.json").read_text(encoding="utf-8"))
    ids = cohort["candidate_ids"]
    audit = json.loads((ROOT / "reports/V5_4_HISTORICAL_AUDIT_RESULTS.json").read_text(encoding="utf-8"))
    validation = {}
    with (ROOT / "reports/V5_4_VALIDATION_RESULTS.jsonl").open("r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row["candidate_id"] in ids:
                validation[row["candidate_id"]] = row["validation"]
    discovery = {}
    with (ROOT / "reports/v54/qualifier_details.jsonl").open("r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row["candidate_id"] in ids:
                discovery[row["candidate_id"]] = row
    if set(validation) != set(ids) or set(discovery) != set(ids):
        raise RuntimeError("complete report omits a supported candidate")
    records = ledger.data_reads(default_project().ledger_path)
    first = min(datetime.fromisoformat(r["timestamp_utc"])
                for r in records if r["result"] == ledger.ALLOWED
                and r.get("purpose") == "V5_4_FROZEN_BROAD_DISCOVERY")
    freeze_created = datetime.fromtimestamp(
        (ROOT / "V5_4_DISCOVERY_FREEZE.json").stat().st_ctime, timezone.utc)
    runtime_seconds = (freeze_created - first).total_seconds()
    if runtime_seconds <= 0:
        raise RuntimeError("discovery timestamps are inconsistent")
    lines = ["", "## Per-candidate historical evidence", "",
             "The audit labels below use the separately frozen four-candidate Holm family. "
             "Positive net R alone does not mean `SUPPORTED`.", "",
             "| Candidate | Family | Management | Validation trades / net R / Holm p | "
             "2023–2025 trades / net R / Holm p / label | "
             "2026 trades / net R / Holm p / label |",
             "| --- | --- | --- | --- | --- | --- |"]
    for cid in ids:
        spec = cohort["specs"][cid]
        v = validation[cid]
        a1 = audit["audits"]["phase1"][cid]
        a2 = audit["audits"]["phase2"][cid]
        lines.append(
            f"| {cid} | {spec['family']} | {spec['management']['template']} | "
            f"{v['trades']} / {v['net_r']:.3f} / {v['holm_adjusted_p']:.4g} | "
            f"{a1['trades']} / {a1['net_r']:.3f} / {a1['holm_adjusted_p']:.4g} / {a1['classification']} | "
            f"{a2['trades']} / {a2['net_r']:.3f} / {a2['holm_adjusted_p']:.4g} / {a2['classification']} |")
    lines += ["", "Audit classifications: 2023–2025 had four `INCONCLUSIVE / UNDERPOWERED`; "
              "2026 had two `SUPPORTED` and two `INCONCLUSIVE / UNDERPOWERED`. "
              "No candidate was supported in both. Validation-supported management "
              "styles were three session runners and one break-even/trailing runner; "
              "no style survived both audits.", "",
              "## Candidate dependence and modeled risk budgets", "",
              "The four validation-supported candidates had no identical entry/exit trade "
              "fingerprints on validation. Pairwise correlation below uses full 2019–2022 "
              "daily net R, including zero-trade days.", "",
              "| Pair | Daily net-R correlation |", "| --- | ---: |"]
    for i in range(len(ids)):
        for j in range(i+1, len(ids)):
            x = np.asarray(validation[ids[i]]["daily_net_r"], float)
            y = np.asarray(validation[ids[j]]["daily_net_r"], float)
            corr = float(np.corrcoef(x, y)[0, 1])
            lines.append(f"| {ids[i]} / {ids[j]} | {corr:.3f} |")
    lines += ["", "The following counts are modeled integer-MNQ eligibility on "
              "discovery; each candidate needs at least one executed trade for the "
              "corresponding budget. The MNQ commission remains unvalidated.", "",
              "| Candidate | $250 trades | $300 trades | $350 trades | $400 trades |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for cid in ids:
        coverage = discovery[cid]["mnq_budget_coverage"]
        lines.append("| " + cid + " | " + " | ".join(
            str(coverage[str(b)]["executed_trades"]) for b in (250, 300, 350, 400)) + " |")
    lines += ["", "All four have modeled executions at each budget, but the study "
              "does not establish firm deployability or portfolio performance. "
              "There is no preregistered portfolio selection in V5.4.", "",
              "## Runtime and artifact scope", "",
              f"From first ledgered V5.4 DISCOVERY read to creation of the complete "
              f"discovery freeze: approximately {runtime_seconds/3600:.2f} hours "
              "(includes a resumable Windows checkpoint-lock interruption). "
              "The first-pass row store is approximately 1.66 GB; detailed discovery "
              "records are approximately 393 MB; validation results are approximately "
              "342 MB. The largest process peak observed during monitoring was about "
              "3.6 GB; this is an observed lower bound on true peak memory.", "",
              "Original V5 artifacts remain at their earlier immutable tags. "
              "LIVE_FORWARD remains unopened. The campaign ends with zero dual-audit "
              "supported candidates, which is a valid frozen-experiment result.", ""]
    REPORT.write_text(original.rstrip("\n") + "\n" + "\n".join(lines), encoding="utf-8")
    print("V5.4 complete report enriched with per-candidate evidence")


if __name__ == "__main__":
    main()
