# QuantLabV3 — MASTER RESEARCH RECORD (first V3 campaign)

Generated 2026-09-22 19:30 (New York). Research freeze **2026-09-22 19:27:42.806385-04:00**. Final cohort freeze sha256 `f5666dac728aa2539b2f8223309012914d71923ab71f3363e9e035344ace8f03`.

**Historical V3 research is complete. The final cohort is frozen. No post-freeze future performance has been assumed.** True forward starts with session **2026-09-24** and has not started.

How to read this: every number below is net of costs at the BASELINE scenario ($14.00 per NQ round trip, $29.00 per ES round trip: $4 commission + 1 tick slippage per side) for one contract, unless labelled GROSS, MODERATE or STRESS ($26 NQ / $56 ES). 'PF' = profit factor, 'WR' = win rate, 't' = t-statistic of the mean net trade, 'D' = the mean RTH range of the previous 10 sessions, 'ATRh' = ATR(14) of 15-minute bars.

Periods (CME sessions, 18:00-17:00 New York): DISCOVERY 2010-06-07..2018-12-31; CONFIRMATION 2019..2022; UNTOUCHED HOLDOUT 2023..2025; 2026 SECONDARY HISTORICAL AUDIT 2026-01-01..2026-08-14 (all data that exists); TRUE FORWARD from 2026-09-24.

## A. Engine verification

- Test suite: **207 passed in 48.63s** at the end (82 inherited V2 tests + 13 isolation tests + V3 tests for the swing trail, statistics, features, stops, natural targets, catalog causality, known answers, null generator, evidence rules).
- Real-data look-ahead check (DISCOVERY window 2016-01-04..2016-06-30): every one of the 53 families x every grid point x every Stage-A and Stage-B management = **15,091 spec checks, 1,794,805 trades compared, 0 problems**; every family fired signals before its cut.
- Coverage of the required checks: next-bar entries, stop fills and gaps, 1-tick target trade-through, pessimistic same-bar stop/target, breakeven timing and same-bar ambiguity, trailing stops applied from the next bar only, partial exits and their cost accounting, session flat and no position across sessions, contract rolls (no window spans a roll), DST, costs, P&L / PF / drawdown / streak (V3 fast statistics = reference metrics).
- Stage gate: in DISCOVERY the REAL gate refused CONFIRMATION, FINAL_HOLDOUT and SEALED_2026 ({'CONFIRMATION': True, 'FINAL_HOLDOUT': True, 'SEALED_2026': True}); discovery partition hashes matched ({'NQ': True, 'ES': True}).
- Smoke test on DISCOVERY: 117 specs, 755,405 trades, 33 ms/spec. Latest bar read before discovery: 2018-12-31 16:59:00-05:00.
- Bugs found and fixed: (1) *null p-value for strategies with < 2 trades* in the holdout/audit script (undefined t treated as +inf, p = 1/101 instead of 1) -- only the 2026 X3 row (0 trades) was affected; sealed files left unchanged, erratum `results/audit2026/ERRATUM_2026-09-22.json`, code fixed, regression test added. (2) Pre-freeze development fixes found by tests/dry runs: the pullback kernel counted the low of the bar that set a new extreme (order unknowable) -- now conservative; the other market's null rebuild restarted at missing minutes -- now continues across them; Numba typing of the carried close. No engine bug was found in the inherited V2 execution kernel.
- Deviation from the V3 README (accepted by the brief): research ran as Administrator with software/stage-gate isolation only (no OS-level hard isolation).

## B. Exact strategy catalog tested

53 families = hypotheses H01-H50 of the brief + 3 executor hypotheses (X1 turn-of-month long; X2 first half-hour -> last half-hour; X3 correlation-regime momentum), all preregistered before any discovery result (`preregistration/V3_DISCOVERY_PREREGISTRATION.md` lists every rule, grid and ablated condition). NQ is traded for every hypothesis except H22 (ES traded, NQ as leader). Entries RTH 09:30-15:30 New York (X2: to 15:45), always flat by 16:00, one contract, one position at a time, signal at a bar close -> market order at the next bar's open.

| hypothesis | family | section | specs | entries |
|---|---|---|---|---|
| H01 | v3_h01_efficient_momentum | A | 2157 | 81 |
| H02 | v3_h02_momentum_acceleration | A | 1380 | 84 |
| H03 | v3_h03_multi_horizon | A | 802 | 42 |
| H04 | v3_h04_htf_trend_impulse | A | 1704 | 72 |
| H05 | v3_h05_vol_shock_momentum | A | 1088 | 48 |
| H06 | v3_h06_compression_expansion | A | 756 | 36 |
| H07 | v3_h07_opening_drive | A | 964 | 36 |
| H08 | v3_h08_morning_trend | A | 1392 | 48 |
| H09 | v3_h09_last_hour_trend | A | 696 | 24 |
| H10 | v3_h10_impulse_pullback | A | 992 | 48 |
| H11 | v3_h11_failed_countertrend | A | 836 | 36 |
| H12 | v3_h12_breakout_acceptance | A | 793 | 45 |
| H13 | v3_h13_overextension | B | 501 | 27 |
| H14 | v3_h14_deceleration_exhaustion | B | 712 | 36 |
| H15 | v3_h15_session_extreme_rejection | B | 284 | 18 |
| H16 | v3_h16_pdhl_failed_break | B | 462 | 18 |
| H17 | v3_h17_overnight_failed_break | B | 382 | 18 |
| H18 | v3_h18_or_failed_breakout | B | 568 | 24 |
| H19 | v3_h19_large_morning_reversal | B | 494 | 18 |
| H20 | v3_h20_extreme_move_path | B | 1128 | 48 |
| H21 | v3_h21_es_leads_nq | C | 512 | 24 |
| H22 | v3_h22_nq_leads_es | C | 384 | 24 |
| H23 | v3_h23_relative_momentum | C | 410 | 18 |
| H24 | v3_h24_beta_residual_reversion | C | 270 | 18 |
| H25 | v3_h25_corr_breakdown | C | 564 | 24 |
| H26 | v3_h26_smt_nonconfirmation | C | 504 | 36 |
| H27 | v3_h27_cross_confirm_momentum | C | 756 | 36 |
| H28 | v3_h28_disagreement_reversal | C | 400 | 24 |
| H29 | v3_h29_relative_acceleration | C | 472 | 24 |
| H30 | v3_h30_path_efficiency_cont | D | 410 | 18 |
| H31 | v3_h31_low_efficiency_reversal | D | 432 | 24 |
| H32 | v3_h32_speed_shock | D | 404 | 24 |
| H33 | v3_h33_acceleration | D | 410 | 18 |
| H34 | v3_h34_deceleration | D | 168 | 12 |
| H35 | v3_h35_pullback_quality | D | 394 | 18 |
| H36 | v3_h36_time_since_extreme | D | 500 | 24 |
| H37 | v3_h37_rv_shock | E | 580 | 24 |
| H38 | v3_h38_vol_of_vol | E | 452 | 24 |
| H39 | v3_h39_intraday_compression_breakout | E | 282 | 18 |
| H40 | v3_h40_daily_compression | E | 298 | 18 |
| H41 | v3_h41_vr_trending | E | 758 | 30 |
| H42 | v3_h42_vr_mean_reverting | E | 610 | 30 |
| H43 | v3_h43_pos_autocorr_momentum | E | 458 | 18 |
| H44 | v3_h44_neg_autocorr_meanrev | E | 318 | 18 |
| H45 | v3_h45_early_trend_day | F | 522 | 18 |
| H46 | v3_h46_early_range_day | F | 414 | 18 |
| H47 | v3_h47_overnight_same_dir_open | F | 648 | 24 |
| H48 | v3_h48_overnight_opening_rejection | F | 584 | 24 |
| H49 | v3_h49_morning_range_pm | F | 596 | 24 |
| H50 | v3_h50_trend_lunch_pm | F | 772 | 36 |
| X1 | v3_x1_turn_of_month | X | 42 | 2 |
| X2 | v3_x2_first_to_last_half_hour | X | 156 | 12 |
| X3 | v3_x3_corr_regime_momentum | X | 506 | 18 |

## C. Search-space size

- signal configurations **511**, entries (x direction) **1,529**, Stage-A specs **20,693**, Stage-B maximum **24,464** -> maximum **45,157** (budget ~150,000). Actually evaluated: **33,077** (Stage B ran only for the 774 entries with any positive Stage-A variant).
- Management: Stage A 13-17 single-exit variants per entry (1 ATR stop x R-target ladder / EOD / 60-min time exit; 1.5 ATR and structural stops x 3 exits; natural targets for reversal families; 2/5/10-minute time exits for the lead-lag families). Stage B 16 variants (breakeven 0.5/1/1.5R, ATR trails 1.5/2/3 and a confirmed-swing trail, four partial/runner plans, two combinations) on the 1-ATR stop, each compared with its Stage-A control.

## D. Discovery results (2010-06-07 .. 2018-12-31)

- 33,077 specs: **PRIMARY 2,403** (trades >= 30, BASELINE net > 0, t >= 1), WEAK_POSITIVE 6,209, LOW_SAMPLE 40, MODERATE_ONLY 4,592, GROSS_ONLY 10,536, NEGATIVE 9,141, no trades 156.
- BASELINE-profitable specs: **8,652**; STRESS-profitable: 3,300; PRIMARY with negative STRESS: 360; regime-conditional PRIMARY: 394.
- Distinct behaviours among the 2,403 PRIMARY specs (discovery daily-P&L clustering): **90 at rho 0.50** (41 at 0.30, 259 at 0.70, 1028 at 0.90); 367 distinct entry rules; 2,321 distinct trade lists.
- Strongest families (share of specs PRIMARY): H09 last-hour trend, H08 morning trend, X3, H47 overnight + same-direction open, H45 early trend-day, H07 opening drive, H41 VR-trending momentum. Weakest (no PRIMARY at all): H15, H17, H22, H24, H26, H28, H29, H34, H44, X1, X2 -- i.e. most fades of extremes, the NQ->ES lead, the beta residual, SMT, and both new calendar/intraday-momentum ideas.

| hypothesis | specs | primary | weak_pos | moderate_only | gross_only | baseline_positive | stress_positive | best_t | median_trades | median_pf |
|---|---|---|---|---|---|---|---|---|---|---|
| H08 | 1392 | 368 | 598 | 159 | 200 | 966 | 554 | 2.68 | 341 | 1.08 |
| H09 | 696 | 336 | 257 | 55 | 47 | 593 | 376 | 2.85 | 342 | 1.18 |
| H01 | 2157 | 261 | 545 | 540 | 682 | 806 | 154 | 2.56 | 3,208 | 0.976 |
| H07 | 964 | 162 | 335 | 113 | 180 | 497 | 259 | 2.25 | 305 | 1.01 |
| H47 | 648 | 122 | 151 | 59 | 116 | 273 | 160 | 2.4 | 234 | 0.944 |
| H41 | 758 | 119 | 200 | 126 | 229 | 319 | 145 | 2.69 | 958 | 0.977 |
| X3 | 506 | 119 | 135 | 86 | 129 | 254 | 130 | 2.49 | 835 | 1 |
| H04 | 1704 | 103 | 362 | 386 | 676 | 465 | 53 | 1.87 | 3,188 | 0.956 |
| H45 | 522 | 95 | 215 | 79 | 78 | 310 | 156 | 2.27 | 332 | 1.03 |
| H50 | 772 | 89 | 186 | 60 | 135 | 287 | 149 | 1.84 | 100 | 0.98 |
| H20 | 1128 | 80 | 265 | 110 | 243 | 345 | 154 | 2.41 | 821 | 0.935 |
| H19 | 494 | 62 | 86 | 38 | 80 | 148 | 91 | 1.9 | 286 | 0.891 |
| H05 | 1088 | 50 | 270 | 183 | 384 | 320 | 146 | 1.86 | 1,298 | 0.955 |
| H49 | 596 | 40 | 180 | 31 | 54 | 248 | 151 | 1.96 | 123 | 0.931 |
| H25 | 564 | 40 | 99 | 58 | 144 | 139 | 57 | 2.16 | 523 | 0.83 |
| H06 | 756 | 38 | 108 | 147 | 367 | 146 | 24 | 2.13 | 1,856 | 0.92 |
| H11 | 836 | 38 | 207 | 170 | 334 | 245 | 43 | 1.6 | 2,130 | 0.957 |
| H10 | 992 | 32 | 170 | 203 | 472 | 202 | 21 | 2.47 | 2,995 | 0.941 |
| H14 | 712 | 31 | 77 | 18 | 78 | 108 | 72 | 1.81 | 412 | 0.808 |
| H03 | 802 | 23 | 119 | 168 | 377 | 142 | 7 | 1.67 | 5,088 | 0.936 |
| H43 | 458 | 23 | 84 | 91 | 206 | 107 | 16 | 2.51 | 2,876 | 0.942 |
| H42 | 610 | 21 | 61 | 30 | 85 | 82 | 40 | 2.14 | 467 | 0.785 |
| H48 | 584 | 20 | 86 | 33 | 134 | 106 | 49 | 2.42 | 221 | 0.83 |
| H38 | 452 | 19 | 51 | 33 | 110 | 70 | 33 | 1.78 | 1,734 | 0.831 |
| H21 | 512 | 17 | 51 | 43 | 204 | 68 | 26 | 1.92 | 3,170 | 0.887 |
| H16 | 462 | 16 | 114 | 101 | 134 | 130 | 18 | 1.72 | 606 | 0.938 |
| H36 | 500 | 13 | 110 | 100 | 96 | 123 | 0 | 1.38 | 1,136 | 0.932 |
| H35 | 394 | 12 | 127 | 78 | 148 | 139 | 53 | 1.59 | 1,188 | 0.968 |
| H31 | 432 | 10 | 70 | 31 | 59 | 80 | 44 | 1.52 | 924 | 0.87 |
| H02 | 1380 | 10 | 105 | 216 | 936 | 115 | 0 | 1.37 | 5,851 | 0.929 |
| H27 | 756 | 6 | 76 | 179 | 436 | 82 | 0 | 1.39 | 5,392 | 0.936 |
| H30 | 410 | 5 | 48 | 98 | 230 | 53 | 1 | 1.52 | 5,076 | 0.931 |
| H46 | 414 | 4 | 53 | 35 | 107 | 57 | 17 | 1.41 | 414 | 0.84 |
| H12 | 793 | 4 | 59 | 110 | 315 | 63 | 7 | 1.53 | 2,141 | 0.886 |
| H33 | 410 | 3 | 66 | 83 | 238 | 69 | 0 | 1.21 | 3,924 | 0.94 |
| H37 | 580 | 3 | 144 | 52 | 113 | 147 | 58 | 1.29 | 299 | 0.915 |
| H40 | 298 | 2 | 39 | 19 | 67 | 41 | 8 | 1.25 | 374 | 0.834 |
| H13 | 501 | 2 | 36 | 32 | 101 | 38 | 7 | 1.6 | 889 | 0.834 |
| H18 | 568 | 2 | 65 | 103 | 246 | 67 | 3 | 1.4 | 1,158 | 0.874 |
| H39 | 282 | 1 | 29 | 31 | 141 | 30 | 1 | 1.27 | 1,680 | 0.883 |
| H32 | 404 | 1 | 16 | 38 | 164 | 17 | 0 | 1.01 | 2,938 | 0.893 |
| H23 | 410 | 1 | 60 | 49 | 143 | 61 | 9 | 1.05 | 1,106 | 0.901 |
| H17 | 382 | 0 | 37 | 69 | 224 | 37 | 0 | 0.724 | 992 | 0.896 |
| H15 | 284 | 0 | 8 | 15 | 99 | 8 | 0 | 0.711 | 1,437 | 0.837 |
| H29 | 472 | 0 | 18 | 70 | 277 | 18 | 0 | 0.915 | 3,460 | 0.908 |
| H34 | 168 | 0 | 0 | 0 | 9 | 0 | 0 | -0.595 | 3,370 | 0.78 |
| H26 | 504 | 0 | 0 | 2 | 87 | 0 | 0 | -0.283 | 5,824 | 0.807 |
| H28 | 400 | 0 | 13 | 39 | 131 | 13 | 0 | 0.345 | 1,171 | 0.852 |
| H22 | 384 | 0 | 0 | 2 | 125 | 0 | 0 | -0.99 | 4,624 | 0.735 |
| H24 | 270 | 0 | 0 | 0 | 36 | 0 | 0 | -0.473 | 2,149 | 0.753 |
| H44 | 318 | 0 | 17 | 9 | 34 | 17 | 8 | 0.736 | 997 | 0.788 |
| X1 | 42 | 0 | 1 | 6 | 15 | 1 | 0 | 0.0872 | 103 | 0.811 |
| X2 | 156 | 0 | 0 | 6 | 81 | 0 | 0 | -0.31 | 984 | 0.812 |

