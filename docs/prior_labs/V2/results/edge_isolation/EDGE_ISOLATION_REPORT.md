# EDGE ISOLATION REPORT -- QuantLabV2

```
REAL FINAL SURVIVORS:          11,462  (verified: six stage result files + stored OOS trades)
DISTINCT ENTRY RULES:          567
PRIMARY BEHAVIOURAL CLUSTERS:  259  (daily OOS P&L correlation, average linkage, tau 0.5)
STRONGER-SUBSET CLUSTERS:      70  (4,362 candidates, 138 entry rules)
CLUSTERS CLEARLY ABOVE NULL:   0
CLUSTERS WITH MIXED EVIDENCE:  7
NULL-LIKE CLUSTERS:            252
  (all final survivors, primary clusters). STRONGER SUBSET: 3 clearly above null, 3 mixed, 64 null-like
```

Analysis of completed official and null results only. No new market data, no strategy changes, no optimisation, no selection. Summed P&L of overlapping strategies is never presented as an achievable portfolio result. Nothing here is a recommendation to trade.

## 1. Integrity (start of stage)

# EDGE ISOLATION -- INTEGRITY CHECK (START, 2026-09-22 16:28 UTC)

REAL_DATA_CUTOFF: NQ 2026-08-10 19:59:00-04:00, ES 2026-08-14 16:59:00-04:00

| check | result | detail |
|---|---|---|
| Archive manifest hash unchanged | PASS | cfe9dc59ccd12762e46a32a889fbc119bcd69aa9adaf26b1acbe588ef371c5cb |
| All 192 archived files match their hashes | PASS | 0 |
| results/main files identical to the archive | PASS | [] |
| Large official files (frozen cohort, stage results) unchanged | PASS | [] |
| Official trade files unchanged | PASS | [] |
| Official freeze verifies and its hash is unchanged | PASS | c6da1c8ad6908f9a4ce94d8ed8e4cf5084bc465b94effd750556627be00f1d6b |
| Null-funnel world files match their checkpoint hashes (200 worlds) | PASS | [] |
| Null-funnel snapshot recorded | PASS | 640 files |
| Official ledger unchanged | PASS |  |
| Null ledger: no bar past the per-instrument cutoff | PASS | 12 entries |
| No cached real-market extract past the cutoff | PASS | 2026-08-14 16:59:00-04:00 |
| Null source arrays (cache/null_source) within the cutoff | PASS |  |
| Edge-isolation stage made no guarded market-data load (no ledger of its own) | PASS |  |
| Tests | PASS | 87 passed, 0 failed |

**ALL CHECKS PASSED**

## 2. Method

- Pre-registered before any clustering ran: `CLUSTERING_PREREGISTRATION.md` (sha256 in `.sha256`) and `CLUSTER_EVIDENCE_PREREGISTRATION.md`.
- Behaviour = daily OOS baseline-net P&L over 1,453 sessions (2021-01-01 .. cutoff) from the 9,975,435 stored official OOS trades of the survivors (per-survivor totals verified against the official final table), plus entry events (5-minute bucket x direction).
- PRIMARY: average-linkage clustering on 1 - Pearson(daily P&L), cut at rho = 0.5. Entry-overlap view (Jaccard) as a cross-check. Descriptive labels are never clustering inputs.
- Null: every one of the 200 null worlds was regenerated from its stored seeds. Its final survivors' trades reproduced the stored OOS trade counts and net P&L exactly (check in every world JSON), and they were clustered with the identical rule.
- Per-cluster evidence: compared with the BEST cluster of each null world (size, entry-rule count, strong members), which is family-wise across the many clusters examined.

## 3. How redundant are the 11,462 survivors?

| view | level | tau | clusters | median size | largest | singletons | share in clusters >= 20 | ge5 | ge20 | ge100 |
|---|---|---|---|---|---|---|---|---|---|---|
| A_pnl_corr | VERY_TIGHT | 0.9 | 2,482 | 1 | 111 | 1,249 | 45.1% | 474 | 115 | 4 |
| A_pnl_corr | TIGHT | 0.7 | 731 | 3 | 665 | 220 | 79.0% | 281 | 122 | 30 |
| A_pnl_corr | MODERATE | 0.5 | 259 | 4 | 1,728 | 64 | 92.6% | 124 | 69 | 22 |
| A_pnl_corr | LOOSE | 0.3 | 94 | 5 | 4,038 | 23 | 97.7% | 50 | 31 | 12 |
| B_entry_jaccard | VERY_TIGHT | 0.9 | 1,527 | 2 | 162 | 686 | 63.5% | 383 | 136 | 17 |
| B_entry_jaccard | TIGHT | 0.7 | 635 | 3 | 244 | 195 | 82.6% | 289 | 146 | 32 |
| B_entry_jaccard | MODERATE | 0.5 | 460 | 5 | 342 | 111 | 86.9% | 235 | 128 | 35 |
| B_entry_jaccard | LOOSE | 0.3 | 286 | 7 | 464 | 64 | 92.1% | 167 | 96 | 34 |

Agreement between the P&L view (A) and the entry-overlap view (B) at the same level:

| level | adjusted Rand | A-pairs also together in B | B-pairs also together in A |
|---|---|---|---|
| VERY_TIGHT | 0.672 | 90.8% | 53.5% |
| TIGHT | 0.581 | 48.7% | 73.3% |
| MODERATE | 0.252 | 15.9% | 77.6% |
| LOOSE | 0.085 | 6.2% | 75.1% |

![cluster sizes](reports/plots/cluster_size_rank.png)


## 4. Real vs null: distinct behaviours

