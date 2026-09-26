# Updated V5 power gate: 0.10R robust-effect stop

Status: **STOP / investigation required**. The 2026-09-25 instruction changes the economic target: 0.01–0.03R plants are diagnostics, while 0.05R at high frequency and robust 0.075–0.10R+ plants are the practical targets. The historical partition architecture remains unchanged. This report uses only the existing synthetic dependent-stream calibration. It is not a completed market-level search replay.

## Binding 0.10R observation

`reports/V5_HIERARCHICAL_POWER.json` contains 120 independent 1,034-session synthetic worlds per frequency, 30 families × four related rules, 99 common-index block-bootstrap resamples, and a prespecified global → family → neighborhood procedure. The 0.10R target results are:

| Trades/year | Shape | One-rule block test | Global search | Supported family/neighborhood |
|---:|---|---:|---:|---:|
| 100 | Needle | 47.5% | 16.7% | 0.8% |
| 100 | Plateau | 47.5% | 20.0% | 8.3% |
| 100 | Family | 47.5% | 18.3% | 5.0% |
| 100 | Regime | 43.3% | 14.2% | 0.8% |
| 250 | Needle | 88.3% | 39.2% | 0.8% |
| 250 | Plateau | 88.3% | 43.3% | 36.7% |
| 250 | Family | 88.3% | 39.2% | 15.8% |
| 250 | Regime | 75.8% | 26.7% | 2.5% |
| 500 | Needle | 96.7% | 56.7% | 3.3% |
| 500 | Plateau | 96.7% | 58.3% | 50.0% |
| 500 | Family | 96.7% | 56.7% | 27.5% |
| 500 | Regime | 89.2% | 31.7% | 5.0% |

The 500/year plateau family result is 60/120, with an exact two-sided 95% binomial interval about 40.7–59.3%. If **the same family-support rule** is required for validation, complete discovery→validation survival is a subset of validation family support; its power is therefore bounded above by 50% under this synthetic model. That is well below reliable recovery. The inequality is about this proposed rule, not a universal limit on any future method. At 500/year the single-rule test detects 0.10R in 96.7% of plateau worlds, while the joint global search detects it in 58.3% and the family gate in 50.0%. At this effect/frequency, **search multiplicity and joint gating dominate the additional loss**; at smaller effects the one-rule test itself lacks power because effective independent-session information is limited.

The primary practical-grid results below are **conditional fixed-library family-support probabilities**, *not* end-to-end A/B/C plus validation probabilities. Each cell is based on 120 synthetic worlds.

| Trades/year | Plant | 0.05R | 0.075R | 0.10R | 0.15R |
|---:|---|---:|---:|---:|---:|
| 100 | Needle | 0.8% | 0.8% | 0.8% | 2.5% |
| 100 | Plateau | 2.5% | 5.0% | 8.3% | 25.0% |
| 100 | Family | 1.7% | 2.5% | 5.0% | 11.7% |
| 100 | Regime | 0.8% | 0.8% | 0.8% | 2.5% |
| 250 | Needle | 0.8% | 0.8% | 0.8% | 3.3% |
| 250 | Plateau | 3.3% | 15.0% | 36.7% | 76.7% |
| 250 | Family | 1.7% | 4.2% | 15.8% | 45.8% |
| 250 | Regime | 0.0% | 0.8% | 2.5% | 6.7% |
| 500 | Needle | 1.7% | 2.5% | 3.3% | 9.2% |
| 500 | Plateau | 12.5% | 28.3% | 50.0% | 90.8% |
| 500 | Family | 4.2% | 15.8% | 27.5% | 64.2% |
| 500 | Regime | 1.7% | 2.5% | 5.0% | 17.5% |

The independent all-null fixed-library check in `reports/V5_HIERARCHICAL_NULL.json` observed global rejection in 17/300, 16/300 and 16/300 worlds at 100, 250 and 500/year. These rates have one-sided 95% upper bounds 8.4%, 8.0%, and 8.0%; they meet the draft's 10% gross all-null sanity gate but do not establish strong partial-null or adaptive-search control. No alpha threshold was relaxed.

## Inventory progress and remaining block

`quantlab5/v5/candidate_inventory.py` and `reports/V5_CANDIDATE_INVENTORY.json` now deterministically enumerate **60 Stage A directional specifications** and **220 applicable one-factor Stage B variants**. There are at most **57 reachable Stage C interactions per run**, for an **outcome-blind structural ceiling of 337 evaluated specifications**. Across alternative Stage B winners there are 448 conditional C IDs and 728 possible IDs in the full branch union. E11 and E22 have no Stage B axis, so neither can produce a Stage B winner or Stage C child; E02 and E13 have a meaningful additional C15 interaction. The C count is *conditional* on family-specific B winners. The B axes and tie handling remain subject to executable signal and causal-feature audit; behavioral duplicates cannot be known without market signals. The JSON is marked `REVIEW_ONLY_NOT_EXECUTABLE` and must not be treated as a final preregistered executable candidate universe.

Executable signal implementations for all 30 families, full synthetic NQ/ES market-surrogate generation, adaptive A→B→C replay, planted market-level end-to-end searches, validation simulation and true end-to-end MDE80 remain **unavailable**. The preliminary replay interface cannot claim adaptive false-positive control. The 0.10R stop instruction is triggered before those claims can be made. The scientifically relevant next investigation is a predeclared family-first statistic/selection design that can improve broad-effect recovery while preserving global and family false-positive control, followed by market-level replay; no change to data partitions or alpha is justified by these results alone.

No real discovery search was run, no sealed partition was opened, no stage transition was made, and no final `v5-prereg` freeze, commit or tag was created.