Sub-periods (P1 2010-12, P2 2013-15, P3 2016-18) and yearly results for every spec: `results/discovery/discovery_labelled.parquet`; per-family: `subperiods.csv`, `direction_breakdown.csv`.

## E. Confluence / ablation results

Each spec with a confluence condition was compared with the identical spec without it (same entry parameters, direction and management). 'improved' = average net trade higher. The confirmation column uses only pairs in which both specs were frozen, so it is descriptive.

| hypothesis | condition | pairs | trades_removed | d_avg | improved | d_pf | d_wr | d_t | d_mdd | sub2 | child_pos | parent_pos | pairs_both_frozen | conf_share_improved | conf_median_d_avg |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H01 | pe | 1310 | 0.209 | 2.1 | 0.687 | 0.0188 | 0.00568 | 0.436 | -8,253 | 0.679 | 0.428 | 0.29 | 655 | 0.901 | 26.3 |
| H02 | acc | 468 | 0.319 | 4.08 | 0.981 | 0.0386 | 0.0153 | 1.85 | -59,472 | 0.953 | 0.0641 | 0 | 14 | 1 | 42.8 |
| H03 | h120 | 266 | 0.458 | 5.9 | 0.974 | 0.0583 | 0.0113 | 2.17 | -49,586 | 0.955 | 0.308 | 0.015 | 40 | 0.725 | 6.86 |
| H03 | h30 | 330 | 0.176 | 4.46 | 0.945 | 0.0416 | 0.00877 | 1.01 | -17,353 | 0.882 | 0.288 | 0.139 | 102 | 0.745 | 7.7 |
| H03 | h5 | 346 | 0.00749 | -0.414 | 0.422 | -0.00317 | -0.000681 | -0.139 | 2,301 | 0.454 | 0.205 | 0.205 | 132 | 0.22 | -9.64 |
| H04 | zh | 408 | 0.457 | 7.31 | 0.985 | 0.0637 | 0.0113 | 1.91 | -43,778 | 0.961 | 0.436 | 0.0833 | 94 | 0.457 | -1.26 |
| H04 | zi | 440 | 0.193 | 5.51 | 0.945 | 0.0599 | 0.0138 | 1.33 | -14,320 | 0.916 | 0.339 | 0.1 | 127 | 0.228 | -16 |
| H05 | v | 676 | 0.813 | 1.73 | 0.562 | 0.03 | 0.00304 | 1.41 | -40,296 | 0.49 | 0.318 | 0.0976 | 152 | 0.421 | -12.3 |
| H06 | cth | 312 | 0.764 | 4.26 | 0.798 | 0.0223 | 0.0214 | 1.7 | -61,924 | 0.769 | 0.263 | 0 | 9 | 0.889 | 21.2 |
| H06 | strong | 362 | 0.263 | 1.9 | 0.854 | 0.0256 | 0.0108 | 0.818 | -8,335 | 0.848 | 0.257 | 0.135 | 110 | 0.5 | -0.176 |
| H07 | e | 600 | 0.331 | 3.71 | 0.72 | 0.0394 | 0.00831 | 0.244 | -2,072 | 0.677 | 0.56 | 0.423 | 310 | 0.894 | 77.1 |
| H08 | cl | 696 | 0.156 | -3.22 | 0.329 | -0.032 | 0.00304 | -0.203 | -60.5 | 0.437 | 0.626 | 0.761 | 513 | 0.47 | -2.65 |
| H08 | e | 696 | 0.116 | -3.75 | 0.236 | -0.0374 | 0 | -0.281 | 0 | 0.191 | 0.628 | 0.76 | 512 | 0.318 | -8.41 |
| H09 | cl | 348 | 0.227 | 10.5 | 0.874 | 0.153 | 0.018 | 0.48 | -1,812 | 0.908 | 0.897 | 0.807 | 317 | 0.814 | 21.2 |
| H09 | e | 348 | 0.19 | -2.55 | 0.33 | -0.0346 | -0.00196 | -0.279 | -456 | 0.342 | 0.825 | 0.879 | 307 | 0.251 | -30.3 |
| H10 | retr | 692 | 0.228 | -3.5 | 0.254 | -0.0273 | 0.00317 | -0.385 | -416 | 0.367 | 0.156 | 0.322 | 203 | 0.384 | -6.11 |
| H11 | zc | 536 | 0.372 | -0.441 | 0.472 | 0.00087 | 0.00777 | 0.266 | -3,293 | 0.418 | 0.295 | 0.317 | 206 | 0.471 | -2.14 |
| H14 | r | 336 | 0.9 | -13.9 | 0.301 | -0.0746 | -0.00658 | 2.03 | -46,742 | 0.402 | 0.149 | 0 | 1 | 1 | 200 |
| H19 | dr | 324 | -1.14 | 15.4 | 0.799 | 0.135 | 0.0428 | 0.718 | 730 | 0.79 | 0.38 | 0.154 | 53 | 0.774 | 119 |
| H21 | lag | 224 | 0.844 | -0.153 | 0.487 | -0.000984 | 0.00383 | 1.62 | -62,592 | 0.616 | 0.214 | 0.0536 | 27 | 0.741 | 41.6 |
| H22 | lag | 192 | 0.696 | 2.54 | 0.786 | -0.00665 | 0.00528 | 4.24 | -164,436 | 0.688 | 0 | 0 |  |  |  |
| H26 | confirm | 252 | 0.218 | -0.304 | 0.452 | 0.0124 | 0.00152 | 1.16 | -25,697 | 0.508 | 0 | 0 |  |  |  |
| H27 | ce | 472 | 0.0474 | 0.146 | 0.551 | 0.00244 | 0.00221 | 0.103 | -4,148 | 0.561 | 0.125 | 0.0932 | 143 | 0.692 | 2.63 |
| H28 | es | 168 | 0.807 | 9.64 | 0.905 | 0.0751 | 0.0177 | 3.64 | -76,700 | 0.804 | 0.0476 | 0 |  |  |  |
| H28 | trig | 168 | 0.161 | 2.41 | 0.72 | 0.0309 | 0.0101 | 0.855 | -7,443 | 0.607 | 0.0417 | 0.00595 | 1 | 1 | 15 |
| H29 | acc | 236 | 0.00783 | 0.348 | 0.682 | 0.00365 | 0.000555 | 0.0731 | -1,116 | 0.576 | 0.0424 | 0.0339 | 36 | 0.472 | -0.565 |
| H35 | qual | 220 | 0.641 | 2.57 | 0.682 | 0.0226 | 0.00662 | 0.562 | -14,376 | 0.632 | 0.391 | 0.155 | 67 | 0.239 | -37.2 |
| H37 | hist | 290 | 0.214 | -5.82 | 0.293 | -0.0435 | -0.0171 | -0.214 | -781 | 0.307 | 0.203 | 0.303 | 61 | 0.344 | -24.4 |
| H39 | cth | 156 | 0.837 | 2.08 | 0.603 | -0.00801 | 0.0257 | 2.32 | -117,970 | 0.705 | 0.0897 | 0 |  |  |  |
| H40 | dc | 172 | 0.749 | -2.35 | 0.395 | -0.0441 | -0.00971 | 0.754 | -21,887 | 0.291 | 0.0872 | 0.0698 | 13 | 0.846 | 100 |
| H41 | vr | 220 | 0.827 | 9.36 | 0.909 | 0.0812 | 0.0243 | 2.37 | -60,169 | 0.777 | 0.5 | 0.0182 | 42 | 0.762 | 40.8 |
| H42 | vr | 180 | 0.824 | 1.39 | 0.583 | -0.0227 | -0.0139 | 3.37 | -77,613 | 0.483 | 0.0389 | 0 |  |  |  |
| H43 | a | 220 | 0.619 | 6.65 | 0.918 | 0.0641 | 0.012 | 1.98 | -50,554 | 0.873 | 0.395 | 0.0182 | 41 | 0.854 | 41.1 |
| H44 | a | 180 | 0.804 | -1.57 | 0.444 | -0.0147 | 0.000783 | 3.41 | -73,662 | 0.456 | 0.0333 | 0 |  |  |  |
| H46 | strict | 180 | 0.714 | 3.54 | 0.644 | 0.0296 | 0.00516 | 1.65 | -16,724 | 0.533 | 0.111 | 0 | 3 | 1 | 47 |
| H47 | open | 300 | 0.671 | 15.6 | 0.767 | 0.182 | 0.0403 | 0.75 | -3,794 | 0.773 | 0.507 | 0.37 | 114 | 0.605 | 29.4 |
| H50 | cons | 440 | 0.726 | -14.7 | 0.107 | -0.176 | -0.0323 | -0.576 | -2,132 | 0.1 | 0.118 | 0.718 | 89 | 0.742 | 65.1 |
| H50 | trig | 314 | 0.54 | -11 | 0.115 | -0.127 | -0.0213 | -0.928 | 1,156 | 0.169 | 0.42 | 0.439 | 107 | 0.514 | 1.97 |
| X3 | reg | 316 | 0.797 | 1.9 | 0.554 | 0.0242 | -0.00494 | 0.199 | -14,506 | 0.478 | 0.57 | 0.43 | 177 | 0.407 | -26.2 |

Reading: `trades_removed` median share of the parent's trades removed; `d_avg` median change in avg net trade ($); `sub2` share of pairs improving in >= 2 of 3 discovery sub-periods; `child_pos`/`parent_pos` share of profitable specs with / without the condition.

## F. Management / RR results

Discovery, Stage-B variant vs its Stage-A control (same entry, same 1-ATR stop):

| variant_class | pairs | share_better_net | median_d_avg_trade |
|---|---|---|---|
| BE | 4,501 | 0.17 | -4.91 |
| COMBO | 774 | 0.103 | -12 |
| PARTIAL/RUNNER | 4,013 | 0.107 | -5.06 |
| TRAIL | 3,096 | 0.226 | -6.15 |

Confirmation (2019-2022), same comparison where both specs were frozen:

| cls | pairs | share_better | median_d_avg |
|---|---|---|---|
| BE | 1723 | 0.305 | -12.6 |
| COMBO | 337 | 0.131 | -42.5 |
| PARTIAL/RUNNER | 1826 | 0.168 | -16.6 |
| TRAIL | 2284 | 0.276 | -19.6 |

Per variant: `results/discovery/management_summary.csv`, `results/tables/management_confirmation.csv`.

Payoff shape (PRIMARY specs; discovery label -> share positive in confirmation):

| mode | payoff_shape | primary_specs | conf_positive | conf_stress_positive | conf_median_t |
|---|---|---|---|---|---|
| continuation | ASYMMETRIC | 340 | 0.803 | 0.724 | 0.863 |
| continuation | BALANCED | 135 | 0.711 | 0.681 | 0.604 |
| continuation | HIGH_RR | 686 | 0.88 | 0.838 | 1.07 |
| continuation | MANAGED | 1017 | 0.819 | 0.749 | 0.798 |
| continuation | TIME_EXIT | 37 | 0.784 | 0.784 | 0.671 |
| reversal | ASYMMETRIC | 17 | 0.471 | 0.294 | -0.092 |
| reversal | BALANCED | 20 | 0.25 | 0.25 | -0.286 |
| reversal | HIGH_RR | 31 | 0.645 | 0.581 | 0.436 |
| reversal | HIGH_WR | 8 | 0.5 | 0.375 | 0.0341 |
| reversal | MANAGED | 91 | 0.341 | 0.264 | -0.322 |
| reversal | NATURAL | 12 | 0.25 | 0.167 | -0.873 |
| reversal | TIME_EXIT | 9 | 0.222 | 0.222 | -0.966 |