p = (1 + #null worlds >= real) / 201. `candidates` = survivors in that set.

| set | metric | real | null_median | null_p95 | null_p99 | null_max | p_upper |
|---|---|---|---|---|---|---|---|
| all | candidates | 11,462 | 1,013 | 2,837 | 3,786 | 4,664 | 0.0050 |
| strong | candidates | 4,362 | 148 | 696 | 799 | 1,114 | 0.0050 |
| short | candidates | 1,227 | 150 | 744 | 987 | 1,141 | 0.0050 |
| all | entry_rules | 567 | 145 | 264 | 345 | 374 | 0.0050 |
| all | clusters | 259 | 102 | 158 | 179 | 184 | 0.0050 |
| all | clusters_ge5 | 124 | 34 | 63.1 | 78 | 82 | 0.0050 |
| all | clusters_ge20 | 69 | 12 | 25 | 33 | 39 | 0.0050 |
| all | clusters_ge100 | 22 | 1 | 7 | 8.01 | 11 | 0.0050 |
| all | singletons | 64 | 38 | 54 | 60 | 60 | 0.0050 |
| all | largest_cluster | 1,728 | 149 | 594 | 1,103 | 1,781 | 0.0100 |
| all | high_confidence_clusters | 38 | 4 | 13 | 16 | 21 | 0.0050 |
| strong | entry_rules | 138 | 24 | 54.1 | 74 | 88 | 0.0050 |
| strong | clusters | 70 | 19 | 37 | 44 | 48 | 0.0050 |
| strong | clusters_ge5 | 37 | 6 | 15 | 19 | 27 | 0.0050 |
| strong | clusters_ge20 | 26 | 2 | 7 | 9.01 | 10 | 0.0050 |
| strong | clusters_ge100 | 10 | 0 | 2 | 3 | 3 | 0.0050 |
| strong | singletons | 18 | 6 | 13 | 16 | 18 | 0.0100 |
| strong | largest_cluster | 981 | 45.5 | 209 | 400 | 473 | 0.0050 |
| strong | high_confidence_clusters | 23 | 2 | 7.05 | 11 | 13 | 0.0050 |
| short | entry_rules | 70 | 27.5 | 61.1 | 78 | 83 | 0.0348 |
| short | clusters | 47 | 22.5 | 42 | 50 | 61 | 0.0448 |
| short | clusters_ge5 | 21 | 7 | 18 | 21 | 26 | 0.0249 |
| short | clusters_ge20 | 10 | 2 | 7 | 11 | 12 | 0.0249 |
| short | clusters_ge100 | 4 | 0 | 2 | 3.01 | 5 | 0.0149 |
| short | singletons | 9 | 9 | 18 | 21 | 24 | 0.5721 |
| short | largest_cluster | 300 | 49 | 236 | 376 | 414 | 0.0398 |
| short | high_confidence_clusters | 4 | 0 | 3 | 4 | 7 | 0.0398 |

## 5. Cluster evidence (primary clusters of all final survivors)

| evidence | clusters | members | entry_rules | strong_members |
|---|---|---|---|---|
| MIXED | 7 | 5,295 | 211 | 2,296 |
| NULL-LIKE | 252 | 6,167 | 563 | 2,066 |

By majority family and evidence:

| family | MIXED | NULL-LIKE |
|---|---|---|
| candles | 0 | 6 |
| compression_expansion | 0 | 6 |
| consecutive_bars | 0 | 3 |
| cross_market | 0 | 31 |
| displacement | 0 | 6 |
| fvg | 1 | 23 |
| gap | 0 | 4 |
| mean_deviation | 3 | 27 |
| momentum | 3 | 67 |
| multi_timeframe | 0 | 21 |
| opening_range | 0 | 4 |
| overnight_range | 0 | 3 |
| price_structure | 0 | 4 |
| prior_session_levels | 0 | 9 |
| range_position | 0 | 2 |
| rolling_breakout | 0 | 1 |
| session_open_distance | 0 | 11 |
| time_of_day | 0 | 10 |
| volatility_regime | 0 | 14 |

By instrument / direction (clusters that are not NULL-LIKE):

| instrument | MIXED | both | long |
|---|---|---|---|
| MIXED | 2 | 1 | 2 |
| NQ | 2 | 0 | 0 |

**Every cluster that is not NULL-LIKE** (full table: `cluster_summary.csv`):

| cluster | evidence | size | entry_rules | strong | family | instrument | direction | homogeneity | edge_type | median_pair_corr | median_pair_entry_jaccard | median_oos_trades | median_oos_pf | median_oos_wr | frac_broad_plateau | frac_cliff | recency_class | recent_signs_of_life | p_size | p_entries | p_strong |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | MIXED | 1,728 | 97 | 6 | fvg | MIXED | long | MIXED | entry edge, robust across management types | 0.633 | 0.0305 | 1,768 | 1.13 | 44.0% | 33% | 7% | PERSISTENT | above null median, not p95 | 0.0100 | 0.0149 | 0.9701 |
| 1 | MIXED | 971 | 54 | 307 | momentum | MIXED | both | MIXED | entry edge, robust across management types | 0.565 | 0.119 | 1,363 | 1.23 | 46.5% | 23% | 15% | RECENTLY STRONG | above null median, not p95 | 0.0199 | 0.0746 | 0.0149 |
| 2 | MIXED | 903 | 25 | 724 | mean_deviation | MIXED | long | MIXED | entry edge, robust across management types | 0.606 | 0.224 | 383 | 1.47 | 52.0% | 25% | 20% | RECENTLY STRONG | above null median, not p95 | 0.0199 | 0.1741 | 0.0050 |
| 3 | MIXED | 554 | 13 | 442 | mean_deviation | MIXED | MIXED | MIXED | entry edge, robust across management types | 0.637 | 0.333 | 299 | 1.54 | 49.2% | 13% | 6% | PERSISTENT | above null median, not p95 | 0.0697 | 0.4279 | 0.0050 |
| 4 | MIXED | 473 | 11 | 260 | mean_deviation | MIXED | MIXED | MIXED | entry edge, robust across management types | 0.641 | 0.153 | 243 | 1.53 | 58.0% | 43% | 4% | INTERMITTENT | at or below null median | 0.1045 | 0.4826 | 0.0249 |
| 5 | MIXED | 373 | 9 | 286 | momentum | NQ | MIXED | MIXED | entry edge, robust across management types | 0.639 | 0.188 | 481 | 1.39 | 54.5% | 42% | 0% | PERSISTENT | above null median, not p95 | 0.1443 | 0.5821 | 0.0149 |
| 7 | MIXED | 293 | 2 | 271 | momentum | NQ | MIXED | BEHAVIOUR-HOMOGENEOUS | entry edge, robust across management types | 0.67 | 0.828 | 320 | 1.4 | 55.0% | 4% | 6% | PERSISTENT | above null median, not p95 | 0.2189 | 1.0000 | 0.0149 |

## 6. Family level (real vs null)

| family | real_survivors | null_median_survivors | p_survivors | real_entry_rules | null_median_entry_rules | null_p95_entry_rules | p_entry_rules | real_clusters | null_median_clusters | null_p95_clusters | p_clusters | real_strong | null_median_strong | null_p95_strong | p_strong | real_high_conf_clusters | null_median_high_conf | p_high_conf | real_clusters_clearly_above_null | real_clusters_mixed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| momentum | 3,860 | 356 | 0.0050 | 167 | 45 | 83 | 0.0050 | 70 | 31 | 48 | 0.0050 | 1,501 | 35 | 276 | 0.0050 | 16 | 1 | 0.0050 | 0 | 3 |
| mean_deviation | 2,583 | 128 | 0.0050 | 77 | 21 | 41 | 0.0050 | 30 | 13 | 24 | 0.0199 | 1,504 | 8 | 154 | 0.0050 | 8 | 0 | 0.0050 | 0 | 3 |
| cross_market | 1,607 | 46 | 0.0050 | 51 | 9 | 20 | 0.0050 | 31 | 7 | 16 | 0.0050 | 645 | 3 | 80 | 0.0050 | 6 | 0 | 0.0050 | 0 | 0 |
| fvg | 1,235 | 61 | 0.0050 | 52 | 11 | 27 | 0.0050 | 24 | 9 | 16 | 0.0050 | 2 | 1 | 32.1 | 0.4677 | 0 | 0 | 1.0000 | 0 | 1 |
| multi_timeframe | 529 | 63 | 0.0149 | 37 | 13 | 31 | 0.0149 | 21 | 9 | 20 | 0.0448 | 430 | 8 | 127 | 0.0100 | 2 | 0 | 0.1692 | 0 | 0 |
| session_open_distance | 306 | 14.5 | 0.0149 | 17 | 4 | 10 | 0.0050 | 11 | 3 | 8 | 0.0149 | 121 | 1 | 32.1 | 0.0100 | 3 | 0 | 0.0050 | 0 | 0 |
| volatility_regime | 253 | 24 | 0.0100 | 17 | 5 | 10 | 0.0050 | 14 | 4 | 8 | 0.0050 | 4 | 0 | 32.1 | 0.2488 | 0 | 0 | 1.0000 | 0 | 0 |
| prior_session_levels | 162 | 19.5 | 0.0398 | 14 | 5 | 15 | 0.0896 | 9 | 4 | 9 | 0.0697 | 80 | 1.5 | 46 | 0.0249 | 2 | 0 | 0.0647 | 0 | 0 |
| compression_expansion | 155 | 8 | 0.0149 | 9 | 2.5 | 8 | 0.0498 | 6 | 2 | 6.05 | 0.0995 | 0 | 0 | 8.1 | 1.0000 | 0 | 0 | 1.0000 | 0 | 0 |
| candles | 126 | 3 | 0.0050 | 17 | 1 | 7.05 | 0.0050 | 6 | 1 | 4.05 | 0.0199 | 0 | 0 | 0 | 1.0000 | 0 | 0 | 1.0000 | 0 | 0 |
| time_of_day | 114 | 14 | 0.0647 | 16 | 5 | 20 | 0.0896 | 10 | 4 | 13 | 0.1244 | 2 | 0 | 14.1 | 0.2537 | 0 | 0 | 1.0000 | 0 | 0 |
| range_position | 109 | 0 | 0.0149 | 16 | 0 | 8.05 | 0.0149 | 2 | 0 | 1 | 0.0299 | 0 | 0 | 0 | 1.0000 | 0 | 0 | 1.0000 | 0 | 0 |
| displacement | 93 | 7 | 0.0945 | 18 | 3 | 14 | 0.0100 | 6 | 2 | 7.05 | 0.1443 | 49 | 0 | 34.5 | 0.0448 | 1 | 0 | 0.1542 | 0 | 0 |
| consecutive_bars | 91 | 2 | 0.0199 | 8 | 1 | 4 | 0.0050 | 3 | 1 | 3 | 0.0945 | 23 | 0 | 3.05 | 0.0050 | 0 | 0 | 1.0000 | 0 | 0 |
| opening_range | 75 | 3 | 0.0050 | 6 | 1 | 5 | 0.0398 | 4 | 1 | 4 | 0.0697 | 0 | 0 | 11 | 1.0000 | 0 | 0 | 1.0000 | 0 | 0 |
| rolling_breakout | 59 | 2 | 0.0945 | 17 | 1 | 11 | 0.0149 | 1 | 1 | 2 | 0.5373 | 0 | 0 | 1.05 | 1.0000 | 0 | 0 | 1.0000 | 0 | 0 |
| price_structure | 46 | 3 | 0.0597 | 13 | 1 | 8 | 0.0100 | 4 | 1 | 4 | 0.1045 | 0 | 0 | 3 | 1.0000 | 0 | 0 | 1.0000 | 0 | 0 |
| failed_breakout | 24 | 0 | 0.0299 | 3 | 0 | 2.05 | 0.0547 | 0 | 0 | 0 | 1.0000 | 0 | 0 | 0 | 1.0000 | 0 | 0 | 1.0000 | 0 | 0 |
| overnight_range | 22 | 5 | 0.1542 | 6 | 2 | 7 | 0.1045 | 3 | 2 | 5 | 0.3483 | 0 | 0 | 7 | 1.0000 | 0 | 0 | 1.0000 | 0 | 0 |
| gap | 13 | 10 | 0.4677 | 6 | 3 | 10 | 0.3184 | 4 | 2 | 7 | 0.3333 | 1 | 1 | 49 | 0.6169 | 0 | 0 | 1.0000 | 0 | 0 |

## 7. High-frequency behaviour

![hf](reports/plots/hf_clusters.png)

| oos_trades_bucket | real_survivors | null_median | null_p95 | p_survivors | real_entry_rules | null_median_entry_rules | p_entry_rules | real_clusters_touched | null_median_clusters_touched | null_p95_clusters_touched | p_clusters_touched | share_in_largest_cluster | clusters_clearly_above_null_touched | pf_p10_p50_p90 | wr_p10_p50_p90 | mgmt_styles |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <200 | 1,756 | 382 | 861 | 0.0050 | 111 | 53 | 0.0050 | 84 | 44 | 61 | 0.0050 | 18.6% | 0 | [1.469, 1.808, 3.429] | [0.373, 0.55, 0.709] | trailing stop 909; simple (stop/target/time) 366; breakeven 223; runner 166; partial 92 |
| 200-500 | 3,594 | 248 | 804 | 0.0050 | 111 | 35 | 0.0050 | 89 | 30 | 53 | 0.0050 | 16.3% | 0 | [1.263, 1.432, 1.68] | [0.365, 0.515, 0.598] | trailing stop 1846; simple (stop/target/time) 661; breakeven 521; runner 385; partial 181 |
| 500-1,000 | 2,557 | 162 | 673 | 0.0050 | 116 | 28 | 0.0050 | 82 | 22.5 | 44 | 0.0050 | 10.4% | 0 | [1.176, 1.292, 1.486] | [0.301, 0.474, 0.554] | trailing stop 1280; simple (stop/target/time) 509; breakeven 435; runner 243; partial 90 |
| 1,000-2,500 | 2,845 | 102 | 788 | 0.0050 | 222 | 28 | 0.0050 | 81 | 19 | 41 | 0.0050 | 39.0% | 0 | [1.094, 1.161, 1.261] | [0.321, 0.452, 0.528] | trailing stop 1391; simple (stop/target/time) 623; breakeven 556; runner 203; partial 72 |
| 2,500+ | 710 | 12 | 138 | 0.0050 | 92 | 5 | 0.0050 | 23 | 3 | 11 | 0.0050 | 54.1% | 0 | [1.052, 1.086, 1.137] | [0.292, 0.38, 0.499] | trailing stop 475; simple (stop/target/time) 114; breakeven 85; runner 29; partial 7 |

## 8. The stronger subset (>= 200 OOS trades AND OOS PF >= 1.3), clustered within itself

4,362 candidates, 138 entry rules, **70 behavioural clusters**: NULL-LIKE 64, CLEARLY ABOVE NULL 3, MIXED 3.

| cluster | evidence | size | entry_rules | strong | family | instrument | direction | homogeneity | edge_type | median_pair_corr | median_oos_trades | median_oos_pf | p_size | p_entries | p_strong |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | CLEARLY ABOVE NULL | 981 | 22 | 981 | mean_deviation | MIXED | long | MIXED | entry edge, robust across management types | 0.604 | 302 | 1.55 | 0.0050 | 0.0100 | 0.0050 |
| 1 | CLEARLY ABOVE NULL | 632 | 22 | 632 | momentum | NQ | MIXED | MIXED | entry edge, robust across management types | 0.564 | 775 | 1.4 | 0.0050 | 0.0100 | 0.0050 |
| 2 | CLEARLY ABOVE NULL | 496 | 9 | 496 | mean_deviation | NQ | both | MIXED | entry edge, robust across management types | 0.653 | 364 | 1.54 | 0.0050 | 0.0846 | 0.0050 |
| 3 | MIXED | 298 | 3 | 298 | cross_market | NQ | MIXED | MIXED | entry edge, robust across management types | 0.622 | 360 | 1.49 | 0.0199 | 0.6418 | 0.0199 |
| 4 | MIXED | 271 | 2 | 271 | momentum | NQ | MIXED | BEHAVIOUR-HOMOGENEOUS | entry edge, robust across management types | 0.693 | 313 | 1.41 | 0.0249 | 0.9353 | 0.0249 |
| 5 | NULL-LIKE | 197 | 2 | 197 | momentum | NQ | both | BEHAVIOUR-HOMOGENEOUS | entry edge, robust across management types | 0.746 | 329 | 1.41 | 0.0697 | 0.9353 | 0.0697 |
| 6 | NULL-LIKE | 159 | 2 | 159 | momentum | NQ | long | BEHAVIOUR-HOMOGENEOUS | entry edge, robust across management types | 0.8 | 426 | 1.4 | 0.0995 | 0.9353 | 0.0995 |
| 7 | NULL-LIKE | 140 | 8 | 140 | session_open_distance | MIXED | long | MIXED | entry edge, robust across management types | 0.626 | 612 | 1.34 | 0.1144 | 0.1045 | 0.1144 |
| 8 | NULL-LIKE | 139 | 9 | 139 | mean_deviation | NQ | short | MIXED | entry edge, robust across management types | 0.67 | 321 | 1.4 | 0.1144 | 0.0846 | 0.1144 |
| 9 | NULL-LIKE | 129 | 2 | 129 | cross_market | NQ | MIXED | BEHAVIOUR-HOMOGENEOUS | entry edge, robust across management types | 0.611 | 406 | 1.42 | 0.1343 | 0.9353 | 0.1343 |
| 10 | NULL-LIKE | 81 | 4 | 81 | mean_deviation | NQ | MIXED | BEHAVIOUR-HOMOGENEOUS | entry edge, robust across management types | 0.903 | 283 | 1.35 | 0.3085 | 0.4478 | 0.3085 |
| 11 | NULL-LIKE | 70 | 4 | 70 | momentum | MIXED | long | BEHAVIOUR-HOMOGENEOUS | entry edge, robust across management types | 0.857 | 309 | 1.37 | 0.3582 | 0.4478 | 0.3582 |
| 12 | NULL-LIKE | 68 | 1 | 68 | prior_session_levels | NQ | long | ENTRY-HOMOGENEOUS | entry edge, robust across management types | 0.881 | 205 | 1.56 | 0.3582 | 1.0000 | 0.3582 |
| 13 | NULL-LIKE | 63 | 1 | 63 | cross_market | NQ | long | ENTRY-HOMOGENEOUS | entry edge, robust across management types | 0.705 | 294 | 1.44 | 0.3831 | 1.0000 | 0.3831 |
| 14 | MIXED | 62 | 12 | 62 | momentum | NQ | MIXED | MIXED | entry edge, robust across management types | 0.592 | 763 | 1.42 | 0.3881 | 0.0249 | 0.3881 |
| 15 | NULL-LIKE | 61 | 5 | 61 | momentum | NQ | long | MIXED | entry edge, robust across management types | 0.613 | 442 | 1.38 | 0.3881 | 0.3085 | 0.3881 |
| 16 | NULL-LIKE | 47 | 2 | 47 | cross_market | NQ | MIXED | BEHAVIOUR-HOMOGENEOUS | entry edge, robust across management types | 0.631 | 429 | 1.5 | 0.4925 | 0.9353 | 0.4925 |
| 17 | NULL-LIKE | 47 | 4 | 47 | cross_market | NQ | MIXED | MIXED | entry edge, robust across management types | 0.684 | 798 | 1.34 | 0.4925 | 0.4478 | 0.4925 |
| 18 | NULL-LIKE | 42 | 5 | 42 | displacement | NQ | MIXED | MIXED | entry edge, robust across management types | 0.635 | 280 | 1.45 | 0.5373 | 0.3085 | 0.5373 |
| 19 | NULL-LIKE | 36 | 1 | 36 | multi_timeframe | NQ | long | ENTRY-HOMOGENEOUS | entry edge, robust across management types | 0.9 | 828 | 1.4 | 0.6119 | 1.0000 | 0.6119 |
| 20 | NULL-LIKE | 30 | 6 | 30 | multi_timeframe | NQ | long | MIXED | entry edge, robust across management types | 0.603 | 334 | 1.38 | 0.6716 | 0.1841 | 0.6716 |
| 21 | NULL-LIKE | 29 | 2 | 29 | cross_market | NQ | MIXED | BEHAVIOUR-HOMOGENEOUS | entry edge, robust across management types | 0.681 | 665 | 1.49 | 0.6816 | 0.9353 | 0.6816 |
| 22 | NULL-LIKE | 28 | 1 | 28 | mean_deviation | NQ | both | ENTRY-HOMOGENEOUS | entry edge, robust across management types | 0.663 | 614 | 1.43 | 0.6866 | 1.0000 | 0.6866 |
| 23 | NULL-LIKE | 24 | 2 | 24 | momentum | NQ | both | BEHAVIOUR-HOMOGENEOUS | entry edge, robust across management types | 0.686 | 308 | 1.55 | 0.7313 | 0.9353 | 0.7313 |
| 24 | NULL-LIKE | 23 | 1 | 23 | mean_deviation | NQ | both | ENTRY-HOMOGENEOUS | entry edge, robust across management types | 0.775 | 244 | 1.34 | 0.7313 | 1.0000 | 0.7313 |
| 25 | NULL-LIKE | 23 | 1 | 23 | consecutive_bars | NQ | long | ENTRY-HOMOGENEOUS | entry edge, robust across management types | 0.883 | 659 | 1.34 | 0.7313 | 1.0000 | 0.7313 |
| 26 | NULL-LIKE | 19 | 2 | 19 | session_open_distance | NQ | MIXED | BEHAVIOUR-HOMOGENEOUS | entry edge, robust across management types | 0.626 | 290 | 1.62 | 0.8010 | 0.9353 | 0.8010 |
| 27 | NULL-LIKE | 19 | 2 | 19 | mean_deviation | ES | long | BEHAVIOUR-HOMOGENEOUS | entry edge, robust across management types | 0.876 | 202 | 1.54 | 0.8010 | 0.9353 | 0.8010 |
| 28 | NULL-LIKE | 18 | 2 | 18 | momentum | ES | both | BEHAVIOUR-HOMOGENEOUS | several managements, no simple variant | 0.871 | 223 | 1.49 | 0.8109 | 0.9353 | 0.8109 |
| 29 | NULL-LIKE | 17 | 1 | 17 | mean_deviation | NQ | long | ENTRY-HOMOGENEOUS | entry edge, robust across management types | 0.744 | 434 | 1.4 | 0.8259 | 1.0000 | 0.8259 |
| 30 | NULL-LIKE | 10 | 1 | 10 | session_open_distance | ES | long | ENTRY-HOMOGENEOUS | entry edge, robust across management types | 0.932 | 210 | 1.42 | 0.9055 | 1.0000 | 0.9055 |
| 31 | NULL-LIKE | 10 | 1 | 10 | cross_market | NQ | long | ENTRY-HOMOGENEOUS | entry edge, robust across management types | 0.771 | 383 | 1.34 | 0.9055 | 1.0000 | 0.9055 |
| 32 | NULL-LIKE | 8 | 1 | 8 | momentum | NQ | long | ENTRY-HOMOGENEOUS | entry edge, robust across management types | 0.916 | 227 | 1.5 | 0.9552 | 1.0000 | 0.9552 |
| 33 | NULL-LIKE | 7 | 1 | 7 | prior_session_levels | NQ | long | ENTRY-HOMOGENEOUS | several managements, no simple variant | 0.959 | 419 | 1.32 | 0.9701 | 1.0000 | 0.9701 |
| 34 | NULL-LIKE | 5 | 2 | 5 | session_open_distance | NQ | MIXED | BEHAVIOUR-HOMOGENEOUS | several managements, no simple variant | 0.703 | 603 | 1.33 | 0.9751 | 0.9353 | 0.9751 |
| 35 | NULL-LIKE | 5 | 4 | 5 | mean_deviation | NQ | both | MIXED | one-management-template dependent | 0.587 | 538 | 1.4 | 0.9751 | 0.4478 | 0.9751 |
| 36 | NULL-LIKE | 5 | 3 | 5 | multi_timeframe | NQ | long | BEHAVIOUR-HOMOGENEOUS | several managements, no simple variant | 0.727 | 258 | 1.43 | 0.9751 | 0.6418 | 0.9751 |
| 37 | NULL-LIKE | 4 | 2 | 4 | momentum | NQ | both | MIXED | one-management-template dependent | 0.622 | 300 | 1.37 | 0.9950 | 0.9353 | 0.9950 |
| 38 | NULL-LIKE | 4 | 2 | 4 | cross_market | NQ | MIXED | BEHAVIOUR-HOMOGENEOUS | one-management-template dependent | 0.69 | 541 | 1.43 | 0.9950 | 0.9353 | 0.9950 |
| 39 | NULL-LIKE | 4 | 2 | 4 | cross_market | NQ | long | MIXED | simple-management profitable | 0.564 | 438 | 1.4 | 0.9950 | 0.9353 | 0.9950 |
| 40 | NULL-LIKE | 4 | 3 | 4 | cross_market | NQ | MIXED | MIXED | one-management-template dependent | 0.692 | 337 | 1.61 | 0.9950 | 0.6418 | 0.9950 |
| 41 | NULL-LIKE | 4 | 3 | 4 | displacement | NQ | long | BEHAVIOUR-HOMOGENEOUS | one-management-template dependent | 0.636 | 316 | 1.41 | 0.9950 | 0.6418 | 0.9950 |
| 42 | NULL-LIKE | 4 | 2 | 4 | mean_deviation | NQ | long | BEHAVIOUR-HOMOGENEOUS | several managements, no simple variant | 0.615 | 229 | 1.66 | 0.9950 | 0.9353 | 0.9950 |
| 43 | NULL-LIKE | 4 | 1 | 4 | prior_session_levels | NQ | both | ENTRY-HOMOGENEOUS | several managements, no simple variant | 0.894 | 526 | 1.4 | 0.9950 | 1.0000 | 0.9950 |
| 44 | NULL-LIKE | 3 | 1 | 3 | momentum | NQ | long | ENTRY-HOMOGENEOUS | one-management-template dependent | 0.677 | 224 | 1.75 | 0.9950 | 1.0000 | 0.9950 |
| 45 | NULL-LIKE | 2 | 2 | 2 | multi_timeframe | NQ | MIXED | BEHAVIOUR-HOMOGENEOUS | one-management-template dependent | 0.809 | 433 | 1.43 | 1.0000 | 0.9353 | 1.0000 |
| 46 | NULL-LIKE | 2 | 2 | 2 | displacement | NQ | both | BEHAVIOUR-HOMOGENEOUS | one-management-template dependent | 0.994 | 288 | 1.35 | 1.0000 | 0.9353 | 1.0000 |
| 47 | NULL-LIKE | 2 | 1 | 2 | cross_market | NQ | both | ENTRY-HOMOGENEOUS | several managements, no simple variant | 0.832 | 286 | 1.42 | 1.0000 | 1.0000 | 1.0000 |
| 48 | NULL-LIKE | 2 | 1 | 2 | multi_timeframe | NQ | both | ENTRY-HOMOGENEOUS | one-management-template dependent | 0.978 | 652 | 1.42 | 1.0000 | 1.0000 | 1.0000 |
| 49 | NULL-LIKE | 2 | 2 | 2 | multi_timeframe | NQ | both | MIXED | one-management-template dependent | 0.63 | 738 | 1.43 | 1.0000 | 0.9353 | 1.0000 |
| 50 | NULL-LIKE | 2 | 1 | 2 | momentum | NQ | both | ENTRY-HOMOGENEOUS | one-management-template dependent | 0.918 | 311 | 1.39 | 1.0000 | 1.0000 | 1.0000 |
| 51 | NULL-LIKE | 2 | 1 | 2 | mean_deviation | NQ | both | ENTRY-HOMOGENEOUS | one-management-template dependent | 1 | 270 | 1.8 | 1.0000 | 1.0000 | 1.0000 |
| 52 | NULL-LIKE | 1 | 1 | 1 | gap | NQ | long | SINGLE STRATEGY | single strategy | - | 408 | 1.31 | 1.0000 | 1.0000 | 1.0000 |
| 53 | NULL-LIKE | 1 | 1 | 1 | mean_deviation | NQ | both | SINGLE STRATEGY | single strategy | - | 249 | 1.63 | 1.0000 | 1.0000 | 1.0000 |
| 54 | NULL-LIKE | 1 | 1 | 1 | multi_timeframe | NQ | both | SINGLE STRATEGY | single strategy | - | 285 | 1.37 | 1.0000 | 1.0000 | 1.0000 |
| 55 | NULL-LIKE | 1 | 1 | 1 | mean_deviation | NQ | long | SINGLE STRATEGY | single strategy | - | 378 | 1.31 | 1.0000 | 1.0000 | 1.0000 |
| 56 | NULL-LIKE | 1 | 1 | 1 | cross_market | NQ | short | SINGLE STRATEGY | single strategy | - | 239 | 1.44 | 1.0000 | 1.0000 | 1.0000 |
| 57 | NULL-LIKE | 1 | 1 | 1 | time_of_day | NQ | long | SINGLE STRATEGY | single strategy | - | 1,243 | 1.31 | 1.0000 | 1.0000 | 1.0000 |
| 58 | NULL-LIKE | 1 | 1 | 1 | momentum | NQ | both | SINGLE STRATEGY | single strategy | - | 249 | 1.36 | 1.0000 | 1.0000 | 1.0000 |
| 59 | NULL-LIKE | 1 | 1 | 1 | fvg | NQ | both | SINGLE STRATEGY | single strategy | - | 1,360 | 1.3 | 1.0000 | 1.0000 | 1.0000 |

## 9. Short-only survivors, clustered within themselves

1,227 candidates, 70 entry rules, **47 clusters**: NULL-LIKE 45, MIXED 2.

| cluster | evidence | size | entry_rules | strong | family | instrument | median_pair_corr | median_oos_trades | median_oos_pf | p_size | p_entries | p_strong |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | MIXED | 300 | 17 | 159 | mean_deviation | NQ | 0.625 | 484 | 1.32 | 0.0398 | 0.0249 | 0.0100 |
| 1 | NULL-LIKE | 178 | 3 | 16 | cross_market | NQ | 0.701 | 93.5 | 1.79 | 0.1144 | 0.6866 | 0.3333 |
| 2 | MIXED | 171 | 2 | 148 | cross_market | NQ | 0.634 | 335 | 1.49 | 0.1194 | 0.9403 | 0.0149 |
| 3 | NULL-LIKE | 171 | 3 | 0 | momentum | NQ | 0.794 | 60 | 3.39 | 0.1194 | 0.6866 | 1.0000 |
| 4 | NULL-LIKE | 72 | 5 | 0 | fvg | NQ | 0.752 | 746 | 1.24 | 0.3582 | 0.3383 | 1.0000 |
| 5 | NULL-LIKE | 60 | 1 | 0 | compression_expansion | ES | 0.919 | 23 | 2.4 | 0.4577 | 1.0000 | 1.0000 |
| 6 | NULL-LIKE | 34 | 1 | 0 | momentum | NQ | 1 | 16 | 2.42 | 0.6468 | 1.0000 | 1.0000 |
| 7 | NULL-LIKE | 29 | 1 | 0 | momentum | NQ | 0.809 | 33 | 2.11 | 0.6965 | 1.0000 | 1.0000 |
| 8 | NULL-LIKE | 29 | 1 | 23 | cross_market | NQ | 0.715 | 665 | 1.48 | 0.6965 | 1.0000 | 0.2687 |
| 9 | NULL-LIKE | 20 | 1 | 17 | cross_market | NQ | 0.848 | 430 | 1.36 | 0.8458 | 1.0000 | 0.3184 |
| 10 | NULL-LIKE | 19 | 2 | 14 | session_open_distance | NQ | 0.637 | 288 | 1.54 | 0.8607 | 0.9403 | 0.3632 |
| 11 | NULL-LIKE | 16 | 2 | 0 | mean_deviation | NQ | 0.719 | 162 | 1.59 | 0.9055 | 0.9403 | 1.0000 |
| 12 | NULL-LIKE | 13 | 1 | 0 | fvg | NQ | 0.741 | 24 | 4.22 | 0.9652 | 1.0000 | 1.0000 |
| 13 | NULL-LIKE | 10 | 2 | 0 | momentum | NQ | 0.792 | 132 | 1.68 | 0.9751 | 0.9403 | 1.0000 |
| 14 | NULL-LIKE | 9 | 1 | 0 | overnight_range | NQ | 0.981 | 643 | 1.17 | 0.9801 | 1.0000 | 1.0000 |
| 15 | NULL-LIKE | 9 | 3 | 0 | momentum | ES | 0.83 | 137 | 1.48 | 0.9801 | 0.6866 | 1.0000 |
| 16 | NULL-LIKE | 8 | 1 | 0 | mean_deviation | NQ | 0.636 | 528 | 1.21 | 0.9851 | 1.0000 | 1.0000 |
| 17 | NULL-LIKE | 8 | 1 | 0 | momentum | NQ | 0.995 | 40 | 1.48 | 0.9851 | 1.0000 | 1.0000 |
| 18 | NULL-LIKE | 7 | 2 | 0 | momentum | ES | 0.795 | 64 | 1.95 | 0.9851 | 0.9403 | 1.0000 |
| 19 | NULL-LIKE | 6 | 1 | 0 | mean_deviation | ES | 0.93 | 7 | 10.4 | 0.9950 | 1.0000 | 1.0000 |
| 20 | NULL-LIKE | 5 | 1 | 0 | fvg | NQ | 0.994 | 22 | 1.86 | 0.9950 | 1.0000 | 1.0000 |
| 21 | NULL-LIKE | 4 | 3 | 1 | displacement | NQ | 0.718 | 265 | 1.36 | 1.0000 | 0.6866 | 0.9055 |
| 22 | NULL-LIKE | 4 | 2 | 0 | momentum | NQ | 0.679 | 75.5 | 1.81 | 1.0000 | 0.9403 | 1.0000 |
| 23 | NULL-LIKE | 4 | 1 | 0 | mean_deviation | ES | 0.696 | 46 | 1.73 | 1.0000 | 1.0000 | 1.0000 |
| 24 | NULL-LIKE | 3 | 1 | 0 | overnight_range | NQ | 0.958 | 759 | 1.11 | 1.0000 | 1.0000 | 1.0000 |
| 25 | NULL-LIKE | 3 | 1 | 0 | multi_timeframe | NQ | 0.675 | 157 | 1.36 | 1.0000 | 1.0000 | 1.0000 |
| 26 | NULL-LIKE | 3 | 2 | 1 | momentum | NQ | 0.755 | 258 | 1.22 | 1.0000 | 0.9403 | 0.9055 |
| 27 | NULL-LIKE | 3 | 1 | 0 | volatility_regime | NQ | 0.86 | 357 | 1.21 | 1.0000 | 1.0000 | 1.0000 |
| 28 | NULL-LIKE | 2 | 1 | 0 | momentum | NQ | 0.94 | 93.5 | 1.64 | 1.0000 | 1.0000 | 1.0000 |
| 29 | NULL-LIKE | 2 | 1 | 0 | cross_market | NQ | 0.844 | 1,068 | 1.17 | 1.0000 | 1.0000 | 1.0000 |
| 30 | NULL-LIKE | 2 | 1 | 0 | momentum | NQ | 0.512 | 110 | 1.52 | 1.0000 | 1.0000 | 1.0000 |
| 31 | NULL-LIKE | 2 | 1 | 0 | cross_market | NQ | 0.943 | 111 | 2.78 | 1.0000 | 1.0000 | 1.0000 |
| 32 | NULL-LIKE | 2 | 1 | 0 | cross_market | NQ | 0.96 | 525 | 1.23 | 1.0000 | 1.0000 | 1.0000 |
| 33 | NULL-LIKE | 2 | 2 | 0 | momentum | ES | 0.568 | 79.5 | 1.68 | 1.0000 | 0.9403 | 1.0000 |
| 34 | NULL-LIKE | 2 | 1 | 0 | cross_market | NQ | 0.995 | 194 | 1.73 | 1.0000 | 1.0000 | 1.0000 |
| 35 | NULL-LIKE | 2 | 1 | 0 | cross_market | NQ | 0.753 | 246 | 1.28 | 1.0000 | 1.0000 | 1.0000 |
| 36 | NULL-LIKE | 2 | 2 | 2 | multi_timeframe | NQ | 0.658 | 374 | 1.41 | 1.0000 | 0.9403 | 0.8109 |
| 37 | NULL-LIKE | 2 | 2 | 0 | mean_deviation | NQ | 0.665 | 720 | 1.23 | 1.0000 | 0.9403 | 1.0000 |
| 38 | NULL-LIKE | 1 | 1 | 0 | momentum | NQ | - | 198 | 1.21 | 1.0000 | 1.0000 | 1.0000 |
| 39 | NULL-LIKE | 1 | 1 | 0 | gap | NQ | - | 481 | 1.21 | 1.0000 | 1.0000 | 1.0000 |

Short-only net P&L by year (summed across overlapping candidates -- a concentration measure, NOT a portfolio):

| net | trades | net_share | net_per_trade | all_survivors_net_share |
|---|---|---|---|---|
| 10,348,395 | 94,661 | 12.3% | 109 | 15.9% |
| 16,183,042 | 50,825 | 19.3% | 318 | 20.5% |
| 6,800,013 | 54,081 | 8.1% | 126 | 12.2% |
| 15,924,037 | 64,930 | 19.0% | 245 | 13.4% |
| 19,799,695 | 61,236 | 23.6% | 323 | 20.4% |
| 14,744,915 | 32,684 | 17.6% | 451 | 17.6% |

## 10. Recency

Every member of every cluster was profitable in every year by construction, so 'still profitable' is not informative. Two measures are: (a) the recency class from yearly median net per trade, and (b) the cluster FOOTPRINT (all frozen candidates sharing its entry rules): its real conditional survival in 2025 and 2026 vs the same footprint in the null worlds.

| evidence | 2022-2024 DOMINATED | INTERMITTENT | PERSISTENT | RECENTLY STRONG | RECENTLY WEAK |
|---|---|---|---|---|---|
| MIXED | 0 | 1 | 4 | 2 | 0 |
| NULL-LIKE | 23 | 69 | 53 | 105 | 2 |

| evidence | above null median, not p95 | at or below null median | one of 2025/2026 above null p95 |
|---|---|---|---|
| MIXED | 6 | 1 | 0 |
| NULL-LIKE | 162 | 87 | 3 |

## 11. Parameter plateaus and entry-vs-management structure (clusters >= 5 members, real vs pooled null)

| quantity | real | null_pooled |
|---|---|---|
| mean frac_broad_plateau (clusters >= 5 members) | 0.224 | 0.186 |
| mean frac_moderate (clusters >= 5 members) | 0.358 | 0.356 |
| mean frac_narrow (clusters >= 5 members) | 0.114 | 0.155 |
| mean frac_cliff (clusters >= 5 members) | 0.165 | 0.204 |
| mean frac_entry_class_A (clusters >= 5 members) | 0.962 | 0.931 |
| share of clusters >= 5: entry edge, robust across management types | 0.758 | 0.637 |
| share of clusters >= 5: management-dependent (entries rescued by management) | 0.024 | 0.060 |
| share of clusters >= 5: one-management-template dependent | 0.040 | 0.030 |
| share of clusters >= 5: several managements, no simple variant | 0.073 | 0.108 |
| share of clusters >= 5: simple-management profitable | 0.105 | 0.165 |

| edge_type | MIXED | NULL-LIKE |
|---|---|---|
| entry edge, robust across management types | 7 | 89 |
| management-dependent (entries rescued by management) | 0 | 7 |
| one-management-template dependent | 0 | 51 |
| several managements, no simple variant | 0 | 16 |
| simple-management profitable | 0 | 25 |
| single strategy | 0 | 64 |

| homogeneity | MIXED | NULL-LIKE |
|---|---|---|
| BEHAVIOUR-HOMOGENEOUS | 1 | 72 |
| ENTRY-HOMOGENEOUS | 0 | 74 |
| MIXED | 6 | 42 |
| SINGLE STRATEGY | 0 | 64 |

## 12. Representative strategies (for explanation ONLY -- not a selection)

Medoid = the member with the highest average daily-P&L correlation to the rest of its cluster. Simplest central = among the most central quarter, the lowest entry complexity, preferring simple management, then fewest legs. Neither is chosen by performance and neither is a recommendation.

### Cluster 0 -- MIXED (1,728 members, 97 entry rules, 6 strong; fvg, MIXED, long)
Null comparison: p_size 0.0100, p_entries 0.0149, p_strong 0.9701; median pair corr 0.63; MIXED; entry edge, robust across management types; recency PERSISTENT; footprint 2025/2026: above null median, not p95.
- **medoid** `Ce1a46d861808ddd1`: ENTRY: BUY when the close is at least 0.5 x ATR60 x sqrt(60) ABOVE the midpoint of the previous 60-bar range (first bar). Orders are market orders filled at the OPEN of the next one-minute bar. MANAGEMENT: Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short). Initial stop = 1R; move the stop to breakeven after +2R; no target (held to the flat time). Always flat at the session flat time (16:00 New York). (anchor=midpoint, lookback=60, mode=continuation, window=rth, z=0.5; stop=swing; management=BE_2R_Tnone). OOS 2021-2026: 1,860 trades, WR 42.2%, PF 1.12, net $169,195 (one contract).
- **simplest_central** `C03aa1db38ea2a527`: ENTRY: BUY when price first trades back down into the most recent bullish 5-minute FVG. Orders are market orders filled at the OPEN of the next one-minute bar. MANAGEMENT: Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short). Initial stop only, no target; otherwise exit after the session flat time (16:00 New York). Always flat at the session flat time (16:00 New York). (event=touch, min_gap=0.0, mode=continuation, timeframe=5, window=rth; stop=swing; management=STOP_TIME_eod). OOS 2021-2026: 2,391 trades, WR 37.6%, PF 1.12, net $193,836 (one contract).

