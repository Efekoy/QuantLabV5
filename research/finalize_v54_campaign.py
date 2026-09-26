"""Summarize the complete frozen V5.4 historical campaign without new reads."""
from __future__ import annotations

from collections import Counter
import json

import numpy as np

from quantlab5.isolation import ledger
from quantlab5.project import ROOT, default_project
from quantlab5.util.hashing import file_sha256
from quantlab5.v54.access import _frozen_file


OUT = ROOT / "V5_4_COMPLETE_RESEARCH_REPORT.md"


def _read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main():
    if OUT.exists():
        raise RuntimeError("V5.4 complete report already exists")
    for name, tag in (("V5_4_DISCOVERY_FREEZE.json", "v5.4-discovery"),
                      ("V5_4_VALIDATION_FREEZE.json", "v5.4-validation"),
                      ("V5_4_SCIENTIFIC_COHORT_FREEZE.json", "v5.4-validation"),
                      ("V5_4_HISTORICAL_AUDIT_MANIFEST.json", "v5.4-cohort"),
                      ("V5_4_AUDIT_1_REPORT_FREEZE.json", "v5.4-audit1"),
                      ("V5_4_AUDIT_2_REPORT_FREEZE.json", "v5.4-audit2")):
        ok, reason = _frozen_file(ROOT, name, tag)
        if not ok:
            raise RuntimeError(reason)
    project = default_project()
    ok, reason = ledger.verify(project.ledger_path)
    if not ok:
        raise RuntimeError(reason)
    inventory = _read("V5_4_SEARCH_UNIVERSE.json")
    first = _read("reports/v54/first_pass_complete.json")
    discovery = _read("V5_4_DISCOVERY_FREEZE.json")
    validation = _read("V5_4_VALIDATION_FREEZE.json")
    cohort = _read("V5_4_SCIENTIFIC_COHORT_FREEZE.json")
    both = _read("V5_4_BOTH_HISTORICAL_AUDITS_COMPLETE.json")
    audits = _read("reports/V5_4_HISTORICAL_AUDIT_RESULTS.json")
    if not (first["specifications_evaluated"] == discovery["evaluated_specifications"]
            == inventory["counts"]["final_unique_executable_specifications"]):
        raise RuntimeError("V5.4 full-universe count mismatch")
    if (first["qualifier_count"] != discovery["qualifier_count"]
            or validation["evaluated_count"] != discovery["qualifier_count"]
            or len(cohort["candidate_ids"]) != validation["supported_count"]
            or both["candidate_ids"] != cohort["candidate_ids"]
            or both["results_sha256"] != file_sha256(ROOT / "reports/V5_4_HISTORICAL_AUDIT_RESULTS.json")):
        raise RuntimeError("V5.4 phase count/cohort mismatch")
    families = Counter()
    budget = Counter()
    supported = set(cohort["candidate_ids"])
    detail = ROOT / "reports/v54/qualifier_details.jsonl"
    with detail.open("r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            families[row["spec"]["family"]] += 1
            if row["candidate_id"] in supported:
                for dollars, coverage in row["mnq_budget_coverage"].items():
                    if coverage["executed_trades"] > 0:
                        budget[dollars] += 1
    styles = Counter(cohort["specs"][cid]["management"]["template"]
                     for cid in both["dual_supported_ids"])
    validation_rows = {}
    with (ROOT / "reports/V5_4_VALIDATION_RESULTS.jsonl").open("r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row["candidate_id"] in supported:
                validation_rows[row["candidate_id"]] = row
    fingerprints = Counter()
    for row in validation_rows.values():
        v = row["validation"]
        fingerprint = (tuple(v["trade_entry_indices"]), tuple(v["trade_exit_indices"]))
        fingerprints[fingerprint] += 1
    duplicate_pairs = sum(n * (n - 1) // 2 for n in fingerprints.values())
    correlation_note = "No supported cohort."
    if len(validation_rows) >= 2:
        if len(validation_rows) <= 2000:
            streams = [np.asarray(validation_rows[cid]["validation"]["daily_net_r"], float)
                       for cid in cohort["candidate_ids"]]
            matrix = np.stack(streams)
            corr = np.corrcoef(matrix)
            upper = corr[np.triu_indices(len(streams), 1)]
            finite = upper[np.isfinite(upper)]
            correlation_note = (f"{len(finite):,} finite validation daily-P&L pairs; "
                                f"median correlation {float(np.median(finite)):.3f}; "
                                f"maximum {float(np.max(finite)):.3f}." if len(finite)
                                else "No finite daily-P&L pair correlations.")
        else:
            correlation_note = ("More than 2,000 supported candidates; the complete pairwise "
                                "correlation matrix is not materialized. Exact entry/exit "
                                "duplicate pairs are reported below.")
    reads = ledger.data_reads(project.ledger_path)
    v54_reads = [r for r in reads if r["result"] == ledger.ALLOWED
                 and str(r.get("purpose", "")).startswith("V5_4_")]
    partitions = Counter(r["partition"] for r in v54_reads)
    lines = ["# V5.4 complete broad historical research report", "",
             "## Search and discovery", "",
             f"Original V5: 60 Stage A rules tested, zero qualified; its validation and audits were never opened.",
             f"V5.4: {inventory['signal_configurations']:,} signal configurations × "
             f"{inventory['management_variants']} management variants = "
             f"{first['specifications_evaluated']:,} unique specifications, all evaluated.",
             f"Profitable after baseline costs: {first['summary_counts']['positive_net_r']:,}. "
             f"Positive stress net: {first['summary_counts']['positive_stress_net_r']:,}. "
             f"Frozen discovery qualifiers: {discovery['qualifier_count']:,}.",
             f"Qualifier families: {dict(sorted(families.items()))}.", "",
             "## Historical holdout validation", "",
             f"Every {validation['evaluated_count']:,} discovery qualifier was tested on 2019–2022. "
             f"Classifications: {validation['class_counts']}.",
             f"Scientific cohort: {cohort['candidate_ids']}.", "",
             "## Simultaneously revealed historical audits", "",
             f"2023–2025 supported: {sum(x['classification']=='SUPPORTED' for x in audits['audits']['phase1'].values())}; "
             f"positive after costs: {both['audit_1_positive_after_cost']}.",
             f"2026 supported: {sum(x['classification']=='SUPPORTED' for x in audits['audits']['phase2'].values())}; "
             f"positive after costs: {both['audit_2_positive_after_cost']}.",
             f"Dual-audit supported IDs: {both['dual_supported_ids']}.",
             f"Management templates among dual-supported: {dict(sorted(styles.items()))}.", "",
             "## Dependence, integer coverage, and limitations", "",
             f"Validation exact-entry/exit duplicate pairs: {duplicate_pairs:,}. {correlation_note}",
             f"Supported candidates with at least one modeled executed trade by MNQ budget: {dict(sorted(budget.items()))}.",
             "No portfolio was preregistered in V5.4. The MNQ commission is an unvalidated "
             "research placeholder, so the four-budget diagnostics do not establish real-firm deployability.",
             "Discovery is reused development data. The later periods are historical validation "
             "and audits, with V2/V3/V4 program-level awareness; no period is genuine live-forward evidence.",
             f"Data-access ledger verifies ({reason}); V5.4 allowed read partitions: {dict(sorted(partitions.items()))}.",
             "LIVE_FORWARD remains sealed and was not opened.", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("V5.4 complete historical report written")


if __name__ == "__main__":
    main()
