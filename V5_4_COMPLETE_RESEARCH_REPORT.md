# V5.4 complete broad historical research report

## Search and discovery

Original V5: 60 Stage A rules tested, zero qualified; its validation and audits were never opened.
V5.4: 71,820 signal configurations × 198 management variants = 14,220,360 unique specifications, all evaluated.
Profitable after baseline costs: 502,015. Positive stress net: 227,339. Frozen discovery qualifiers: 32,423.
Qualifier families: {'E01': 1209, 'E02': 2169, 'E03': 96, 'E04': 7, 'E06': 6630, 'E07': 252, 'E08': 36, 'E09': 1481, 'E11': 293, 'E12': 926, 'E14': 400, 'E15': 417, 'E16': 165, 'E17': 6, 'E18': 36, 'E20': 83, 'E23': 3176, 'E24': 205, 'E25': 494, 'E26': 458, 'E27': 13387, 'E28': 482, 'E29': 14, 'E30': 1}.

## Historical holdout validation

Every 32,423 discovery qualifier was tested on 2019–2022. Classifications: {'INCONCLUSIVE / UNDERPOWERED': 32194, 'REJECTED': 225, 'SUPPORTED': 4}.
Scientific cohort: ['Q54-4b3a94d211d0d426fe3e7c15', 'Q54-a423e8be601df78f40089a66', 'Q54-cdb1d3d22908f8612e91b90f', 'Q54-0ec535a5e60ebe848bd47456'].

## Simultaneously revealed historical audits

2023–2025 supported: 0; positive after costs: 4.
2026 supported: 2; positive after costs: 4.
Dual-audit supported IDs: [].
Management templates among dual-supported: {}.

## Dependence, integer coverage, and limitations

Validation exact-entry/exit duplicate pairs: 0. 6 finite validation daily-P&L pairs; median correlation 0.661; maximum 0.988.
Supported candidates with at least one modeled executed trade by MNQ budget: {'250': 4, '300': 4, '350': 4, '400': 4}.
No portfolio was preregistered in V5.4. The MNQ commission is an unvalidated research placeholder, so the four-budget diagnostics do not establish real-firm deployability.
Discovery is reused development data. The later periods are historical validation and audits, with V2/V3/V4 program-level awareness; no period is genuine live-forward evidence.
Data-access ledger verifies (ok (36 records)); V5.4 allowed read partitions: {'DISCOVERY': 6, 'HISTORICAL_AUDIT_1': 2, 'HISTORICAL_AUDIT_2': 2, 'VALIDATION': 2}.
LIVE_FORWARD remains sealed and was not opened.

## Per-candidate historical evidence

The audit labels below use the separately frozen four-candidate Holm family. Positive net R alone does not mean `SUPPORTED`.

| Candidate | Family | Management | Validation trades / net R / Holm p | 2023–2025 trades / net R / Holm p / label | 2026 trades / net R / Holm p / label |
| --- | --- | --- | --- | --- | --- |
| Q54-4b3a94d211d0d426fe3e7c15 | E03 | T3_SESSION_RUNNER | 566 / 109.092 / 0.02965 | 426 / 20.750 / 0.3254 / INCONCLUSIVE / UNDERPOWERED | 72 / 4.928 / 0.5895 / INCONCLUSIVE / UNDERPOWERED |
| Q54-a423e8be601df78f40089a66 | E03 | T8_BE_TRAIL_RUNNER | 569 / 102.657 / 0.04815 | 429 / 29.988 / 0.3254 / INCONCLUSIVE / UNDERPOWERED | 72 / 2.928 / 0.5895 / INCONCLUSIVE / UNDERPOWERED |
| Q54-cdb1d3d22908f8612e91b90f | E09 | T3_SESSION_RUNNER | 280 / 104.136 / 0.0125 | 230 / 26.982 / 0.3254 / INCONCLUSIVE / UNDERPOWERED | 41 / 20.225 / 0.02874 / SUPPORTED |
| Q54-0ec535a5e60ebe848bd47456 | E09 | T3_SESSION_RUNNER | 280 / 97.721 / 0.02441 | 226 / 28.585 / 0.3254 / INCONCLUSIVE / UNDERPOWERED | 41 / 16.027 / 0.04082 / SUPPORTED |

Audit classifications: 2023–2025 had four `INCONCLUSIVE / UNDERPOWERED`; 2026 had two `SUPPORTED` and two `INCONCLUSIVE / UNDERPOWERED`. No candidate was supported in both. Validation-supported management styles were three session runners and one break-even/trailing runner; no style survived both audits.

## Candidate dependence and modeled risk budgets

The four validation-supported candidates had no identical entry/exit trade fingerprints on validation. Pairwise correlation below uses full 2019–2022 daily net R, including zero-trade days.

| Pair | Daily net-R correlation |
| --- | ---: |
| Q54-4b3a94d211d0d426fe3e7c15 / Q54-a423e8be601df78f40089a66 | 0.931 |
| Q54-4b3a94d211d0d426fe3e7c15 / Q54-cdb1d3d22908f8612e91b90f | 0.666 |
| Q54-4b3a94d211d0d426fe3e7c15 / Q54-0ec535a5e60ebe848bd47456 | 0.656 |
| Q54-a423e8be601df78f40089a66 / Q54-cdb1d3d22908f8612e91b90f | 0.651 |
| Q54-a423e8be601df78f40089a66 / Q54-0ec535a5e60ebe848bd47456 | 0.639 |
| Q54-cdb1d3d22908f8612e91b90f / Q54-0ec535a5e60ebe848bd47456 | 0.988 |

The following counts are modeled integer-MNQ eligibility on discovery; each candidate needs at least one executed trade for the corresponding budget. The MNQ commission remains unvalidated.

| Candidate | $250 trades | $300 trades | $350 trades | $400 trades |
| --- | ---: | ---: | ---: | ---: |
| Q54-4b3a94d211d0d426fe3e7c15 | 1129 | 1129 | 1129 | 1129 |
| Q54-a423e8be601df78f40089a66 | 1139 | 1139 | 1139 | 1139 |
| Q54-cdb1d3d22908f8612e91b90f | 640 | 640 | 640 | 640 |
| Q54-0ec535a5e60ebe848bd47456 | 640 | 640 | 640 | 640 |

All four have modeled executions at each budget, but the study does not establish firm deployability or portfolio performance. There is no preregistered portfolio selection in V5.4.

## Runtime and artifact scope

From first ledgered V5.4 DISCOVERY read to creation of the complete discovery freeze: approximately 2.59 hours (includes a resumable Windows checkpoint-lock interruption). The first-pass row store is approximately 1.66 GB; detailed discovery records are approximately 393 MB; validation results are approximately 342 MB. The largest process peak observed during monitoring was about 3.6 GB; this is an observed lower bound on true peak memory.

Original V5 artifacts remain at their earlier immutable tags. LIVE_FORWARD remains unopened. The campaign ends with zero dual-audit supported candidates, which is a valid frozen-experiment result.