### Cluster 1 -- MIXED (971 members, 54 entry rules, 307 strong; momentum, MIXED, both)
Null comparison: p_size 0.0199, p_entries 0.0746, p_strong 0.0149; median pair corr 0.57; MIXED; entry edge, robust across management types; recency RECENTLY STRONG; footprint 2025/2026: above null median, not p95.
- **medoid** `C59f9d4b0b6afb79d`: ENTRY: BUY when the close has risen at least 1.5 x ATR60 x sqrt(30) above the close 30 minutes earlier (first bar this becomes true). SELL SHORT when the close has fallen at least 1.5 x ATR60 x sqrt(30) below the close 30 minutes earlier (first bar this becomes true). Orders are market orders filled at the OPEN of the next one-minute bar. MANAGEMENT: Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short). Initial stop = 1R, no target; trailing stop 2R below the highest high since entry, recomputed at every bar close, active from the start. Always flat at the session flat time (16:00 New York). (lookback=30, mode=continuation, window=rth, z=1.5; stop=swing; management=TRAIL_R_2_ACT0R). OOS 2021-2026: 1,264 trades, WR 50.0%, PF 1.32, net $348,599 (one contract).
- **simplest_central** `C0cff68a28ca8bce9`: ENTRY: BUY when the close is at least 1.0 x ATR60 x sqrt(30) ABOVE the midpoint of the previous 30-bar range (first bar). SELL SHORT when the close is at least 1.0 x ATR60 x sqrt(30) BELOW the midpoint of the previous 30-bar range (first bar). Orders are market orders filled at the OPEN of the next one-minute bar. MANAGEMENT: Initial stop 2 x ATR(14 fifteen-minute bars) from the entry. Initial stop only, no target; otherwise exit after the session flat time (16:00 New York). Always flat at the session flat time (16:00 New York). (anchor=midpoint, lookback=30, mode=continuation, window=rth, z=1.0; stop=atr mult=2.0; management=STOP_TIME_eod). OOS 2021-2026: 1,141 trades, WR 37.9%, PF 1.43, net $343,936 (one contract).