Per family: `results/tables/payoff_shape_by_family.csv`; discovery shapes `results/discovery/payoff_shapes.csv`.

## G. Discovery freeze

- `freezes/DISCOVERY_FREEZE.json` sha256 `0343a974953d53dc026fd1f7ef5c124c8985213b132fba5df4f8a986fc85b2c9` (13,244 candidates: {'PRIMARY': 2403, 'WEAK_POSITIVE': 6209, 'LOW_SAMPLE': 40, 'MODERATE_ONLY': 4592}); labels file sha256 `f6b33ebc7b8de06a9491e0708f35710629c2279ca531ca13eb9df9607eef6ed1`; frozen 2026-09-22T23:03:38.474989+00:00 (UTC).
- Confirmation / null / clustering / evidence / selection / holdout procedures frozen in `preregistration/V3_CONFIRMATION_PREREGISTRATION.md` (sha256 `3ac5ab19454bdfdecce70ec0dc5b6fddf39bb8a0bdfee8ded8d7b1402082a900`) BEFORE the confirmation partition was opened; the whole chain had been dry-run on discovery data first (code test only).
- Behaviour-affecting code hash identical from the discovery preregistration to the end (`a05d4436e1e81e4e...`).

## H. Confirmation results (2019-2022)

- All 13,244 frozen candidates were run unchanged. PRIMARY evidence tiers: **STRONG 47, PROMISING 852, INCONCLUSIVE 1013, WEAK 416, REJECTED 75** (definitions below).
- Tier definitions (preregistered): **STRONG** = n>=50, BASELINE net>0, t>=2.0, STRESS net>0, >=3 of 4 confirmation years positive, management support>=0.5, parameter support>=0.5 (or no grid neighbours), null p<=0.05; **PROMISING** = not STRONG; n>=30, BASELINE net>0, t>=1.0, >=2 of 4 years positive, management support>=0.25 or parameter support>=0.25, null p<=0.20; **REJECTED** = n>=30, BASELINE net<=0 and the confirmation mean net trade is significantly below the discovery mean: (mean_conf - mean_disc)/(sd_conf/sqrt(n)) <= -1.645 (rejected with adequate evidence); **WEAK** = n>=30, BASELINE net<=0, but not significantly below the discovery estimate (unsupported, underpowered to reject); **INCONCLUSIVE** = everything else: n<30 (UNDERPOWERED) or positive but below PROMISING
- Diagnostic groups (never eligible) in confirmation: see `results/tables/confirmation_diagnostic_groups.csv`.
- 2019-2022 was an unusually trending, high-volatility period: 79% of PRIMARY specs were positive, but so were ~40% on average in the no-edge worlds (Section I) -- the null comparison, not the raw share, is the evidence.

| hypothesis | INCONCLUSIVE | PROMISING | REJECTED | STRONG | WEAK |
|---|---|---|---|---|---|
| H01 | 64 | 180 | 0 | 15 | 2 |
| H02 | 1 | 9 | 0 | 0 | 0 |
| H03 | 17 | 6 | 0 | 0 | 0 |
| H04 | 59 | 12 | 0 | 0 | 32 |
| H05 | 14 | 27 | 1 | 3 | 5 |
| H06 | 3 | 33 | 0 | 2 | 0 |
| H07 | 32 | 107 | 5 | 0 | 18 |
| H08 | 194 | 142 | 1 | 0 | 31 |
| H09 | 221 | 69 | 0 | 1 | 45 |
| H10 | 17 | 13 | 0 | 0 | 2 |
| H11 | 12 | 0 | 0 | 0 | 26 |
| H12 | 3 | 0 | 0 | 0 | 1 |
| H13 | 0 | 0 | 0 | 0 | 2 |
| H14 | 9 | 0 | 3 | 0 | 19 |
| H16 | 9 | 0 | 0 | 0 | 7 |
| H18 | 1 | 0 | 0 | 0 | 1 |
| H19 | 9 | 0 | 2 | 0 | 51 |
| H20 | 12 | 50 | 0 | 17 | 1 |
| H21 | 9 | 0 | 2 | 0 | 6 |
| H23 | 0 | 0 | 0 | 0 | 1 |
| H25 | 18 | 19 | 1 | 0 | 2 |
| H27 | 4 | 2 | 0 | 0 | 0 |
| H30 | 3 | 2 | 0 | 0 | 0 |
| H31 | 7 | 0 | 0 | 0 | 3 |
| H32 | 1 | 0 | 0 | 0 | 0 |
| H33 | 1 | 2 | 0 | 0 | 0 |
| H35 | 6 | 0 | 5 | 0 | 1 |
| H36 | 13 | 0 | 0 | 0 | 0 |
| H37 | 3 | 0 | 0 | 0 | 0 |
| H38 | 9 | 0 | 0 | 0 | 10 |
| H39 | 1 | 0 | 0 | 0 | 0 |
| H40 | 2 | 0 | 0 | 0 | 0 |
| H41 | 54 | 38 | 1 | 0 | 26 |
| H42 | 4 | 0 | 14 | 0 | 3 |
| H43 | 6 | 17 | 0 | 0 | 0 |
| H45 | 35 | 39 | 1 | 1 | 19 |
| H46 | 2 | 0 | 0 | 0 | 2 |
| H47 | 46 | 53 | 3 | 8 | 12 |
| H48 | 7 | 13 | 0 | 0 | 0 |
| H49 | 22 | 1 | 0 | 0 | 17 |
| H50 | 59 | 3 | 0 | 0 | 27 |
| X3 | 24 | 15 | 36 | 0 | 44 |

## I. Null results (100 worlds: 50 zero-drift + 50 drift-preserving)

Null worlds: per-minute random sign flips shared by NQ and ES, applied to each bar's gap, body and high/low excursions (absolute moves, volatility clustering, intraday seasonality, fat tails, gaps, session/roll/calendar structure and the same-minute NQ-ES relation preserved; directional predictability and lead-lag destroyed). The SAME PRIMARY candidates and the SAME evidence procedure (without the null p-value) ran in every world. Empirical p = (1 + #null >= real)/(1 + worlds); resolution 1/51 per style, 1/101 pooled.

| statistic | real | zero_mean | zero_p95 | zero_p | drift_mean | drift_p95 | drift_p | pooled_p |
|---|---|---|---|---|---|---|---|---|
| prenull_strong | 52 | 7.4 | 27.1 | 0.0588 | 2.5 | 10.5 | 0.0196 | 0.0297 |
| prenull_promising | 849 | 222 | 532 | 0.0392 | 177 | 408 | 0.0196 | 0.0198 |
| positive | 1908 | 959 | 1,646 | 0.0392 | 926 | 1,403 | 0.0196 | 0.0198 |
| stress_positive | 1763 | 809 | 1,495 | 0.0588 | 803 | 1,296 | 0.0196 | 0.0297 |
| behaviours | 43 | 17.9 | 32 | 0.0196 | 16.9 | 25.5 | 0.0196 | 0.0099 |
| strong_behaviours | 7 | 1.18 | 4 | 0.0196 | 0.84 | 3 | 0.0196 | 0.0099 |
| eligible_behaviours | 32 | 10.7 | 22.5 | 0.0196 | 9.2 | 14 | 0.0196 | 0.0099 |
| selected | 25 | 8.88 | 17.5 | 0.0196 | 8 | 12.6 | 0.0196 | 0.0099 |
| survivors_[30,100) | 49 | 39.4 | 94.6 | 0.333 | 38.5 | 83.2 | 0.373 | 0.347 |
| survivors_[100,300) | 324 | 96.5 | 224 | 0.0392 | 80.1 | 190 | 0.0196 | 0.0198 |
| survivors_[300,1000) | 297 | 58.5 | 190 | 0.0392 | 39.6 | 118 | 0.0196 | 0.0198 |
| survivors_[1000,inf) | 231 | 34.8 | 167 | 0.0588 | 21.5 | 88.5 | 0.0196 | 0.0297 |

Candidate level: p_null = max(p_zero, p_drift) of the t-statistic (in `confirmation_primary_evidence.csv`); `p_familywise_bucket` = share of worlds in which the MAXIMUM PRIMARY t in the same trade-frequency bucket reached the candidate's t (a search-wide correction; descriptive).

## J. Behaviour clustering

- STRONG + PROMISING PRIMARY candidates: **899** (entry rules: 191); behaviours at rho 0.30 / **0.50** / 0.70 / 0.90: 17 / **43** / 127 / 464; singletons at 0.50: 9; eligible behaviours 31.
- Null distribution of the same cluster statistics: Section I (behaviours, strong_behaviours, eligible_behaviours).

| cluster_0.50 | members | entry_rules | hypotheses | directions | managements | strong | tier | eligible | selected | representative |
|---|---|---|---|---|---|---|---|---|---|---|
| 43 | 191 | 41 | H01,H02,H03,H04,H10,H20,H27,H30,X3 | both | 13 | 19 | STRONG | True | True | Cdf2b568ee1f8a182 |
| 24 | 87 | 17 | H01,H03,H20 | long | 14 | 13 | STRONG | True | False | Cf74e9b9ab0b061bb |
| 23 | 70 | 8 | H09 | both,short | 20 | 1 | STRONG | True | True | Ce5e284855c7e4be1 |
| 19 | 65 | 11 | H07,H45 | both,short | 12 | 0 | PROMISING | True | True | C915ea812fd5945a5 |
| 34 | 64 | 10 | H08,H45 | both,short | 16 | 1 | STRONG | True | True | Ca55086023a82dafa |
| 27 | 51 | 6 | H08 | both,long | 10 | 0 | PROMISING | True | True | Cf048ad80a1bd7603 |
| 42 | 46 | 19 | H01,H04,H20,H33,H41 | short | 6 | 0 | PROMISING | True | False | C215a01148c22a560 |
| 18 | 35 | 6 | H07 | both,long | 10 | 0 | PROMISING | True | True | C5fbf4cc530f79d84 |
| 35 | 25 | 8 | H08,H45 | long | 11 | 0 | PROMISING | True | True | C046be57651136b5c |
| 11 | 24 | 3 | H47 | both,long | 11 | 8 | STRONG | True | True | Cfa444b4386db8d33 |
| 25 | 22 | 3 | H05 | long | 8 | 3 | STRONG | True | True | C1a82f05b6fe1e264 |
| 8 | 20 | 2 | H47 | long | 10 | 0 | PROMISING | True | True | C82ee16a85ecc3f4d |
| 2 | 19 | 2 | H06 | long | 11 | 0 | PROMISING | True | True | C39c52e02a3c54412 |
| 32 | 19 | 8 | H08,H45 | both,short | 3 | 0 | PROMISING | True | True | Ceef182c53f2e1673 |
| 41 | 17 | 4 | H43 | both | 6 | 0 | PROMISING | True | True | C16cd8e3c605af462 |
| 33 | 13 | 5 | H07 | both,long | 5 | 0 | PROMISING | True | False | C8130346574ced5f4 |
| 40 | 13 | 2 | H41 | both | 7 | 0 | PROMISING | True | True | C91756637ca7282e7 |
| 3 | 13 | 1 | H06 | both | 10 | 2 | STRONG | True | True | C2839e22b29c0cb17 |
| 16 | 12 | 3 | H48 | both,short | 6 | 0 | PROMISING | True | True | C936c5aa985ba50fd |
| 15 | 11 | 3 | H25 | both,short | 6 | 0 | PROMISING | True | True | C431e7e54dbc7b968 |
| 26 | 8 | 2 | H05 | both | 5 | 0 | PROMISING | True | True | Cd165e089c8a180ec |
| 31 | 7 | 3 | H08,H45 | short | 5 | 0 | PROMISING | True | False | Cf4c117851104d7ab |
| 38 | 7 | 2 | H41 | both | 4 | 0 | PROMISING | True | False | C84012de7cf222d8a |
| 14 | 7 | 2 | H25 | both,short | 5 | 0 | PROMISING | True | True | C2845a074bb5a5501 |
| 39 | 7 | 2 | H41 | both | 5 | 0 | PROMISING | True | False | Cf59641d59e4ca79f |
| 10 | 6 | 2 | H47 | long | 4 | 0 | PROMISING | True | True | C62eeef3eabed9056 |
| 30 | 6 | 1 | H45 | both | 5 | 0 | PROMISING | False | False | Ce13c6ec6dd1f4df6 |
| 36 | 5 | 3 | H41 | short | 2 | 0 | PROMISING | True | True | Ce2bc1c0f03390096 |
| 7 | 5 | 2 | H47 | both | 3 | 0 | PROMISING | True | True | Cfcc0e08cf3dce32c |
| 13 | 4 | 2 | X3 | both | 2 | 0 | PROMISING | True | True | C77d755b168515944 |
| 22 | 3 | 3 | H50 | both,short | 2 | 0 | PROMISING | True | True | C87a31838e567ad3c |
| 1 | 3 | 1 | H06 | both | 1 | 0 | PROMISING | False | False | Cd9f4692ff24d569b |
| 4 | 3 | 1 | H47 | both | 3 | 0 | PROMISING | False | False | C9b58a261865d5423 |
| 20 | 2 | 2 | H07 | short | 1 | 0 | PROMISING | True | True | C18117db2aa81a2bf |
| 5 | 1 | 1 | H47 | both | 1 | 0 | PROMISING | False | False | Cd1686a46158a1f41 |
| 9 | 1 | 1 | H47 | long | 1 | 0 | PROMISING | False | False | C1c67e88d2d86f5b0 |
| 6 | 1 | 1 | H47 | short | 1 | 0 | PROMISING | False | False | C3e9de33e0a21e437 |
| 12 | 1 | 1 | H25 | long | 1 | 0 | PROMISING | False | False | C10d4d578b15b6d14 |
| 17 | 1 | 1 | H48 | short | 1 | 0 | PROMISING | False | False | Ca827664d8dbd7883 |
| 21 | 1 | 1 | H07 | short | 1 | 0 | PROMISING | False | False | Cb781552274e28e57 |
| 28 | 1 | 1 | H08 | long | 1 | 0 | PROMISING | False | False | C2b4f15ac8e51a68f |
| 29 | 1 | 1 | H49 | both | 1 | 0 | PROMISING | False | False | C29161a4910e0e471 |
| 37 | 1 | 1 | H41 | both | 1 | 0 | PROMISING | False | False | Cbf634e3535837cd3 |

