# What V4 inherited from QuantLabV3 and what it did not

Source: `C:\Users\Administrator\Desktop\QuantLabV3` at git HEAD `cee42fef1a908498b0d8c5f78536107145a77f1e`.
Only engine and infrastructure code was read. No V3 results, rankings, survivors, cohorts,
freezes, ledgers, preregistrations, forward logs or reports were read or copied.
Every copied file's source SHA-256 and destination SHA-256 are in
`provenance/V3_COPIED_FILES.json` (at copy time) and `provenance/V3_COPIED_FILES_FINAL.json`
(after adaptation).

## Copied, then adapted

| V3 file | V4 file | Change |
|---|---|---|
| data/sessions.py | quantlab4/data/sessions.py | unchanged logic; added session_dates, session_end_utc_ns, is_complete_final_session |
| data/resample.py | quantlab4/data/resample.py | volume aggregated; session-straddling buckets flagged; strict-order check |
| data/validation.py | quantlab4/data/validation.py | volume validated (negative / non-integral / inf); full_report removed (it computed price statistics) |
| data/synthetic.py | quantlab4/synthetic/markets.py | integer volume added; **V3 DST bug fixed** (see below); known-property fixtures added |
| data/ledger.py | quantlab4/isolation/ledger.py | V4 record fields, seq numbers, cross-process lock, head check, anchors |
| data/stage_gate.py | quantlab4/isolation/stage_gate.py | nine V4 stages; registry pin; state file hashed and cross-checked with ledger |
| data/loader.py | quantlab4/isolation/load_view.py | logical requests, argument/path validation, refusals ledgered, volume, TRUE_FORWARD |
| freeze/hashing.py | quantlab4/isolation/manifests.py | generic write-once manifests with body + file hashes |
| engine/backtest.py | quantlab4/engine/backtest.py | added target trade-through (V3 engine-v2 policy); identical when tgt_through=0 |
| engine/execution.py | quantlab4/engine/execution.py | V3 management-library coupling removed; run_signals added |
| engine/costs.py | quantlab4/engine/costs.py | "stressed" -> "stress"; validated flag; micro mapping |
| engine/metrics.py | quantlab4/engine/metrics.py | integer contract column; "stress" naming |
| diagnostics/causality.py | quantlab4/diagnostics/lookahead.py | decoupled from V3 features/families; generic for any function of Bars |
| config/costs.yaml | config/costs.yaml | values unchanged for NQ/ES; MNQ/MES added as UNVALIDATED placeholders |
| config/sessions.yaml | config/sessions.yaml | V3-hypothesis window `rth_late` removed; completeness rule added |
| tools/harden_isolation.ps1 | tools/harden_isolation.ps1 | V4 paths, read-only project grant, denies on raw data and V2/V3 |
| tests/test_sessions_dst.py, test_resample.py, test_engine_timing.py, test_costs_metrics.py | same names | ported; V3-family-dependent tests dropped; V4 tests added |

## Inherited defaults (recorded exactly)

* Costs (V3 `costs_v2_approved_2026-09-21`): NQ and ES $4.00 commission per round trip and
  1 tick of slippage per side at baseline. Scenario multipliers: gross 0/0/0, moderate 1/0.5/1,
  baseline 1/1/1, stress 1.5/2/1. The resulting round trips are NQ $0 / $9 / $14 / $26 and
  ES $0 / $16.50 / $29 / $56.
* Execution: next-bar-open entry; pessimistic same-bar stop/target resolution; a target fills
  only on a 1-tick trade-through; a stop gap fills at the open; flat at session end and at a roll.
* Session convention: 18:00-17:00 New York, labelled by end date. Windows rth / rth_am / rth_pm / globex.

## Deliberately NOT inherited

* All V2/V3 strategy families and the V3 catalog (`strategies/**`, `v3_catalog.py`).
* V3 hypothesis features (`features/v3feat.py`, `indicators.py`, `cache.py`).
* The V3 management library and multi-leg kernel (`engine/managed.py`, `management.py`,
  `v3exec.py`). Its curated templates encode V3 research choices. Generic multi-leg
  management can be ported later after a separate review.
* V3 discovery enumeration/evaluation, config/search_space.yaml, research.yaml, management_smoke.yaml.
* V3 partitions, ledgers, freezes, results, reports, preregistrations, forward data.
* V3 tests that depended on the above (test_v3*, test_management, test_reference, test_isolation,
  test_lookahead, test_cross_market). Equivalent V4 tests were written against V4 code instead.

## Bugs found in inherited code

* `data/synthetic.py` built Globex session starts as "local midnight + 18h". On a DST-ending
  Sunday that gives 17:00, so the bars land in a phantom Sunday session. The V4 partitioner
  refused the synthetic file because of it (rows fell between partitions). Fixed with
  wall-clock construction, and a regression test was added. This affected synthetic test data
  only, not real data.