### Cluster 2 -- MIXED (903 members, 25 entry rules, 724 strong; mean_deviation, MIXED, long)
Null comparison: p_size 0.0199, p_entries 0.1741, p_strong 0.0050; median pair corr 0.61; MIXED; entry edge, robust across management types; recency RECENTLY STRONG; footprint 2025/2026: above null median, not p95.
- **medoid** `Cde07e4a776a3c324`: ENTRY: BUY when the close is at least 1.0 x ATR60 x sqrt(60) ABOVE the average of the previous 60 closes (first bar). Orders are market orders filled at the OPEN of the next one-minute bar. MANAGEMENT: Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short). Initial stop = 1R; move the stop to breakeven after +1R; target +3R. Always flat at the session flat time (16:00 New York). (anchor=sma, lookback=60, mode=continuation, window=rth, z=1.0; stop=swing; management=BE_1R_T3R). OOS 2021-2026: 383 trades, WR 52.2%, PF 1.70, net $179,478 (one contract).
- **simplest_central** `C36109383948c81a5`: ENTRY: BUY when the close is at least 1.0 x ATR60 x sqrt(30) ABOVE the midpoint of the previous 30-bar range (first bar). Orders are market orders filled at the OPEN of the next one-minute bar. MANAGEMENT: Initial stop 2 x ATR(14 fifteen-minute bars) from the entry. Initial stop = 1R, single target at +4R. Always flat at the session flat time (16:00 New York). (anchor=midpoint, lookback=30, mode=continuation, window=rth, z=1.0; stop=atr mult=2.0; management=RR_4R). OOS 2021-2026: 518 trades, WR 41.3%, PF 1.59, net $190,363 (one contract).