## K. Final-selection method (preregistered)

- **eligible_behaviour**: >= 1 STRONG member, or >= 2 PROMISING-or-better members with DISTINCT entry rules
- **representative**: pool = STRONG members if any else all members; keep the fewest confluence conditions; medoid = highest mean daily-P&L correlation to all cluster members; ties -> lowest id
- **order**: STRONG behaviours first, then breadth (distinct entry rules) desc, size desc, representative id
- **correlation_rule**: accept a representative only if its confirmation daily-P&L correlation with every already accepted representative is < 0.50
- **size**: no forced size; an empty cohort is a valid result (then there is no holdout test)
- **never_by**: highest PF / WR / P&L / Sharpe / best 2022 / best-looking equity curve

Result: 31 eligible behaviours -> **25 selected**; the others were excluded only by the < 0.50 correlation rule (see `results/confirmation/behaviours.csv`).

## L. Final frozen cohort

`freezes/FINAL_COHORT_FREEZE.json` sha256 **`f5666dac728aa2539b2f8223309012914d71923ab71f3363e9e035344ace8f03`**, frozen 2026-09-22T23:21:51.429326+00:00 (UTC), before any 2023+ bar was opened. Each member's spec is a byte-identical copy of its discovery-freeze spec (verified before every data read). Machine-readable: `results/tables/final_cohort.csv`.

### 1. `Cdf2b568ee1f8a182` — H20 Extreme-move path test (both, continuation)

- **Behaviour cluster** 43 (STRONG; 191 members, 41 entry rules) — confirmation tier **STRONG**
- **Entry**: BUY when the 30-minute move first exceeds +2.0 sigma units with path efficiency x sqrt(n) >= 2.4. SELL SHORT when the 30-minute move first falls below -2.0 sigma units with path efficiency x sqrt(n) >= 2.4. Market order at the next one-minute bar's open.
- **Context / confluences**: none; parameters `{"cls": "high", "mode": "continuation", "n": 30, "pe_hi": 2.4, "pe_lo": 1.7, "z": 2.0}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1.5 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 100% no target (payoff shape HIGH_RR). **BE**: none. **Partials**: none. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 1045 trades, PF 1.26, WR 40.4%, net $149,075, avg $143, max DD $25,869, t 2.56, STRESS $136,535, null p 0.039, parameter support 1.00, management support 0.62 (discovery: 2096 trades, PF 1.17, t 2.24, parameter robustness 1.00)
- **Holdout 2023-25**: 795 trades, PF 1.21, WR 38.5%, net $120,595, avg $152, max DD $42,886, longest losing streak 13; 2023 $23,719 / 2024 $48,978 / 2025 $47,898; STRESS net $111,055 (PF 1.19); **SUPPORTED** (t 1.73, z vs confirmation 0.10, null p 0.059)
- **2026 audit**: 167 trades, net $-52,593, PF 0.77, STRESS $-54,597; FAILED

### 2. `Ca55086023a82dafa` — H45 Early trend-day classification (both, continuation)

- **Behaviour cluster** 34 (STRONG; 64 members, 10 entry rules) — confirmation tier **STRONG**
- **Entry**: BUY when at 10:30 at least 4 of the 5 trend-day criteria hold and the close is above the RTH open. SELL SHORT when at 10:30 at least 4 of the 5 trend-day criteria hold and the close is below the RTH open. Market order at the next one-minute bar's open.
- **Context / confluences**: none; parameters `{"cut": "10:30", "k": 4, "mode": "continuation"}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1.5 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 100% at +2R (payoff shape ASYMMETRIC). **BE**: none. **Partials**: none. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 327 trades, PF 1.35, WR 45.3%, net $62,622, avg $192, max DD $21,314, t 2.25, STRESS $58,698, null p 0.039, parameter support 0.50, management support 0.54 (discovery: 659 trades, PF 1.15, t 1.40, parameter robustness 1.00)
- **Holdout 2023-25**: 233 trades, PF 1.23, WR 40.8%, net $39,098, avg $168, max DD $13,505, longest losing streak 9; 2023 $2,064 / 2024 $20,917 / 2025 $16,117; STRESS net $36,302 (PF 1.22); **SUPPORTED** (t 1.38, z vs confirmation -0.20, null p 0.109)
- **2026 audit**: 60 trades, net $-8,290, PF 0.90, STRESS $-9,010; INCONCLUSIVE

### 3. `Ce5e284855c7e4be1` — H09 Last-hour trend continuation (short, continuation)

- **Behaviour cluster** 23 (STRONG; 70 members, 8 entry rules) — confirmation tier **STRONG**
- **Entry**: SELL SHORT when at 15:00 the close is >= 0.4 x D below the RTH open. Market order at the next one-minute bar's open.
- **Context / confluences**: none; parameters `{"cl": null, "cut": "15:00", "e": null, "m": 0.4, "mode": "continuation"}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 tick beyond the last confirmed 5-minute swing, kept between 0.5 and 3.0 ATRh from the signal close. **Target**: 100% at +1R (payoff shape BALANCED). **BE**: none. **Partials**: none. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 225 trades, PF 1.49, WR 53.3%, net $30,300, avg $135, max DD $7,731, t 2.11, STRESS $27,600, null p 0.039, parameter support 1.00, management support 0.77 (discovery: 465 trades, PF 1.19, t 1.16, parameter robustness 1.00)
- **Holdout 2023-25**: 177 trades, PF 1.39, WR 55.9%, net $24,057, avg $136, max DD $8,872, longest losing streak 5; 2023 $13,425 / 2024 $3,574 / 2025 $7,058; STRESS net $21,933 (PF 1.35); **SUPPORTED** (t 1.62, z vs confirmation 0.01, null p 0.040)
- **2026 audit**: 39 trades, net $8,294, PF 1.37, STRESS $7,826; WEAKER_THAN_EXPECTED

### 4. `Cfa444b4386db8d33` — H47 Large overnight move + same-direction open (long, continuation)

- **Behaviour cluster** 11 (STRONG; 24 members, 3 entry rules) — confirmation tier **STRONG**
- **Entry**: BUY when at 09:30+15min, the RTH open gapped >= 0.25D above the previous RTH close and the close is >= 0.05D above the RTH open. Market order at the next one-minute bar's open.
- **Context / confluences**: {"open": "same"}; parameters `{"g": 0.25, "mode": "continuation", "open": "same", "w": 15}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 25% at +1R, 75% no target (payoff shape MANAGED). **BE**: none. **Partials**: 25%@+1R / 75%@runner. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 137 trades, PF 1.77, WR 28.5%, net $24,860, avg $181, max DD $5,027, t 2.20, STRESS $23,216, null p 0.020, parameter support 0.50, management support 0.54 (discovery: 228 trades, PF 1.49, t 2.08, parameter robustness 1.00)
- **Holdout 2023-25**: 99 trades, PF 1.90, WR 27.3%, net $29,058, avg $294, max DD $4,621, longest losing streak 8; 2023 $3,970 / 2024 $18,668 / 2025 $6,420; STRESS net $27,870 (PF 1.84); **SUPPORTED** (t 2.18, z vs confirmation 0.83, null p 0.020)
- **2026 audit**: 20 trades, net $16,650, PF 2.35, STRESS $16,410; SUPPORTED

### 5. `C1a82f05b6fe1e264` — H05 Volatility-shock momentum (long, continuation)

- **Behaviour cluster** 25 (STRONG; 22 members, 3 entry rules) — confirmation tier **STRONG**
- **Entry**: BUY when the 30-minute move first exceeds +1.0 sigma units while 15-minute realised vol >= 3.0x its same-time-of-day norm. Market order at the next one-minute bar's open.
- **Context / confluences**: {"v": 3.0}; parameters `{"mode": "continuation", "n": 30, "v": 3.0, "z": 1.0}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 100% no target (payoff shape MANAGED). **BE**: none. **Partials**: none. **Trail**: atr_high 1.5. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 128 trades, PF 2.19, WR 40.6%, net $50,223, avg $392, max DD $8,136, t 2.47, STRESS $48,687, null p 0.020, parameter support 0.50, management support 0.62 (discovery: 147 trades, PF 1.36, t 1.17, parameter robustness 1.00)
- **Holdout 2023-25**: 72 trades, PF 1.02, WR 40.3%, net $1,497, avg $21, max DD $28,895, longest losing streak 6; 2023 $4,828 / 2024 $5,820 / 2025 $-9,151; STRESS net $633 (PF 1.01); **WEAKER_THAN_EXPECTED** (t 0.07, z vs confirmation -1.27, null p 0.446)
- **2026 audit**: 22 trades, net $4,252, PF 1.17, STRESS $3,988; WEAKER_THAN_EXPECTED

### 6. `C2839e22b29c0cb17` — H06 Compression to expansion (both, continuation)

- **Behaviour cluster** 3 (STRONG; 13 members, 1 entry rules) — confirmation tier **STRONG**
- **Entry**: BUY when the close breaks above the previous 60-bar high; the previous 60 bars' realised vol was <= 0.6x its time-of-day norm; the 5-minute move >= 1.0 sigma units. SELL SHORT when the close breaks below the previous 60-bar low; the previous 60 bars' realised vol was <= 0.6x its time-of-day norm; the 5-minute move >= 1.0 sigma units. Market order at the next one-minute bar's open.
- **Context / confluences**: {"cth": 0.6, "strong": 1.0}; parameters `{"N": 60, "cth": 0.6, "mode": "continuation", "strong": 1.0}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 100% no target (payoff shape HIGH_RR). **BE**: none. **Partials**: none. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 531 trades, PF 1.43, WR 33.5%, net $61,006, avg $115, max DD $9,376, t 2.58, STRESS $54,634, null p 0.020, parameter support 0.50, management support 0.77 (discovery: 742 trades, PF 1.17, t 1.36, parameter robustness 1.00)
- **Holdout 2023-25**: 331 trades, PF 0.97, WR 29.0%, net $-4,424, avg $-13, max DD $35,340, longest losing streak 12; 2023 $5,245 / 2024 $4,880 / 2025 $-14,549; STRESS net $-8,396 (PF 0.94); **FAILED** (t -0.19, z vs confirmation -1.78, null p 0.446)
- **2026 audit**: 53 trades, net $26,378, PF 2.11, STRESS $25,742; SUPPORTED

### 7. `C915ea812fd5945a5` — H07 Opening-drive continuation (both, continuation)

- **Behaviour cluster** 19 (PROMISING; 65 members, 11 entry rules) — confirmation tier **PROMISING**
- **Entry**: BUY when at 09:30+30min the close is >= 0.3 x D above the RTH open. SELL SHORT when at 09:30+30min the close is >= 0.3 x D below the RTH open. Market order at the next one-minute bar's open.
- **Context / confluences**: none; parameters `{"e": null, "m": 0.3, "mode": "continuation", "w": 30}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 100% no target (payoff shape MANAGED). **BE**: none. **Partials**: none. **Trail**: atr_high 3. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 304 trades, PF 1.43, WR 32.2%, net $53,864, avg $177, max DD $10,833, t 2.02, STRESS $50,216, null p 0.059, parameter support 0.50, management support 0.46 (discovery: 605 trades, PF 1.26, t 1.68, parameter robustness 1.00)
- **Holdout 2023-25**: 225 trades, PF 1.15, WR 24.0%, net $17,630, avg $78, max DD $11,404, longest losing streak 14; 2023 $125 / 2024 $15,747 / 2025 $1,758; STRESS net $14,930 (PF 1.12); **WEAKER_THAN_EXPECTED** (t 0.67, z vs confirmation -0.85, null p 0.228)
- **2026 audit**: 56 trades, net $-17,074, PF 0.69, STRESS $-17,746; FAILED

### 8. `C046be57651136b5c` — H08 Morning trend continuation (long, continuation)

- **Behaviour cluster** 35 (PROMISING; 25 members, 8 entry rules) — confirmation tier **PROMISING**
- **Entry**: BUY when at 10:30 the close is >= 0.5 x D above the RTH open. Market order at the next one-minute bar's open.
- **Context / confluences**: none; parameters `{"cl": null, "cut": "10:30", "e": null, "m": 0.5, "mode": "continuation"}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 25% at +1R, 75% no target (payoff shape MANAGED). **BE**: none. **Partials**: 25%@+1R / 75%@runner. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 84 trades, PF 1.55, WR 41.7%, net $14,970, avg $178, max DD $6,696, t 1.21, STRESS $13,962, null p 0.118, parameter support 1.00, management support 0.38 (discovery: 177 trades, PF 1.60, t 1.91, parameter robustness 1.00)
- **Holdout 2023-25**: 66 trades, PF 1.25, WR 34.8%, net $8,298, avg $126, max DD $7,610, longest losing streak 9; 2023 $3,690 / 2024 $-1,077 / 2025 $5,686; STRESS net $7,506 (PF 1.22); **WEAKER_THAN_EXPECTED** (t 0.75, z vs confirmation -0.31, null p 0.238)
- **2026 audit**: 19 trades, net $-3,657, PF 0.81, STRESS $-3,885; INCONCLUSIVE

### 9. `Ceef182c53f2e1673` — H08 Morning trend continuation (short, continuation)

