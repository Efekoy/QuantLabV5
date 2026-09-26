# V5.4 broad discovery universe

Post-original-V5 design inventory, generated before any V5.4 real strategy outcome.

Original V5 campaign: 60 Stage A evaluated; 0 qualified; later partitions unopened.
30 families; 71,820 signal configurations; 198 management variants; 14,220,360 unique executable specifications.
Removed 4,740,120 exact RTH/Globex semantic duplicates before the final count.

| Family | Core | Signal configurations | Combined specifications |
| --- | ---: | ---: | ---: |
| E01 | 30 | 2,700 | 534,600 |
| E02 | 36 | 3,240 | 641,520 |
| E03 | 42 | 3,780 | 748,440 |
| E04 | 5 | 450 | 89,100 |
| E05 | 36 | 3,240 | 641,520 |
| E06 | 30 | 2,700 | 534,600 |
| E07 | 28 | 2,520 | 498,960 |
| E08 | 25 | 2,250 | 445,500 |
| E09 | 30 | 2,700 | 534,600 |
| E10 | 24 | 2,160 | 427,680 |
| E11 | 1 | 90 | 17,820 |
| E12 | 30 | 2,700 | 534,600 |
| E13 | 30 | 2,700 | 534,600 |
| E14 | 36 | 3,240 | 641,520 |
| E15 | 6 | 540 | 106,920 |
| E16 | 30 | 2,700 | 534,600 |
| E17 | 30 | 2,700 | 534,600 |
| E18 | 30 | 2,700 | 534,600 |
| E19 | 30 | 2,700 | 534,600 |
| E20 | 30 | 2,700 | 534,600 |
| E21 | 30 | 2,700 | 534,600 |
| E22 | 1 | 90 | 17,820 |
| E23 | 30 | 2,700 | 534,600 |
| E24 | 30 | 2,700 | 534,600 |
| E25 | 30 | 2,700 | 534,600 |
| E26 | 30 | 2,700 | 534,600 |
| E27 | 30 | 2,700 | 534,600 |
| E28 | 24 | 2,160 | 427,680 |
| E29 | 24 | 2,160 | 427,680 |
| E30 | 30 | 2,700 | 534,600 |

Every family evaluates its full prespecified core surface. Family performance cannot stop expansion because there is no family kill gate.

## Combinatorial accounting

Four-session raw valid combinations: 18,960,480; exact RTH/Globex duplicates removed: 4,740,120; remaining static duplicates: 0.
Naive management Cartesian tuples per signal: 9,072; invalid/inconsistent tuples excluded per signal: 8,874; valid disjoint templates per signal: 198.

## Counts by template and axes

| Management template | Per signal | Complete universe |
| --- | ---: | ---: |
| T10_TIME_EXIT | 18 | 1,292,760 |
| T11_MECHANISM_EXIT | 6 | 430,920 |
| T1_FIXED_TARGET | 18 | 1,292,760 |
| T2_STRUCTURE_STOP_FIXED_TARGET | 18 | 1,292,760 |
| T3_SESSION_RUNNER | 6 | 430,920 |
| T4_BREAKEVEN_TARGET | 54 | 3,878,280 |
| T5_PARTIAL_RUNNER | 12 | 861,840 |
| T6_PARTIAL_BE_RUNNER | 18 | 1,292,760 |
| T7_TRAIL_RUNNER | 12 | 861,840 |
| T8_BE_TRAIL_RUNNER | 18 | 1,292,760 |
| T9_PARTIAL_TRAIL | 18 | 1,292,760 |

| Signal axis | Value | Complete universe |
| --- | --- | ---: |
| direction | long | 4,740,120 |
| direction | short | 4,740,120 |
| direction | both | 4,740,120 |
| session | rth | 4,740,120 |
| session | rth_am | 4,740,120 |
| session | rth_pm | 4,740,120 |
| filter count | zero | 2,844,072 |
| filter count | one | 8,532,216 |
| filter count | two | 2,844,072 |

| Management axis | Value | Complete universe |
| --- | --- | ---: |
| stop | atr_0.75 | 2,370,060 |
| stop | atr_1 | 2,370,060 |
| stop | atr_1.5 | 2,370,060 |
| stop | signal_bar | 2,370,060 |
| stop | swing_15 | 2,370,060 |
| stop | swing_5 | 2,370,060 |
| target_r | 0.75 | 430,920 |
| target_r | 1.0 | 861,840 |
| target_r | 1.5 | 1,292,760 |
| target_r | 2.0 | 1,292,760 |
| target_r | 3.0 | 1,292,760 |
| target_r | 4.0 | 1,292,760 |
| target_r | none | 7,756,560 |
| breakeven_r | 0.75 | 3,878,280 |
| breakeven_r | 1.25 | 2,585,520 |
| breakeven_r | none | 7,756,560 |
| partial_r | 1.0 | 1,292,760 |
| partial_r | 1.5 | 2,154,600 |
| partial_r | none | 10,773,000 |
| partial_fraction | 0.5 | 3,447,360 |
| partial_fraction | none | 10,773,000 |
| trail_r | 1.0 | 1,723,680 |
| trail_r | 1.5 | 1,723,680 |
| trail_r | none | 10,773,000 |
| hold | 15 | 430,920 |
| hold | 30 | 430,920 |
| hold | 60 | 6,894,720 |
| hold | eod | 6,463,800 |
| mechanism_exit | True | 430,920 |
| mechanism_exit | none | 13,789,440 |

## Compute and storage planning

First-pass storage: 1.66 GB (117 bytes/specification). Worst-case qualifier index: 0.11 GB. Detail, validation, and audit files depend on the uncapped qualifying cohort.
Pre-run peak process RAM estimate: 4–12 GB, unverified until a full-market run.
Actual sparse-kernel benchmark: 66,931 specifications/second at 1,000,000 synthetic evaluations; 10 million kernel calls ~149 s; full universe kernel calls ~212 s.
These times are lower bounds only. Real feature/event generation, real entry density, qualifier reruns, hashing, and storage may extend the full run to many hours.

Full axes and all management templates are in `V5_4_SEARCH_UNIVERSE.json`.