### Cluster 3 -- MIXED (554 members, 13 entry rules, 442 strong; mean_deviation, MIXED, MIXED)
Null comparison: p_size 0.0697, p_entries 0.4279, p_strong 0.0050; median pair corr 0.64; MIXED; entry edge, robust across management types; recency PERSISTENT; footprint 2025/2026: above null median, not p95.
- **medoid** `C31113be081de0358`: ENTRY: BUY when the close is at least 1.5 x ATR60 x sqrt(30) ABOVE the average of the previous 30 closes (first bar). SELL SHORT when the close is at least 1.5 x ATR60 x sqrt(30) BELOW the average of the previous 30 closes (first bar). Orders are market orders filled at the OPEN of the next one-minute bar. MANAGEMENT: Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short). Initial stop = 1R, no target; trailing stop 2R below the highest high since entry, recomputed at every bar close, active once the trade has been +1R in favour. Always flat at the session flat time (16:00 New York). (anchor=sma, lookback=30, mode=continuation, window=rth, z=1.5; stop=swing; management=TRAIL_R_2_ACT1R). OOS 2021-2026: 363 trades, WR 48.5%, PF 1.52, net $171,158 (one contract).
- **simplest_central** `C09ff049e953f8718`: ENTRY: BUY when the close is at least 2.0 x ATR60 x sqrt(15) ABOVE the average of the previous 15 closes (first bar). SELL SHORT when the close is at least 2.0 x ATR60 x sqrt(15) BELOW the average of the previous 15 closes (first bar). Orders are market orders filled at the OPEN of the next one-minute bar. MANAGEMENT: Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short). Initial stop = 1R, single target at +4R. Always flat at the session flat time (16:00 New York). (anchor=sma, lookback=15, mode=continuation, window=rth, z=2.0; stop=swing; management=RR_4R). OOS 2021-2026: 252 trades, WR 47.2%, PF 1.61, net $138,567 (one contract).