- **Behaviour cluster** 32 (PROMISING; 19 members, 8 entry rules) — confirmation tier **PROMISING**
- **Entry**: SELL SHORT when at 10:30 the close is >= 0.5 x D below the RTH open. Market order at the next one-minute bar's open.
- **Context / confluences**: none; parameters `{"cl": null, "cut": "10:30", "e": null, "m": 0.5, "mode": "continuation"}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 tick beyond the last confirmed 5-minute swing, kept between 0.5 and 3.0 ATRh from the signal close. **Target**: 100% no target (payoff shape HIGH_RR). **BE**: none. **Partials**: none. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 86 trades, PF 1.73, WR 51.2%, net $39,216, avg $456, max DD $10,079, t 1.89, STRESS $38,184, null p 0.059, parameter support 1.00, management support 0.23 (discovery: 208 trades, PF 1.26, t 1.17, parameter robustness 1.00)
- **Holdout 2023-25**: 75 trades, PF 1.51, WR 52.0%, net $36,085, avg $481, max DD $17,982, longest losing streak 5; 2023 $8,158 / 2024 $-5,639 / 2025 $33,566; STRESS net $35,185 (PF 1.49); **SUPPORTED** (t 1.38, z vs confirmation 0.07, null p 0.079)
- **2026 audit**: 20 trades, net $-11,980, PF 0.74, STRESS $-12,220; INCONCLUSIVE

### 10. `Cf048ad80a1bd7603` — H08 Morning trend continuation (long, continuation)

- **Behaviour cluster** 27 (PROMISING; 51 members, 6 entry rules) — confirmation tier **PROMISING**
- **Entry**: BUY when at 11:00 the close is >= 0.3 x D above the RTH open. Market order at the next one-minute bar's open.
- **Context / confluences**: none; parameters `{"cl": null, "cut": "11:00", "e": null, "m": 0.3, "mode": "continuation"}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 25% at +1R, 75% no target (payoff shape MANAGED). **BE**: none. **Partials**: 25%@+1R / 75%@runner. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 242 trades, PF 1.24, WR 37.6%, net $22,091, avg $91, max DD $10,698, t 1.13, STRESS $19,187, null p 0.078, parameter support 1.00, management support 0.77 (discovery: 509 trades, PF 1.36, t 2.29, parameter robustness 1.00)
- **Holdout 2023-25**: 186 trades, PF 1.05, WR 35.5%, net $4,948, avg $27, max DD $17,734, longest losing streak 11; 2023 $11,346 / 2024 $5,138 / 2025 $-11,535; STRESS net $2,716 (PF 1.03); **WEAKER_THAN_EXPECTED** (t 0.27, z vs confirmation -0.66, null p 0.525)
- **2026 audit**: 48 trades, net $12,827, PF 1.38, STRESS $12,251; WEAKER_THAN_EXPECTED

### 11. `C5fbf4cc530f79d84` — H07 Opening-drive continuation (long, continuation)

- **Behaviour cluster** 18 (PROMISING; 35 members, 6 entry rules) — confirmation tier **PROMISING**
- **Entry**: BUY when at 09:30+30min the close is >= 0.3 x D above the RTH open with path efficiency since the open >= 0.4. Market order at the next one-minute bar's open.
- **Context / confluences**: {"e": 0.4}; parameters `{"e": 0.4, "m": 0.3, "mode": "continuation", "w": 30}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 100% no target (payoff shape MANAGED). **BE**: none. **Partials**: none. **Trail**: atr_high 2. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 70 trades, PF 1.89, WR 44.3%, net $16,305, avg $233, max DD $4,265, t 2.05, STRESS $15,465, null p 0.020, parameter support 1.00, management support 0.08 (discovery: 93 trades, PF 1.50, t 1.18, parameter robustness 1.00)
- **Holdout 2023-25**: 41 trades, PF 1.60, WR 36.6%, net $8,306, avg $203, max DD $4,217, longest losing streak 8; 2023 $4,888 / 2024 $6,804 / 2025 $-3,386; STRESS net $7,814 (PF 1.55); **SUPPORTED** (t 1.03, z vs confirmation -0.15, null p 0.109)
- **2026 audit**: 11 trades, net $9,886, PF 2.22, STRESS $9,754; WEAKER_THAN_EXPECTED

### 12. `C16cd8e3c605af462` — H43 Positive autocorrelation regime + momentum (both, continuation)

- **Behaviour cluster** 41 (PROMISING; 17 members, 4 entry rules) — confirmation tier **PROMISING**
- **Entry**: BUY when the 15-minute move first exceeds +1.0 sigma units with the 5-minute return autocorrelation (last 24) >= 0.25. SELL SHORT when the 15-minute move first falls below -1.0 sigma units with the 5-minute return autocorrelation (last 24) >= 0.25. Market order at the next one-minute bar's open.
- **Context / confluences**: {"a": 0.25}; parameters `{"a": 0.25, "mode": "continuation", "z": 1.0}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 100% no target (payoff shape HIGH_RR). **BE**: none. **Partials**: none. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 970 trades, PF 1.39, WR 30.5%, net $156,625, avg $161, max DD $28,955, t 3.27, STRESS $144,985, null p 0.020, parameter support 0.50, management support 0.46 (discovery: 2123 trades, PF 1.16, t 1.88, parameter robustness 1.00)
- **Holdout 2023-25**: 836 trades, PF 1.14, WR 27.6%, net $64,961, avg $78, max DD $31,523, longest losing streak 19; 2023 $20,229 / 2024 $5,598 / 2025 $39,134; STRESS net $54,929 (PF 1.11); **SUPPORTED** (t 1.15, z vs confirmation -1.24, null p 0.079)
- **2026 audit**: 165 trades, net $-2,630, PF 0.98, STRESS $-4,610; INCONCLUSIVE

### 13. `C936c5aa985ba50fd` — H48 Large overnight move + opening rejection (short, reversal)

- **Behaviour cluster** 16 (PROMISING; 12 members, 3 entry rules) — confirmation tier **PROMISING**
- **Entry**: SELL SHORT when the RTH open gapped >= 0.25D up and at 09:30+30min the close is >= 0.1D below the RTH open. Market order at the next one-minute bar's open.
- **Context / confluences**: none; parameters `{"g": 0.25, "mode": "reversal", "o": 0.1, "w": 30}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 25% at +1R, 75% no target (payoff shape MANAGED). **BE**: none. **Partials**: 25%@+1R / 75%@runner. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 107 trades, PF 1.68, WR 29.0%, net $22,253, avg $208, max DD $5,760, t 1.56, STRESS $20,969, null p 0.078, parameter support 0.33, management support 0.27 (discovery: 243 trades, PF 1.70, t 2.03, parameter robustness 0.67)
- **Holdout 2023-25**: 85 trades, PF 1.06, WR 18.8%, net $2,228, avg $26, max DD $11,070, longest losing streak 11; 2023 $-1,971 / 2024 $7,022 / 2025 $-2,824; STRESS net $1,208 (PF 1.03); **WEAKER_THAN_EXPECTED** (t 0.16, z vs confirmation -1.13, null p 0.416)
- **2026 audit**: 22 trades, net $-863, PF 0.95, STRESS $-1,127; INCONCLUSIVE

### 14. `C431e7e54dbc7b968` — H25 Correlation breakdown (both, continuation)

- **Behaviour cluster** 15 (PROMISING; 11 members, 3 entry rules) — confirmation tier **PROMISING**
- **Entry**: BUY when 30-minute NQ/ES correlation <= 0.5 and NQ's 30-minute beta residual >= +2.0 sigma. SELL SHORT when 30-minute NQ/ES correlation <= 0.5 and NQ's 30-minute beta residual <= -2.0 sigma. Market order at the next one-minute bar's open.
- **Context / confluences**: none; parameters `{"cth": 0.5, "mode": "continuation", "rz": 2.0}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 100% no target (payoff shape HIGH_RR). **BE**: none. **Partials**: none. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 234 trades, PF 1.34, WR 17.9%, net $20,014, avg $86, max DD $8,713, t 1.26, STRESS $17,206, null p 0.059, parameter support 0.50, management support 0.31 (discovery: 343 trades, PF 1.63, t 2.16, parameter robustness 1.00)
- **Holdout 2023-25**: 115 trades, PF 1.17, WR 16.5%, net $6,095, avg $53, max DD $7,555, longest losing streak 14; 2023 $-1,200 / 2024 $3,241 / 2025 $4,054; STRESS net $4,715 (PF 1.13); **WEAKER_THAN_EXPECTED** (t 0.48, z vs confirmation -0.30, null p 0.337)
- **2026 audit**: 24 trades, net $6,664, PF 1.50, STRESS $6,376; WEAKER_THAN_EXPECTED

### 15. `Ce2bc1c0f03390096` — H41 Variance-ratio trending regime + momentum (short, continuation)

- **Behaviour cluster** 36 (PROMISING; 5 members, 3 entry rules) — confirmation tier **PROMISING**
- **Entry**: SELL SHORT when the 15-minute move first falls below -1.0 sigma units with variance ratio VR(5) over the last 120 minutes >= 1.4. Market order at the next one-minute bar's open.
- **Context / confluences**: {"vr": 1.4}; parameters `{"L": 120, "mode": "continuation", "vr": 1.4, "z": 1.0}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 tick beyond the last confirmed 5-minute swing, kept between 0.5 and 3.0 ATRh from the signal close. **Target**: 100% no target (payoff shape HIGH_RR). **BE**: none. **Partials**: none. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 359 trades, PF 1.23, WR 35.1%, net $48,399, avg $135, max DD $15,936, t 1.35, STRESS $44,091, null p 0.098, parameter support 1.00, management support 0.23 (discovery: 454 trades, PF 1.21, t 1.28, parameter robustness 1.00)
- **Holdout 2023-25**: 232 trades, PF 1.29, WR 37.9%, net $49,692, avg $214, max DD $22,645, longest losing streak 11; 2023 $2,009 / 2024 $24,533 / 2025 $23,150; STRESS net $46,908 (PF 1.27); **SUPPORTED** (t 1.30, z vs confirmation 0.48, null p 0.050)
- **2026 audit**: 40 trades, net $-2,195, PF 0.96, STRESS $-2,675; INCONCLUSIVE

### 16. `C87a31838e567ad3c` — H50 Trend morning -> lunch consolidation -> PM continuation (short, continuation)

- **Behaviour cluster** 22 (PROMISING; 3 members, 3 entry rules) — confirmation tier **PROMISING**
- **Entry**: SELL SHORT when at 11:30 the close is >= 0.4D below the RTH open with efficiency >= 0.1; entry at 13:30. Market order at the next one-minute bar's open.
- **Context / confluences**: none; parameters `{"cons": null, "m": 0.4, "mode": "continuation", "trig": null}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 100% no target (payoff shape MANAGED). **BE**: stop to entry after +0.5R. **Partials**: none. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 164 trades, PF 1.38, WR 18.9%, net $15,239, avg $93, max DD $7,992, t 1.13, STRESS $13,271, null p 0.059, parameter support 1.00, management support 0.00 (discovery: 349 trades, PF 1.31, t 1.11, parameter robustness 1.00)
- **Holdout 2023-25**: 131 trades, PF 1.74, WR 22.9%, net $29,271, avg $223, max DD $8,934, longest losing streak 14; 2023 $4,590 / 2024 $-626 / 2025 $25,307; STRESS net $27,699 (PF 1.68); **SUPPORTED** (t 1.65, z vs confirmation 0.96, null p 0.040)
- **2026 audit**: 30 trades, net $-5,600, PF 0.75, STRESS $-5,960; INCONCLUSIVE

### 17. `C82ee16a85ecc3f4d` — H47 Large overnight move + same-direction open (long, continuation)

- **Behaviour cluster** 8 (PROMISING; 20 members, 2 entry rules) — confirmation tier **PROMISING**
- **Entry**: BUY when at 09:30+15min, the RTH open gapped >= 0.5D above the previous RTH close. Market order at the next one-minute bar's open.
- **Context / confluences**: none; parameters `{"g": 0.5, "mode": "continuation", "open": null, "w": 15}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 25% at +1R, 75% no target (payoff shape MANAGED). **BE**: none. **Partials**: 25%@+1R / 75%@runner. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 153 trades, PF 1.43, WR 22.2%, net $17,706, avg $116, max DD $6,351, t 1.34, STRESS $15,870, null p 0.059, parameter support 0.50, management support 0.31 (discovery: 283 trades, PF 1.37, t 1.70, parameter robustness 0.50)
- **Holdout 2023-25**: 121 trades, PF 0.70, WR 15.7%, net $-14,755, avg $-122, max DD $18,386, longest losing streak 19; 2023 $-1,595 / 2024 $-4,048 / 2025 $-9,112; STRESS net $-16,207 (PF 0.68); **FAILED** (t -1.45, z vs confirmation -2.83, null p 0.941)
- **2026 audit**: 35 trades, net $4,499, PF 1.16, STRESS $4,079; WEAKER_THAN_EXPECTED

### 18. `C39c52e02a3c54412` — H06 Compression to expansion (long, continuation)

- **Behaviour cluster** 2 (PROMISING; 19 members, 2 entry rules) — confirmation tier **PROMISING**
- **Entry**: BUY when the close breaks above the previous 60-bar high; the previous 60 bars' realised vol was <= 0.6x its time-of-day norm. Market order at the next one-minute bar's open.
- **Context / confluences**: {"cth": 0.6}; parameters `{"N": 60, "cth": 0.6, "mode": "continuation", "strong": null}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1.5 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 100% no target (payoff shape HIGH_RR). **BE**: none. **Partials**: none. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 435 trades, PF 1.48, WR 46.0%, net $60,290, avg $139, max DD $10,414, t 2.79, STRESS $55,070, null p 0.020, parameter support 0.00, management support 0.31 (discovery: 618 trades, PF 1.15, t 1.15, parameter robustness 1.00)
- **Holdout 2023-25**: 303 trades, PF 0.93, WR 35.6%, net $-9,047, avg $-30, max DD $22,839, longest losing streak 9; 2023 $2,689 / 2024 $-716 / 2025 $-11,020; STRESS net $-12,683 (PF 0.91); **FAILED** (t -0.44, z vs confirmation -2.46, null p 0.644)
- **2026 audit**: 47 trades, net $3,947, PF 1.13, STRESS $3,383; WEAKER_THAN_EXPECTED

### 19. `C91756637ca7282e7` — H41 Variance-ratio trending regime + momentum (both, continuation)