### Cluster 4 -- MIXED (473 members, 11 entry rules, 260 strong; mean_deviation, MIXED, MIXED)
Null comparison: p_size 0.1045, p_entries 0.4826, p_strong 0.0249; median pair corr 0.64; MIXED; entry edge, robust across management types; recency INTERMITTENT; footprint 2025/2026: at or below null median.
- **medoid** `C721c7e439e4c22ec`: ENTRY: BUY when the close is at least 1.0 x ATR60 x sqrt(120) ABOVE the average of the previous 120 closes (first bar). Orders are market orders filled at the OPEN of the next one-minute bar. MANAGEMENT: Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short). Initial stop = 1R; move the stop to breakeven after +0.75R; target +3R. Always flat at the session flat time (16:00 New York). (anchor=sma, lookback=120, mode=continuation, window=rth, z=1.0; stop=swing; management=BE_0.75R_T3R). OOS 2021-2026: 244 trades, WR 55.3%, PF 1.76, net $121,564 (one contract).
- **simplest_central** `C10abb691f657ef8d`: ENTRY: BUY when the close is at least 1.0 x ATR60 x sqrt(120) ABOVE the average of the previous 120 closes (first bar). Orders are market orders filled at the OPEN of the next one-minute bar. MANAGEMENT: Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short). Initial stop only, no target; otherwise exit after the session flat time (16:00 New York). Always flat at the session flat time (16:00 New York). (anchor=sma, lookback=120, mode=continuation, window=rth, z=1.0; stop=swing; management=STOP_TIME_eod). OOS 2021-2026: 243 trades, WR 58.0%, PF 1.65, net $112,948 (one contract).

### Cluster 5 -- MIXED (373 members, 9 entry rules, 286 strong; momentum, NQ, MIXED)
Null comparison: p_size 0.1443, p_entries 0.5821, p_strong 0.0149; median pair corr 0.64; MIXED; entry edge, robust across management types; recency PERSISTENT; footprint 2025/2026: above null median, not p95.
- **medoid** `C27380cdc71dc1bf9`: ENTRY: BUY when the close has risen at least 1.5 x ATR60 x sqrt(60) above the close 60 minutes earlier (first bar this becomes true). SELL SHORT when the close has fallen at least 1.5 x ATR60 x sqrt(60) below the close 60 minutes earlier (first bar this becomes true). Orders are market orders filled at the OPEN of the next one-minute bar. MANAGEMENT: Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short). Initial stop = 1R, no target; trailing stop 3 ATR below the highest high since entry (above the lowest low for shorts), recomputed at every bar close, active once the trade has been +1.5R in favour. Always flat at the session flat time (16:00 New York). (lookback=60, mode=continuation, window=rth, z=1.5; stop=swing; management=TRAIL_ATR_3_ACT1.5R). OOS 2021-2026: 778 trades, WR 54.5%, PF 1.34, net $220,823 (one contract).
- **simplest_central** `C002d474c224d1907`: ENTRY: BUY when the close has risen at least 1.5 x ATR60 x sqrt(60) above the close 60 minutes earlier (first bar this becomes true). SELL SHORT when the close has fallen at least 1.5 x ATR60 x sqrt(60) below the close 60 minutes earlier (first bar this becomes true). Orders are market orders filled at the OPEN of the next one-minute bar. MANAGEMENT: Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short). Initial stop = 1R, single target at +1.25R. Always flat at the session flat time (16:00 New York). (lookback=60, mode=continuation, window=rth, z=1.5; stop=swing; management=RR_1.25R). OOS 2021-2026: 821 trades, WR 54.9%, PF 1.27, net $182,346 (one contract).

### Cluster 7 -- MIXED (293 members, 2 entry rules, 271 strong; momentum, NQ, MIXED)
Null comparison: p_size 0.2189, p_entries 1.0000, p_strong 0.0149; median pair corr 0.67; BEHAVIOUR-HOMOGENEOUS; entry edge, robust across management types; recency PERSISTENT; footprint 2025/2026: above null median, not p95.
- **medoid** `Cef95b7cf49251506`: ENTRY: BUY when the close has risen at least 1.0 x ATR60 x sqrt(240) above the close 240 minutes earlier (first bar this becomes true). Orders are market orders filled at the OPEN of the next one-minute bar. MANAGEMENT: Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short). Take 50% at +1R; the runner is held to the session close. Always flat at the session flat time (16:00 New York). (lookback=240, mode=continuation, window=rth_am, z=1.0; stop=swing; management=RUNNER_EOD). OOS 2021-2026: 289 trades, WR 56.1%, PF 1.40, net $73,116 (one contract).
- **simplest_central** `C3dc5dc6a88e523c7`: ENTRY: BUY when the close has risen at least 1.0 x ATR60 x sqrt(240) above the close 240 minutes earlier (first bar this becomes true). Orders are market orders filled at the OPEN of the next one-minute bar. MANAGEMENT: Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short). Initial stop = 1R, single target at +2R. Always flat at the session flat time (16:00 New York). (lookback=240, mode=continuation, window=rth_am, z=1.0; stop=swing; management=RR_2R). OOS 2021-2026: 293 trades, WR 57.0%, PF 1.38, net $74,243 (one contract).


## 13. What this does and does not show

Written by the analyst after the pre-registered analysis ran, from `cluster_summary.csv` and
`tables/`. It changes no classification.

### 1. Redundancy: 11,462 survivors are about 259 behaviours

- **567 entry rules; 259 primary P&L clusters.** Median cluster size is 4. The largest cluster
  holds 1,728 members (97 entry rules, mostly long FVG). 64 singletons.
- **The count depends on how "the same" is defined, but it is stable in order of magnitude:**
  - P&L view: 2,482 clusters at rho 0.9, 731 at 0.7, 259 at 0.5 and 94 at 0.3.
  - Entry-overlap view: 1,527, 635, 460 and 286 at the same four levels.