- **Behaviour cluster** 40 (PROMISING; 13 members, 2 entry rules) — confirmation tier **PROMISING**
- **Entry**: BUY when the 15-minute move first exceeds +1.5 sigma units with variance ratio VR(5) over the last 120 minutes >= 1.2. SELL SHORT when the 15-minute move first falls below -1.5 sigma units with variance ratio VR(5) over the last 120 minutes >= 1.2. Market order at the next one-minute bar's open.
- **Context / confluences**: {"vr": 1.2}; parameters `{"L": 120, "mode": "continuation", "vr": 1.2, "z": 1.5}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 100% no target (payoff shape HIGH_RR). **BE**: none. **Partials**: none. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 1207 trades, PF 1.18, WR 29.3%, net $99,842, avg $83, max DD $48,427, t 1.92, STRESS $85,358, null p 0.039, parameter support 1.00, management support 0.38 (discovery: 1852 trades, PF 1.14, t 1.66, parameter robustness 1.00)
- **Holdout 2023-25**: 843 trades, PF 1.31, WR 30.5%, net $143,363, avg $170, max DD $17,936, longest losing streak 15; 2023 $4,804 / 2024 $63,531 / 2025 $75,028; STRESS net $133,247 (PF 1.28); **SUPPORTED** (t 2.43, z vs confirmation 1.25, null p 0.010)
- **2026 audit**: 158 trades, net $56,733, PF 1.45, STRESS $54,837; SUPPORTED

### 20. `Cd165e089c8a180ec` — H05 Volatility-shock momentum (both, continuation)

- **Behaviour cluster** 26 (PROMISING; 8 members, 2 entry rules) — confirmation tier **PROMISING**
- **Entry**: BUY when the 30-minute move first exceeds +1.5 sigma units while 15-minute realised vol >= 3.0x its same-time-of-day norm. SELL SHORT when the 30-minute move first falls below -1.5 sigma units while 15-minute realised vol >= 3.0x its same-time-of-day norm. Market order at the next one-minute bar's open.
- **Context / confluences**: {"v": 3.0}; parameters `{"mode": "continuation", "n": 30, "v": 3.0, "z": 1.5}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1.5 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 100% at +2R (payoff shape ASYMMETRIC). **BE**: none. **Partials**: none. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 242 trades, PF 1.39, WR 42.6%, net $57,932, avg $239, max DD $18,903, t 1.91, STRESS $55,028, null p 0.078, parameter support 0.33, management support 0.54 (discovery: 276 trades, PF 1.37, t 1.85, parameter robustness 1.00)
- **Holdout 2023-25**: 124 trades, PF 1.29, WR 41.1%, net $33,074, avg $267, max DD $32,512, longest losing streak 8; 2023 $-8,388 / 2024 $12,258 / 2025 $29,204; STRESS net $31,586 (PF 1.27); **WEAKER_THAN_EXPECTED** (t 0.98, z vs confirmation 0.10, null p 0.109)
- **2026 audit**: 31 trades, net $15,511, PF 1.35, STRESS $15,139; WEAKER_THAN_EXPECTED

### 21. `C2845a074bb5a5501` — H25 Correlation breakdown (short, continuation)

- **Behaviour cluster** 14 (PROMISING; 7 members, 2 entry rules) — confirmation tier **PROMISING**
- **Entry**: SELL SHORT when 30-minute NQ/ES correlation <= 0.65 and NQ's 30-minute beta residual <= -2.0 sigma. Market order at the next one-minute bar's open.
- **Context / confluences**: none; parameters `{"cth": 0.65, "mode": "continuation", "rz": 2.0}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 25% at +1R, 75% no target (payoff shape MANAGED). **BE**: none. **Partials**: 25%@+1R / 75%@runner. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 255 trades, PF 1.99, WR 21.2%, net $57,109, avg $224, max DD $6,058, t 2.85, STRESS $54,049, null p 0.020, parameter support 1.00, management support 0.15 (discovery: 473 trades, PF 1.22, t 1.13, parameter robustness 1.00)
- **Holdout 2023-25**: 137 trades, PF 1.47, WR 19.0%, net $17,570, avg $128, max DD $6,188, longest losing streak 14; 2023 $-1,710 / 2024 $17,030 / 2025 $2,249; STRESS net $15,926 (PF 1.41); **SUPPORTED** (t 1.19, z vs confirmation -0.89, null p 0.059)
- **2026 audit**: 32 trades, net $15,603, PF 1.93, STRESS $15,219; SUPPORTED

### 22. `C62eeef3eabed9056` — H47 Large overnight move + same-direction open (long, continuation)

- **Behaviour cluster** 10 (PROMISING; 6 members, 2 entry rules) — confirmation tier **PROMISING**
- **Entry**: BUY when at 09:30+5min, the RTH open gapped >= 0.25D above the previous RTH close and the close is >= 0.05D above the RTH open. Market order at the next one-minute bar's open.
- **Context / confluences**: {"open": "same"}; parameters `{"g": 0.25, "mode": "continuation", "open": "same", "w": 5}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 100% no target (payoff shape MANAGED). **BE**: none. **Partials**: none. **Trail**: atr_high 3. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 118 trades, PF 1.98, WR 33.9%, net $26,413, avg $224, max DD $3,497, t 2.27, STRESS $24,997, null p 0.020, parameter support 1.00, management support 0.23 (discovery: 211 trades, PF 1.38, t 1.40, parameter robustness 1.00)
- **Holdout 2023-25**: 89 trades, PF 1.53, WR 27.0%, net $16,069, avg $181, max DD $4,865, longest losing streak 8; 2023 $5,810 / 2024 $12,154 / 2025 $-1,895; STRESS net $15,001 (PF 1.48); **SUPPORTED** (t 1.21, z vs confirmation -0.29, null p 0.040)
- **2026 audit**: 19 trades, net $14,019, PF 2.01, STRESS $13,791; WEAKER_THAN_EXPECTED

### 23. `Cfcc0e08cf3dce32c` — H47 Large overnight move + same-direction open (both, continuation)

- **Behaviour cluster** 7 (PROMISING; 5 members, 2 entry rules) — confirmation tier **PROMISING**
- **Entry**: BUY when at 09:30+15min, the RTH open gapped >= 0.25D above the previous RTH close. SELL SHORT when at 09:30+15min, the RTH open gapped >= 0.25D below the previous RTH close. Market order at the next one-minute bar's open.
- **Context / confluences**: none; parameters `{"g": 0.25, "mode": "continuation", "open": null, "w": 15}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 100% no target (payoff shape MANAGED). **BE**: none. **Partials**: none. **Trail**: atr_high 3. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 588 trades, PF 1.25, WR 25.5%, net $50,133, avg $85, max DD $19,521, t 1.64, STRESS $43,077, null p 0.020, parameter support 0.50, management support 0.23 (discovery: 1132 trades, PF 1.27, t 2.17, parameter robustness 0.50)
- **Holdout 2023-25**: 409 trades, PF 0.95, WR 20.5%, net $-10,006, avg $-24, max DD $36,524, longest losing streak 18; 2023 $-6,384 / 2024 $16,839 / 2025 $-20,461; STRESS net $-14,914 (PF 0.93); **INCONCLUSIVE** (t -0.32, z vs confirmation -1.44, null p 0.554)
- **2026 audit**: 94 trades, net $13,904, PF 1.17, STRESS $12,776; WEAKER_THAN_EXPECTED

### 24. `C77d755b168515944` — X3 Correlation-regime momentum (both, continuation)

- **Behaviour cluster** 13 (PROMISING; 4 members, 2 entry rules) — confirmation tier **PROMISING**
- **Entry**: BUY when the 30-minute move first exceeds +2.0 sigma units with 390-minute NQ/ES correlation <= 0.75. SELL SHORT when the 30-minute move first falls below -2.0 sigma units with 390-minute NQ/ES correlation <= 0.75. Market order at the next one-minute bar's open.
- **Context / confluences**: {"reg": "low"}; parameters `{"mode": "continuation", "reg": "low", "z": 2.0}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 100% no target (payoff shape HIGH_RR). **BE**: none. **Partials**: none. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 154 trades, PF 1.36, WR 27.3%, net $19,119, avg $124, max DD $7,803, t 1.13, STRESS $17,271, null p 0.098, parameter support 0.00, management support 0.38 (discovery: 680 trades, PF 1.19, t 1.32, parameter robustness 1.00)
- **Holdout 2023-25**: 26 trades, PF 2.06, WR 26.9%, net $9,401, avg $362, max DD $2,963, longest losing streak 7; 2023 $4,415 / 2024 $4,986 / 2025 $0; STRESS net $9,089 (PF 2.00); **SUPPORTED** (t 1.16, z vs confirmation 0.76, null p 0.129)
- **2026 audit**: 0 trades, net $0, PF n/a, STRESS $0; INCONCLUSIVE

### 25. `C18117db2aa81a2bf` — H07 Opening-drive continuation (short, continuation)

- **Behaviour cluster** 20 (PROMISING; 2 members, 2 entry rules) — confirmation tier **PROMISING**
- **Entry**: SELL SHORT when at 09:30+30min the close is >= 0.3 x D below the RTH open with path efficiency since the open >= 0.4. Market order at the next one-minute bar's open.
- **Context / confluences**: {"e": 0.4}; parameters `{"e": 0.4, "m": 0.3, "mode": "continuation", "w": 30}`; entries 09:30-15:30 New York, flat by 16:00
- **Initial stop**: 1 x ATRh (ATR(14) of completed 15-minute bars) from the entry. **Target**: 100% at +2R (payoff shape ASYMMETRIC). **BE**: none. **Partials**: none. **Trail**: none. **Time exit**: session flat 16:00 New York.
- **Confirmation 2019-22**: 37 trades, PF 1.75, WR 43.2%, net $7,492, avg $202, max DD $3,338, t 1.41, STRESS $7,048, null p 0.098, parameter support 0.67, management support 0.08 (discovery: 74 trades, PF 1.43, t 1.34, parameter robustness 0.67)
- **Holdout 2023-25**: 30 trades, PF 1.24, WR 40.0%, net $3,215, avg $107, max DD $3,050, longest losing streak 5; 2023 $3,028 / 2024 $-42 / 2025 $229; STRESS net $2,855 (PF 1.21); **WEAKER_THAN_EXPECTED** (t 0.54, z vs confirmation -0.48, null p 0.277)
- **2026 audit**: 10 trades, net $-4,185, PF 0.57, STRESS $-4,305; INCONCLUSIVE

## M. 2023-2025 untouched holdout

- Classification counts: **{'SUPPORTED': 13, 'WEAKER_THAN_EXPECTED': 8, 'FAILED': 3, 'INCONCLUSIVE': 1}** (rules: SUPPORTED = net > 0, t >= 1 and not significantly below the confirmation mean; WEAKER = net > 0 otherwise; FAILED = net <= 0, n >= 20 and significantly below; INCONCLUSIVE otherwise).
- Equal-weight cohort (one contract each, 25 strategies, 5,781 trades): net **$626,278** (gross $707,212, STRESS $556,906); PF of pooled trades **1.20**; max DD of daily equity $99,366; worst day $-32,991; worst week $-35,647; positive months 23/36; max simultaneous positions 13.
- Pairwise daily-P&L correlation: max 0.64, median 0.04. Cohort null p (combined net vs 100 holdout null worlds) **0.030** (null mean $-61,775, 95th pct $400,887).
- By family: {"H05": 34571, "H06": -13471, "H07": 29151, "H08": 49332, "H09": 24057, "H20": 120595, "H25": 23664, "H41": 193055, "H43": 64961, "H45": 39098, "H47": 20366, "H48": 2228, "H50": 29271, "X3": 9401}; by direction: {"both": 419787, "long": 44374, "short": 162117}.

Per strategy:

| strategy_id | hypothesis | direction | trades | net_pnl | pf | win_rate | avg_trade | max_dd | longest_losing_streak | y2023_net | y2024_net | y2025_net | moderate_net_pnl | stress_net_pnl | pf_stress | t_stat | z_vs_confirmation | p_null | classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Cdf2b568ee1f8a182 | H20 | both | 795 | 120,595 | 1.21 | 0.385 | 152 | 42,886 | 13 | 23,719 | 48,978 | 47,898 | 124,570 | 111,055 | 1.19 | 1.73 | 0.103 | 0.0594 | SUPPORTED |
| Ca55086023a82dafa | H45 | both | 233 | 39,098 | 1.23 | 0.408 | 168 | 13,505 | 9 | 2,064 | 20,917 | 16,117 | 40,263 | 36,302 | 1.22 | 1.38 | -0.195 | 0.109 | SUPPORTED |
| Ce5e284855c7e4be1 | H09 | short | 177 | 24,057 | 1.39 | 0.559 | 136 | 8,872 | 5 | 13,425 | 3,574 | 7,058 | 24,942 | 21,933 | 1.35 | 1.62 | 0.0149 | 0.0396 | SUPPORTED |
| Cfa444b4386db8d33 | H47 | long | 99 | 29,058 | 1.9 | 0.273 | 294 | 4,621 | 8 | 3,970 | 18,668 | 6,420 | 29,553 | 27,870 | 1.84 | 2.18 | 0.834 | 0.0198 | SUPPORTED |
| C1a82f05b6fe1e264 | H05 | long | 72 | 1,497 | 1.02 | 0.403 | 20.8 | 28,895 | 6 | 4,828 | 5,820 | -9,151 | 1,857 | 633 | 1.01 | 0.0713 | -1.27 | 0.446 | WEAKER_THAN_EXPECTED |
| C2839e22b29c0cb17 | H06 | both | 331 | -4,424 | 0.968 | 0.29 | -13.4 | 35,340 | 12 | 5,245 | 4,880 | -14,549 | -2,769 | -8,396 | 0.94 | -0.185 | -1.78 | 0.446 | FAILED |
| C915ea812fd5945a5 | H07 | both | 225 | 17,630 | 1.15 | 0.24 | 78.4 | 11,404 | 14 | 125 | 15,747 | 1,758 | 18,755 | 14,930 | 1.12 | 0.671 | -0.846 | 0.228 | WEAKER_THAN_EXPECTED |
| C046be57651136b5c | H08 | long | 66 | 8,298 | 1.25 | 0.348 | 126 | 7,610 | 9 | 3,690 | -1,077 | 5,686 | 8,628 | 7,506 | 1.22 | 0.751 | -0.314 | 0.238 | WEAKER_THAN_EXPECTED |
| Ceef182c53f2e1673 | H08 | short | 75 | 36,085 | 1.51 | 0.52 | 481 | 17,982 | 5 | 8,158 | -5,639 | 33,566 | 36,460 | 35,185 | 1.49 | 1.38 | 0.0723 | 0.0792 | SUPPORTED |
| Cf048ad80a1bd7603 | H08 | long | 186 | 4,948 | 1.05 | 0.355 | 26.6 | 17,734 | 11 | 11,346 | 5,138 | -11,535 | 5,878 | 2,716 | 1.03 | 0.27 | -0.656 | 0.525 | WEAKER_THAN_EXPECTED |
| C5fbf4cc530f79d84 | H07 | long | 41 | 8,306 | 1.6 | 0.366 | 203 | 4,217 | 8 | 4,888 | 6,804 | -3,386 | 8,511 | 7,814 | 1.55 | 1.03 | -0.155 | 0.109 | SUPPORTED |
| C16cd8e3c605af462 | H43 | both | 836 | 64,961 | 1.14 | 0.276 | 77.7 | 31,523 | 19 | 20,229 | 5,598 | 39,134 | 69,141 | 54,929 | 1.11 | 1.15 | -1.24 | 0.0792 | SUPPORTED |
| C936c5aa985ba50fd | H48 | short | 85 | 2,228 | 1.06 | 0.188 | 26.2 | 11,070 | 11 | -1,971 | 7,022 | -2,824 | 2,652 | 1,208 | 1.03 | 0.163 | -1.13 | 0.416 | WEAKER_THAN_EXPECTED |
| C431e7e54dbc7b968 | H25 | both | 115 | 6,095 | 1.17 | 0.165 | 53 | 7,555 | 14 | -1,200 | 3,241 | 4,054 | 6,670 | 4,715 | 1.13 | 0.483 | -0.296 | 0.337 | WEAKER_THAN_EXPECTED |
| Ce2bc1c0f03390096 | H41 | short | 232 | 49,692 | 1.29 | 0.379 | 214 | 22,645 | 11 | 2,009 | 24,533 | 23,150 | 50,852 | 46,908 | 1.27 | 1.3 | 0.482 | 0.0495 | SUPPORTED |
| C87a31838e567ad3c | H50 | short | 131 | 29,271 | 1.74 | 0.229 | 223 | 8,934 | 14 | 4,590 | -626 | 25,307 | 29,926 | 27,699 | 1.68 | 1.65 | 0.962 | 0.0396 | SUPPORTED |
| C82ee16a85ecc3f4d | H47 | long | 121 | -14,755 | 0.7 | 0.157 | -122 | 18,386 | 19 | -1,595 | -4,048 | -9,112 | -14,150 | -16,207 | 0.679 | -1.45 | -2.83 | 0.941 | FAILED |
| C39c52e02a3c54412 | H06 | long | 303 | -9,047 | 0.933 | 0.356 | -29.9 | 22,839 | 9 | 2,689 | -716 | -11,020 | -7,532 | -12,683 | 0.908 | -0.436 | -2.46 | 0.644 | FAILED |
| C91756637ca7282e7 | H41 | both | 843 | 143,363 | 1.31 | 0.305 | 170 | 17,936 | 15 | 4,804 | 63,531 | 75,028 | 147,578 | 133,247 | 1.28 | 2.43 | 1.25 | 0.0099 | SUPPORTED |
| Cd165e089c8a180ec | H05 | both | 124 | 33,074 | 1.29 | 0.411 | 267 | 32,512 | 8 | -8,388 | 12,258 | 29,204 | 33,694 | 31,586 | 1.27 | 0.983 | 0.101 | 0.109 | WEAKER_THAN_EXPECTED |
| C2845a074bb5a5501 | H25 | short | 137 | 17,570 | 1.47 | 0.19 | 128 | 6,188 | 14 | -1,710 | 17,030 | 2,249 | 18,254 | 15,926 | 1.41 | 1.19 | -0.887 | 0.0594 | SUPPORTED |
| C62eeef3eabed9056 | H47 | long | 89 | 16,069 | 1.53 | 0.27 | 181 | 4,865 | 8 | 5,810 | 12,154 | -1,895 | 16,514 | 15,001 | 1.48 | 1.21 | -0.29 | 0.0396 | SUPPORTED |
| Cfcc0e08cf3dce32c | H47 | both | 409 | -10,006 | 0.951 | 0.205 | -24.5 | 36,524 | 18 | -6,384 | 16,839 | -20,461 | -7,961 | -14,914 | 0.928 | -0.321 | -1.44 | 0.554 | INCONCLUSIVE |
| C77d755b168515944 | X3 | both | 26 | 9,401 | 2.06 | 0.269 | 362 | 2,963 | 7 | 4,415 | 4,986 | 0 | 9,531 | 9,089 | 2 | 1.16 | 0.76 | 0.129 | SUPPORTED |
| C18117db2aa81a2bf | H07 | short | 30 | 3,215 | 1.24 | 0.4 | 107 | 3,050 | 5 | 3,028 | -42 | 229 | 3,365 | 2,855 | 1.21 | 0.543 | -0.483 | 0.277 | WEAKER_THAN_EXPECTED |

Monthly cohort net ($):

| month | net |
|---|---|
| 2023-01 | 7,474 |
| 2023-02 | -25,800 |
| 2023-03 | 11,473 |
| 2023-04 | 24,543 |
| 2023-05 | 39,884 |
| 2023-06 | 19,244 |
| 2023-07 | 13,828 |
| 2023-08 | 53,400 |
| 2023-09 | -16,342 |
| 2023-10 | -4,312 |
| 2023-11 | -9,291 |
| 2023-12 | -6,317 |
| 2024-01 | 17,294 |
| 2024-02 | -54,306 |
| 2024-03 | -7,812 |
| 2024-04 | 83,325 |
| 2024-05 | 1,584 |
| 2024-06 | 216 |
| 2024-07 | 67,994 |
| 2024-08 | 34,784 |
| 2024-09 | 61,477 |
| 2024-10 | 2,442 |
| 2024-11 | 5,357 |
| 2024-12 | 73,215 |
| 2025-01 | -49,370 |
| 2025-02 | 95,558 |
| 2025-03 | 39,537 |
| 2025-04 | 160,896 |
| 2025-05 | -18,675 |
| 2025-06 | -27,552 |
| 2025-07 | 2,294 |
| 2025-08 | -21,732 |
| 2025-09 | -15,220 |
| 2025-10 | 57,010 |
| 2025-11 | 40,067 |
| 2025-12 | -29,886 |

Correlation matrix: `results/holdout/correlation_matrix.csv`; trades: `results/holdout/trades.parquet`.

## N. 2026 secondary historical audit (2026-01-01 .. 2026-08-14; NQ data ends 2026-08-10)

- Classification counts: **{'WEAKER_THAN_EXPECTED': 10, 'INCONCLUSIVE': 9, 'SUPPORTED': 4, 'FAILED': 2}**; cohort net **$100,100** over 8 months (5 positive), PF 1.09, max DD $86,883, STRESS $85,436; cohort null p **0.257**.
- Erratum: strategy C77d755b168515944 (X3) had 0 trades in 2026; its printed null p (0.0099) is wrong and should be 1.0 (see Section A).

| strategy_id | hypothesis | direction | trades | net_pnl | pf | win_rate | avg_trade | max_dd | stress_net_pnl | t_stat | classification |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Cdf2b568ee1f8a182 | H20 | both | 167 | -52,593 | 0.767 | 0.329 | -315 | 62,565 | -54,597 | -1.36 | FAILED |
| Ca55086023a82dafa | H45 | both | 60 | -8,290 | 0.901 | 0.35 | -138 | 24,604 | -9,010 | -0.348 | INCONCLUSIVE |
| Ce5e284855c7e4be1 | H09 | short | 39 | 8,294 | 1.37 | 0.615 | 213 | 9,295 | 7,826 | 0.828 | WEAKER_THAN_EXPECTED |
| Cfa444b4386db8d33 | H47 | long | 20 | 16,650 | 2.35 | 0.3 | 832 | 3,032 | 16,410 | 1.25 | SUPPORTED |
| C1a82f05b6fe1e264 | H05 | long | 22 | 4,252 | 1.17 | 0.364 | 193 | 9,516 | 3,988 | 0.266 | WEAKER_THAN_EXPECTED |
| C2839e22b29c0cb17 | H06 | both | 53 | 26,378 | 2.11 | 0.434 | 498 | 8,832 | 25,742 | 1.66 | SUPPORTED |
| C915ea812fd5945a5 | H07 | both | 56 | -17,074 | 0.687 | 0.232 | -305 | 27,960 | -17,746 | -1.06 | FAILED |
| C046be57651136b5c | H08 | long | 19 | -3,657 | 0.809 | 0.263 | -192 | 12,553 | -3,885 | -0.373 | INCONCLUSIVE |
| Ceef182c53f2e1673 | H08 | short | 20 | -11,980 | 0.738 | 0.35 | -599 | 24,453 | -12,220 | -0.508 | INCONCLUSIVE |
| Cf048ad80a1bd7603 | H08 | long | 48 | 12,827 | 1.38 | 0.438 | 267 | 11,371 | 12,251 | 0.873 | WEAKER_THAN_EXPECTED |
| C5fbf4cc530f79d84 | H07 | long | 11 | 9,886 | 2.22 | 0.364 | 899 | 4,237 | 9,754 | 0.945 | WEAKER_THAN_EXPECTED |
| C16cd8e3c605af462 | H43 | both | 165 | -2,630 | 0.981 | 0.333 | -15.9 | 32,482 | -4,610 | -0.0937 | INCONCLUSIVE |
| C936c5aa985ba50fd | H48 | short | 22 | -863 | 0.949 | 0.273 | -39.2 | 7,356 | -1,127 | -0.08 | INCONCLUSIVE |
| C431e7e54dbc7b968 | H25 | both | 24 | 6,664 | 1.5 | 0.25 | 278 | 4,388 | 6,376 | 0.654 | WEAKER_THAN_EXPECTED |
| Ce2bc1c0f03390096 | H41 | short | 40 | -2,195 | 0.961 | 0.325 | -54.9 | 36,974 | -2,675 | -0.0961 | INCONCLUSIVE |
| C87a31838e567ad3c | H50 | short | 30 | -5,600 | 0.749 | 0.233 | -187 | 7,720 | -5,960 | -0.46 | INCONCLUSIVE |
| C82ee16a85ecc3f4d | H47 | long | 35 | 4,499 | 1.16 | 0.171 | 129 | 8,782 | 4,079 | 0.301 | WEAKER_THAN_EXPECTED |
| C39c52e02a3c54412 | H06 | long | 47 | 3,947 | 1.13 | 0.383 | 84 | 10,033 | 3,383 | 0.321 | WEAKER_THAN_EXPECTED |
| C91756637ca7282e7 | H41 | both | 158 | 56,733 | 1.45 | 0.348 | 359 | 17,573 | 54,837 | 1.54 | SUPPORTED |
| Cd165e089c8a180ec | H05 | both | 31 | 15,511 | 1.35 | 0.387 | 500 | 20,013 | 15,139 | 0.644 | WEAKER_THAN_EXPECTED |
| C2845a074bb5a5501 | H25 | short | 32 | 15,603 | 1.93 | 0.219 | 488 | 5,688 | 15,219 | 1.08 | SUPPORTED |
| C62eeef3eabed9056 | H47 | long | 19 | 14,019 | 2.01 | 0.263 | 738 | 5,470 | 13,791 | 0.956 | WEAKER_THAN_EXPECTED |
| Cfcc0e08cf3dce32c | H47 | both | 94 | 13,904 | 1.17 | 0.213 | 148 | 16,317 | 12,776 | 0.461 | WEAKER_THAN_EXPECTED |
| C77d755b168515944 | X3 | both | 0 | 0 |  |  |  | 0 | 0 |  | INCONCLUSIVE |
| C18117db2aa81a2bf | H07 | short | 10 | -4,185 | 0.571 | 0.3 | -418 | 8,894 | -4,305 | -0.817 | INCONCLUSIVE |

Combined view (written only after both standalone reports were sealed): 2023-2026 cohort net $726,378. Agreement of classes: `results/tables/holdout_plus_2026.csv`.

## O. What worked

Evidence ladder used below: discovery (in-sample) -> confirmation 2019-22 (out-of-sample, vs 100 null worlds) ->
untouched holdout 2023-25 -> 2026 secondary audit (7.5 months, low power).

1. **Intraday trend continuation after an efficient, persistent move.** The largest behaviour (191 confirmation
   survivors across H01/H02/H03/H04/H10/H20/H27/H30/X3) is "a large 15-30-minute move made along a smooth path
   continues". Its representative (H20, 30-min Z >= 2 with normalised efficiency >= 2.4, both directions, 1.5 ATR
   stop, no target, flat 16:00) was STRONG in confirmation and **SUPPORTED** in the holdout (+$120.6k, 795 trades,
   PF 1.21, every holdout year positive) -- but **FAILED** in the 2026 audit (-$52.6k, 167 trades).
2. **Momentum in a persistent regime.** 15-minute momentum only when the 120-minute variance ratio >= 1.2 (H41)
   was the best holdout strategy (+$143.4k, PF 1.31, t 2.43, null p 0.01) and **SUPPORTED again in 2026**
   (+$56.7k). Positive 5-minute autocorrelation (H43) as a momentum filter: SUPPORTED in the holdout (+$65.0k).
3. **Day-structure trend continuation.** Early trend-day classification (H45, 10:30, >= 4 of 5 criteria),
   the 15:00 last-hour trend (H09 short), the 10:30 morning trend (H08 short) and the 11:30 trend + 13:30 entry
   (H50 short) were all SUPPORTED in the holdout; their 2026 results were small and mixed.
4. **Gap + same-direction open, long side (H47).** Both long variants that required the open to confirm the gap
   were SUPPORTED in the holdout (+$29.1k and +$16.1k) and positive in 2026 (one SUPPORTED again, +$16.7k).
5. **Correlation breakdown -> continuation (H25).** When NQ/ES 30-minute correlation breaks down, NQ's
   beta-residual move CONTINUED (the convergence version failed). Holdout: one SUPPORTED (+$17.6k), one
   WEAKER (+$6.1k); 2026: both positive (one SUPPORTED).
6. **The cohort as a whole.** Equal-weight holdout net **+$626k** on 5,781 trades (PF 1.20; STRESS still
   +$557k), 23 of 36 months positive, and **above 97% of the no-edge null worlds (p = 0.030)**. 13 of 25 SUPPORTED,
   8 WEAKER_THAN_EXPECTED (all still net positive), 3 FAILED, 1 INCONCLUSIVE; 21 of 25 positive under STRESS.

Important qualification: the evidence is **population-level**. Individually, most members do not survive a
search-wide (max-t) correction in confirmation (`p_familywise_bucket` <= 0.10 only for H43, H06 long, H25 short);
the confirmation aggregates (52 pre-null STRONG vs a null mean of 2.5-7.4; 43 behaviours vs ~17) and the holdout
cohort p of 0.03 are what show that reality exceeded chance.

## P. What failed with adequate evidence

Large samples, strongly negative after costs in discovery (not carried forward; t medians over all specs):

| hypothesis | specs | net > 0 | median trades | median t | verdict |
|---|---|---|---|---|---|
| H22 NQ leads ES (ES traded) | 384 | 0 | 4,624 | -7.98 | rejected (gross-positive in 127 specs; costs dominate) |
| H26 mechanical SMT / non-confirmation | 504 | 0 | 5,824 | -5.92 | rejected |
| H24 beta-adjusted residual REVERSION | 270 | 0 | 2,149 | -5.16 | rejected (the residual continued instead -- H25) |
| H34 deceleration (three windows) -> reversal | 168 | 0 | 3,369 | -5.36 | rejected |
| H15 session-extreme rejection | 284 | 8 | 1,437 | -2.64 | rejected |
| H44 negative autocorrelation + mean reversion | 318 | 17 | 997 | -2.91 | rejected |
| H28 cross-market disagreement reversal | 400 | 13 | 1,171 | -2.25 | rejected |
| X2 first half-hour -> last half-hour | 156 | 0 | 983 | -2.08 | rejected |
| H13 rolling-mean overextension | 501 | 38 | 889 | -1.90 | rejected (2 PRIMARY, both WEAK later) |

In confirmation, **75 PRIMARY candidates were REJECTED with adequate evidence** (significantly below their
discovery estimate and non-positive): X3 36 (the high-correlation-regime variants), H42 VR mean-reversion 14,
H07 5, H35 5, H14 3, H47 3, H19 2, H21 2 and 5 others. In the holdout, **both compression-to-expansion
representatives (H06) FAILED** (-$4.4k, -$9.0k; z -1.8 / -2.5 vs confirmation) and the large-gap-long-without-
open-confirmation H47 variant FAILED (-$14.8k, z -2.8). In 2026 the H20 efficient-momentum and H07 opening-drive
representatives FAILED (short sample).

## Q. What remains inconclusive / underpowered

- 1,013 PRIMARY candidates were INCONCLUSIVE in confirmation (mostly positive but below PROMISING, or < 30 trades)
  and 416 WEAK (non-positive but not significantly below their discovery estimate).
- Low-frequency day-type strategies (30-80 trades a year) cannot distinguish a modest edge from noise in one
  year; their holdout t-stats are 0.2-1.6 and several WEAKER_THAN_EXPECTED results are simply underpowered.
- The X3 low-correlation momentum member traded 26 times in the holdout and not at all in 2026.
- The whole **2026 audit** (1,222 trades, 7.5 months) is underpowered: cohort +$100k but null p 0.26.
- H05 volatility-shock momentum and H48 overnight-rejection: positive but weaker than expected in both the holdout
  and 2026.
- ES->NQ lead-lag (H21): gross-positive in 315 of 512 specs, but only 17 PRIMARY and none survived confirmation;
  the effect may exist below the resolution of one-minute bars plus one-tick slippage.

## R. Limitations

1. **Prior exposure.** 2019-2026 NQ/ES history is public and was used by V1/V2; the brief's hypothesis list and my
   own priors were formed with that knowledge. No file permission can undo this; the holdout is untouched only in
   the sense that no V3 code read it before the cohort was frozen.
2. **Isolation** was software/stage-gate only (research ran as Administrator); the ledger is hash-chained and
   verifies, but the OS did not prevent access.
3. **Regimes.** Both 2019-22 and 2023-25 were strongly trending, high-volatility periods (Covid crash, 2022 bear
   market, 2023-25 AI rally, 2025 tariff shock). Trend-following intraday strategies are regime-sensitive; the
   quieter 2010-18 discovery period and the mixed 2026 audit are reminders.
4. **Execution model.** One-minute OHLC bars: next-bar-open market fills, 1 tick slippage per side (2 ticks in
   STRESS), targets need a 1-tick trade-through, stop-first on ambiguous bars. No queue, latency, or fast-market
   slippage model; volume is not used. A volatility-scaled slippage diagnostic was declined before the holdout.
5. **Null model.** Per-minute sign flips destroy all sign predictability, including microstructure bounce, and
   turn each world into a random walk whose chance trends can be large (null worlds differ a lot). 100 worlds give
   p-value resolution of 1/51 per style and 1/101 pooled; p-values are not more precise than that.
6. **Dependence.** Candidates are heavily overlapping parameterisations; candidate counts overstate independent
   evidence. Behaviour clusters (43 at rho 0.50) are the fairer unit, and even members of the final cohort have
   holdout correlations up to 0.64.
7. **Sizing.** One contract per strategy, equal weight; no volatility targeting or portfolio risk limits. The cohort
   holdout drawdown was $99k on one contract per strategy, with up to 13 positions open at once.
8. **Design choices.** Threshold scales were calibrated from discovery feature quantiles (no returns); family
   definitions (e.g. the structural stop, the trend-day criteria) are one reasonable choice among many.
9. **Instruments.** NQ only (plus one ES family); no transfer test to ES or other indices.
10. **One reporting bug** (2026 null p for a zero-trade strategy) is documented in an erratum; sealed files were not
    edited.

## S. True-forward start

- Research freeze: see header (`freezes/V3_RESEARCH_FREEZE.json`); gate state **TRUE_FORWARD**.
- **TRUE_FORWARD_START = the session ending 2026-09-24** (opens 2026-09-23 18:00 New York).
- **TRUE FORWARD HAS NOT STARTED**: the newest bars in the lab end 2026-08-10 (NQ) / 2026-08-14 (ES), before the
  freeze. Everything up to then is historical.
- Protocol: `forward/FORWARD_PROTOCOL.md`; evaluator: `forward/run_forward.py` (verifies both freezes, refuses to
  change any rule, counts only trades from TRUE_FORWARD_START, logs every evaluation to the ledger).

## Research questions

1. **Does intraday momentum still show evidence?** Yes, conditionally. Plain momentum (H01 without filters) was
   mostly cost-negative in discovery, but momentum on a smooth path (H20/H01 with efficiency) or in a persistent
   regime (H41, H43) survived confirmation (beating null worlds) and the untouched holdout; 2026 was mixed
   (H41 held, H20 failed).
2. **Does high path efficiency improve momentum?** Yes. Adding the efficiency filter raised the average net trade
   in 69% of discovery pairs and in 90% of confirmation pairs (median +$26/trade); the efficiency-filtered H20
   representative was SUPPORTED in the holdout. Efficiency alone as a signal (H30) was weak.
3. **Does acceleration contain incremental information?** A little. H02's acceleration condition improved the
   average trade in essentially every pair in both periods, but it mostly turned large losers into smaller ones
   (only 10 PRIMARY specs); H33 3 PRIMARY, H29 relative acceleration none. Not a stand-alone edge.
4. **Does ES confirmation improve NQ signals?** No material improvement: H27's ES-agreement filter changed the
   average trade by about +$0.1 (discovery) / +$2.6 (confirmation); the correlation-regime filter (X3) did not
   replicate (41% of pairs improved) and 36 of its variants were REJECTED.
5. **Measurable ES -> NQ or NQ -> ES lead-lag?** Gross traces only. ES->NQ (H21) was gross-positive in 315/512
   specs but only 17 PRIMARY and none survived confirmation; NQ->ES (H22) had no positive spec after costs
   (median t -8.0). Not exploitable with one-minute bars and one tick of slippage.
6. **Does the beta-adjusted NQ/ES residual mean-revert?** No (H24: 0 of 270 specs profitable). The opposite held:
   after a correlation breakdown NQ's residual move tended to continue (H25 continuation: 2 cohort members,
   positive in the holdout and 2026).
7. **Does mechanical SMT / non-confirmation contain useful information?** No (H26: 0 of 504 specs profitable,
   median t -5.9; the rejection trigger reduced losses but never made it profitable).
8. **Does realised-volatility state decide momentum vs mean reversion?** Persistence measures matter more than the
   volatility level: VR >= 1.2-1.4 and positive autocorrelation improved momentum in both periods and produced
   holdout-supported strategies; no regime (VR <= 0.8, negative autocorrelation, vol shocks) made mean reversion
   work (H42: 14 REJECTED; H44 none). Vol-shock momentum (H05) was positive but weaker than expected out of sample.
9. **Can early-session information classify trend vs range days usefully?** Trend days: yes (H45 STRONG in
   confirmation and SUPPORTED in the holdout; H08/H09/H50 related members mostly supported). Range days: no
   (H46 fades never became tradable).
10. **Does compression predict directional expansion?** In discovery and confirmation it looked so (H06 compression
    filter improved the average trade; 2 STRONG), but **both H06 cohort members FAILED the holdout**; H39 and H40
    produced nothing durable. Not supported.
11. **Which confluences add genuine incremental information?** Replicated in confirmation (share of pairs whose
    average trade improved): path efficiency on momentum (H01, 90%), efficiency of the opening drive (H07, 89%),
    closing location at 15:00 (H09, 81%), positive autocorrelation (H43, 85%), variance ratio (H41, 76%),
    deterioration before fading a morning move (H19, 77%, though H19 itself stayed unprofitable), 120/30-minute
    agreement (H03, 73-75%). Did NOT replicate or hurt: HTF-trend filters (H04, 23-46%), vol-shock filter (H05,
    42%), correlation regime (X3, 41%), pullback quality (H35, 24%), efficiency/location on the morning trend
    (H08) and efficiency on the last hour (H09), lunch consolidation (H50), pullback entries vs impulse entries
    (H10). 13 of the 25 cohort members use no confluence, 11 use one, 1 uses two.
12. **Which entry behaviours survive across multiple management styles?** STRONG required >= 50% of the entry's
    Stage-A exits to be PRIMARY and positive in confirmation; the momentum/efficiency behaviour, the day-structure
    trends (H08/H45, H09) and gap + same-direction open (H47) met it. Cohort median management support 0.38.
13. **Do BE stops help?** No. Breakeven beat the identical no-BE control in 17% of discovery pairs and 31% of
    confirmation pairs; early BE (0.5R) was the most harmful; a late BE (1.5R) was roughly neutral.
14. **Do partials help?** No. Partial / runner plans beat their single-target control in 11% of discovery pairs
    and 17% of confirmation pairs (they raise win rate but cut the average trade).
15. **Do trailing stops help?** No on average (beat the no-trail control in 23% of discovery / 28% of confirmation pairs); the widest trail
    (3 ATR) was closest to neutral. Advanced management did not add value in V3.
16. **Which RR profile suits which family?** Continuation / momentum / day-trend families: uncapped exits (no
    target, held to 16:00) or >= 2R targets (confirmation: 88% of HIGH_RR PRIMARY positive, median t 1.07, vs
    71% / 0.60 for 1-1.5R); 21 of 25 cohort members use no fixed target or >= 2R. Reversal families: every shape
    was weak; negative RR (0.5-0.75R) was the worst in discovery (3% positive). No family preferred negative RR.
17. **Which behaviours survive confirmation?** 43 behaviours (7 STRONG): efficient momentum; H01/H03/H20 long;
    H08/H45 morning trend; H09 last hour; H47 gap + open; H05 vol-shock momentum; H06 compression breakout; plus
    PROMISING H07, H43, H48, H25, H41, H50, X3 behaviours. Reality exceeded chance on every aggregate (p ~0.01-0.03).
18. **Which survive the untouched holdout?** SUPPORTED: H20 efficient momentum, H45 trend day, H09 last-hour
    short, H47 gap + open long (2), H08 morning-trend short, H07 efficient opening-drive long, H43 autocorrelation
    momentum, H41 VR momentum (2), H50 trend -> lunch -> PM short, H25 correlation-breakdown continuation short, X3
    low-correlation momentum (26 trades). FAILED: H06 compression breakout (2) and H47 large-gap long without open
    confirmation.
19. **Does the 2026 audit agree?** Partly. Cohort +$100k (PF 1.09) with 14 of 25 STRESS-positive, but null p 0.26
    on 7.5 months. Of the 13 holdout-SUPPORTED strategies, 3 were SUPPORTED again (H41 both, H47 long with open,
    H25 short), 3 positive but weaker, 5 negative-but-inconclusive, 1 FAILED (H20) and 1 did not trade (X3).
20. **How much survives STRESS costs?** Discovery: 3,300 of 8,652 baseline-profitable specs (38%); 360 PRIMARY
    specs had negative STRESS. Confirmation: all 899 STRONG/PROMISING were STRESS-positive (required for STRONG).
    Holdout: cohort STRESS net +$557k vs +$626k BASELINE; 21 of 25 members STRESS-positive. 2026: +$85k STRESS.

**Did V3 improve on V2?** Methodologically, yes: V2's six finalists were chosen with every historical year through
2026 as selection data, so V2 had no clean historical test; V3 froze its cohort before an untouched three-year
holdout, and that cohort beat the no-edge nulls there (p = 0.03). V3 also shows that V2's heavy management search
was unlikely to add value (breakeven, partials and trails lost to plain exits in both V3 periods). The
performance numbers of V2 and V3 are not directly comparable (different selection data, cohorts and periods).

**Did the untouched holdout support confirmation?** Largely at the cohort level (21 of 25 net positive, 13 SUPPORTED,
p = 0.03); not for compression breakouts or the unconfirmed large-gap long.