- **The two views agree at the tight end (ARI 0.67 at 0.9) and diverge at the primary level.**
  78% of entry-overlap pairs are also P&L pairs. Only 16% of P&L pairs share entries, so many
  P&L clusters join DIFFERENT entries that carry the same daily exposure. This is why P&L is the
  primary view: entry rules undercount the redundancy.
- 22 clusters of >= 100 members hold most of the survivors; 93% of all survivors sit in
  clusters of >= 20.

### 2. Real vs null at the level of behaviours

- **The excess is many behaviours, not one giant family.** The real market has more distinct
  surviving behaviours than any null world:
  - 259 clusters vs null median 102 and max 184.
  - Clusters of >= 20 members: 69 vs 12 (max 39).
  - Clusters of >= 100: 22 vs 1 (max 11).
  - High-confidence clusters (>= 10 members, >= 2 entry rules, >= 5 strong members, median
    PF >= 1.2): 38 vs null median 4 and max 21.
  - All at p = 0.005, the smallest attainable with 200 worlds.
- **No single cluster of the full survivor set is individually beyond every null world.** Some
  chance world always produced a cluster as large as each real one (the null world maximum
  reaches 1,781 members). Result: 0 CLEARLY ABOVE NULL, 7 MIXED, 252 NULL-LIKE.
- The 7 MIXED clusters are the large FVG, momentum and mean-deviation clusters (293-1,728
  members). Each passes on size or strong-member count, never on all three dimensions together.
- Per-cluster evidence is much weaker than cohort-level evidence. The funnel's excess is spread
  across dozens of medium and large behaviours, each of which on its own looks like something a
  lucky null world could produce.
- **In the stronger subset** (>= 200 OOS trades AND OOS PF >= 1.3; 4,362 candidates, 138 entry
  rules):
  - 70 clusters vs null median 19 and max 48.
  - 3 clusters are CLEARLY ABOVE NULL. No null world produced a strong cluster this large with
    this many strong members:
    - mean deviation, long, NQ+ES: 981 members, 22 entry rules
    - momentum, NQ: 632 members, 22 entry rules
    - mean deviation, both directions, NQ: 496 members, 9 entry rules
  - 3 are MIXED: cross-market NQ (298 members), momentum NQ (271 members, 2 entry rules) and
    momentum NQ (62 members).
  - The other 64 are NULL-LIKE.
- **Families:**
  - Momentum, mean deviation and cross-market lead on every family-level measure (survivors,
    entry rules, clusters, strong members, high-confidence clusters; p <= 0.02).
  - FVG has many survivors, clusters and entry rules, but almost no strong members (2 vs null
    median 1). Its large cluster is low-PF (median 1.13), high-frequency and long.
  - Gap, overnight range, rolling breakout, price structure, time of day and failed breakout are
    null-like on clusters.
- **High frequency is many independent behaviours, but concentrated:**
  - 2,500+ OOS trades: 23 clusters vs null median 3 (p95 11), but 54% of those survivors sit in
    one cluster.
  - 1,000-2,500 OOS trades: 81 clusters vs 19 (p95 41), 39% in the largest.
  - Higher frequency means thinner per-trade margins: median PF 1.09 at 2,500+ vs 1.43 at
    200-500.
- **Structure:**
  - Real clusters of >= 5 members are more often "entry edge, robust across management types"
    than null clusters (76% vs 64%).
  - They are less often management-dependent (2% vs 6%) or cliff-heavy (cliff share 17% vs 20%).
  - They are slightly more often on broad plateaus (22% vs 19%).
  - The differences are modest. The excess looks like predictive entries rather than payoff
    shaping, but plateau structure does not separate real from null strongly.
- **Short-only** (1,227 candidates, 70 entry rules): 47 clusters vs null median 22.5 (p = 0.045).
  - Entry rules: p = 0.035. Clusters >= 100 members: 4 vs null max 5 (p = 0.015).
  - Two MIXED clusters (mean deviation NQ, 300 members; cross-market NQ, 171 members); no
    CLEARLY.
  - Short-only net is not concentrated in 2022-2024 (46% of the six-period total, vs 46% for all
    survivors). 2025 and 2026 are 24% and 18%.
  - Modest evidence, consistent with the null funnel.
- **Recency:**
  - All members were profitable every year by construction. On per-trade strength, 57 clusters
    are PERSISTENT, 107 RECENTLY STRONG, 23 2022-2024 DOMINATED, 70 INTERMITTENT and 2
    RECENTLY WEAK. Of the 7 MIXED clusters: 4 PERSISTENT, 2 RECENTLY STRONG, 1 INTERMITTENT.
  - Footprint test (all candidates sharing the cluster's entry rules): in 2025 and 2026 the real
    conditional survival is above the null MEDIAN for 6 of the 7 MIXED clusters, but above the
    null p95 for none. Only 3 of all 259 clusters exceed the null p95 in either year.
  - The recent signal is positive but no longer statistically unusual. This matches the null
    funnel: most of the excess was earned in 2022-2024.

### 3. Supported

- The survivors contain many more distinct profitable behaviours than chance produces under the
  null, and the excess is spread across dozens of clusters, not one.
- Within the stronger subset, three behaviours (two mean-deviation, one momentum; NQ-led) are
  individually beyond every null world, and three more are borderline.

### 4. Not supported

- That any MEMBER of those clusters has an edge rather than sharing a cluster that does.
- That the full-survivor clusters are individually unusual: none is CLEARLY ABOVE NULL.
- That FVG's large cluster, short-only or high-frequency survival is strong individual evidence.
- That the effect is still unusual in 2025-2026: positive, but within the null range.
- That these clusters would survive in the future. Only the untouched forward period can test that.


## 14. Forward-test start date (verification only; no data read)

- Official cutoff: NQ 2026-08-10 19:59:00-04:00, ES 2026-08-14 16:59:00-04:00.
- Last session any bar of which was read: NQ 2026-08-11, ES 2026-08-14.
- **First session untouched for BOTH instruments: 2026-08-17** (opens 2026-08-16 18:00 (a Monday session opens Sunday evening) New York). NQ sessions after its last partially-read session were never read (absent from the file); the common start is the first session after the later (ES) cutoff. CME holiday calendar not consulted: 2026-08-17 is not a US market holiday.

## 15. Integrity (end of stage)

# EDGE ISOLATION -- INTEGRITY CHECK (END, 2026-09-22 16:58 UTC)

REAL_DATA_CUTOFF: NQ 2026-08-10 19:59:00-04:00, ES 2026-08-14 16:59:00-04:00

| check | result | detail |
|---|---|---|
| Archive manifest hash unchanged | PASS | cfe9dc59ccd12762e46a32a889fbc119bcd69aa9adaf26b1acbe588ef371c5cb |
| All 192 archived files match their hashes | PASS | 0 |
| results/main files identical to the archive | PASS | [] |
| Large official files (frozen cohort, stage results) unchanged | PASS | [] |
| Official trade files unchanged | PASS | [] |
| Official freeze verifies and its hash is unchanged | PASS | c6da1c8ad6908f9a4ce94d8ed8e4cf5084bc465b94effd750556627be00f1d6b |
| Null-funnel world files match their checkpoint hashes (200 worlds) | PASS | [] |
| Null-funnel results unchanged since the start of this stage | PASS | [] |
| Official ledger unchanged | PASS |  |
| Null ledger: no bar past the per-instrument cutoff | PASS | 12 entries |
| No cached real-market extract past the cutoff | PASS | 2026-08-14 16:59:00-04:00 |
| Null source arrays (cache/null_source) within the cutoff | PASS |  |
| Edge-isolation stage made no guarded market-data load (no ledger of its own) | PASS |  |
| Tests | PASS | 87 passed, 0 failed |

**ALL CHECKS PASSED**

## 16. Files

- `cluster_summary.csv/.parquet` (every primary cluster); `tables/cluster_summary_strong|short.*`; `tables/real_vs_null_cluster_counts.csv`, `family_level.csv`, `high_frequency_buckets.csv`, `short_only_by_year.csv`, `structure_real_vs_null.csv`.
- `real/` labels at every level, both views; survivor stats; yearly stats; daily P&L matrix. `null_worlds/` per-world cluster tables, labels and exact-reproduction checks.
- `CLUSTERING_PREREGISTRATION.md`, `CLUSTER_EVIDENCE_PREREGISTRATION.md` (+ sha256), `PROPOSED_FINAL_SELECTION_RULE.md`, `integrity/`.
