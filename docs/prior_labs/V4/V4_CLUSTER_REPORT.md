# V4 cluster report (DISCOVERY)

Input: 1201 passing candidates (passing candidates). Candidates were clustered greedily by daily-P&L correlation (threshold 0.6), and each cluster's representative is its most robust member (ties broken by t). **114 clusters, giving a validation set of 114 representatives.**

Representative families: {"PATH": 14, "VOL": 14, "XMKT": 14, "OPEN": 15, "PERS": 3, "JUMP": 6, "REOPEN": 10, "RET": 22, "TECH": 6, "VWAP": 6, "DIST": 3, "CAL": 1}

Representative variants: {"cont_long": 36, "cont_both": 57, "cont_short": 11, "rev_both": 8, "rev_long": 2}

Robustness classes (representatives): {"broad": 105, "intermediate": 9}

Note: the preregistered neighbourhood criterion (neighbour t >= 1 and net > 0) is lenient. Here 'broad' means the neighbourhood is not negative, not that the plateau is strong.

| # | rep t | cluster size | family | trigger | variant | filters | exit | trades | robustness |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 4.40 | 303 | PATH | PATH:r2_cross:H=60,thr=0.85 | cont_long | on_aligned, open_aligned | S1_R3 | 252 | broad (1.00) |
| 2 | 4.15 | 130 | VOL | VOL:dirvol_cross:thr=0.7 | cont_long | on_aligned, trend240_aligned | S2_R3 | 363 | broad (1.00) |
| 3 | 4.03 | 11 | PATH | PATH:r2_cross:H=30,thr=0.7 | cont_both | on_aligned, trend240_aligned | S1_T120 | 1008 | broad (1.00) |
| 4 | 3.98 | 4 | XMKT | XMKT:vol_disagree:thr=0.7 | cont_long | on_aligned, open_aligned | S1_R3 | 216 | broad (0.75) |
| 5 | 3.94 | 90 | OPEN | OPEN:opening_move:X=5,thr=1.5 | cont_short | sgnvol_aligned | S2_T120 | 240 | broad (1.00) |
| 6 | 3.77 | 6 | PATH | PATH:clean_trend:H=30 | cont_both | jump_recent, vr_high | S1_EOD | 258 | broad (1.00) |
| 7 | 3.74 | 65 | PATH | PATH:clean_trend:H=30 | cont_short | vr_high, vwap_aligned | S1_EOD | 334 | broad (1.00) |
| 8 | 3.70 | 24 | PERS | PERS:momentum_at_persistence_onset: | cont_short | first_hour, range_top_for_long | S1_EOD | 201 | broad (1.00) |
| 9 | 3.66 | 9 | OPEN | OPEN:opening_move:X=30,thr=0.5 | cont_both | on_aligned, sgnvol_aligned | S1_T60 | 203 | broad (0.88) |
| 10 | 3.64 | 6 | JUMP | JUMP:jump_then_smooth: | cont_long | on_aligned, vwap_aligned | S2_T120 | 246 | broad (0.80) |
| 11 | 3.64 | 25 | PATH | PATH:er_cross:H=15,thr=0.5 | cont_both | semi_aligned, vr_high | S2_R3 | 809 | broad (1.00) |
| 12 | 3.63 | 2 | REOPEN | REOPEN:orb:X=15 | cont_long | on_aligned, sgnvol_aligned | S2_T30 | 205 | broad (0.83) |
| 13 | 3.63 | 14 | RET | RET:retz_cross:H=5,thr=2.0 | cont_both | corr_low, sgnvol_aligned | S2_R3 | 264 | broad (1.00) |
| 14 | 3.59 | 7 | RET | RET:retz_cross:H=30,thr=1.5 | cont_both | corr_low, open_aligned | S2_R2 | 226 | broad (0.86) |
| 15 | 3.58 | 92 | RET | RET:open_retz_cross:thr=2.0 | cont_long | on_aligned, range_top_for_long | S2_R3 | 205 | broad (1.00) |
| 16 | 3.57 | 2 | REOPEN | REOPEN:orb:X=15 | cont_both | on_aligned, trend240_aligned | S1_T60 | 341 | broad (0.83) |
| 17 | 3.54 | 26 | RET | RET:open_retz_cross:thr=2.0 | cont_both | semi_aligned, volreg_low | S2_R3 | 648 | broad (1.00) |
| 18 | 3.53 | 35 | REOPEN | REOPEN:orb:X=15 | cont_both | on_aligned, trend240_aligned | S1_EOD | 341 | broad (1.00) |
| 19 | 3.49 | 9 | VOL | VOL:vol_accel_up:thr=1.0 | cont_long | on_aligned, open_aligned | S1_R3 | 304 | broad (0.80) |
| 20 | 3.47 | 5 | PATH | PATH:er_cross:H=15,thr=0.5 | cont_both | volreg_low, vr_high | S2_EOD | 426 | broad (1.00) |
| 21 | 3.46 | 5 | RET | RET:trend_agree_full: | cont_both | er_high, trend240_aligned | S2_R3 | 305 | broad (0.75) |
| 22 | 3.42 | 29 | RET | RET:retz_cross:H=30,thr=1.5 | cont_both | corr_low, range_top_for_long | S1_T60 | 245 | broad (0.88) |
| 23 | 3.41 | 6 | XMKT | XMKT:corr_breakdown:thr=0.5 | cont_both | first_hour | S2_T120 | 230 | broad (1.00) |
| 24 | 3.40 | 4 | XMKT | XMKT:vol_disagree:thr=0.7 | cont_both | clvvol_aligned, trend240_aligned | S1_EOD | 435 | broad (1.00) |
| 25 | 3.38 | 13 | RET | RET:open_retz_cross:thr=1.5 | cont_long | on_aligned, trend60_aligned | S1_R3 | 338 | broad (0.83) |
| 26 | 3.36 | 1 | PATH | PATH:ols_t_cross:H=60,thr=5.0 | cont_both | on_range_high, vol_accelerating | S2_R3 | 236 | broad (0.67) |
| 27 | 3.36 | 3 | VOL | VOL:vol_accel_up:thr=1.0 | cont_long | volreg_high, vwap_aligned | S1_R3 | 309 | broad (0.80) |
| 28 | 3.36 | 2 | PERS | PERS:momentum_at_persistence_onset: | cont_both | open_aligned, trend240_aligned | S1_EOD | 762 | broad (1.00) |
| 29 | 3.34 | 21 | OPEN | OPEN:opening_move:X=5,thr=1.0 | cont_both | clvvol_aligned, jump_recent | S2_T120 | 498 | broad (1.00) |
| 30 | 3.31 | 1 | JUMP | JUMP:jump_then_smooth: | cont_both | on_aligned, trend240_aligned | S2_T120 | 247 | broad (0.80) |
| 31 | 3.30 | 1 | XMKT | XMKT:pers_disagree:thr=0.4 | cont_both | first_hour, volreg_low | S1_T120 | 278 | broad (1.00) |
| 32 | 3.28 | 3 | REOPEN | REOPEN:failed_breakout:N=240 | rev_both | trend60_aligned, vr_high | S1_R3 | 914 | broad (0.80) |
| 33 | 3.28 | 4 | XMKT | XMKT:pers_disagree:thr=0.4 | cont_both | first_hour, vr_high | S2_EOD | 222 | broad (1.00) |
| 34 | 3.27 | 2 | TECH | TECH:bollinger_break:thr=1.0 | rev_both | rvol_cum_rth_high, semi_aligned | S2_T120 | 452 | broad (0.80) |
| 35 | 3.26 | 7 | RET | RET:open_retz_cross:thr=2.0 | cont_long | clvvol_aligned, on_aligned | S2_T120 | 210 | broad (1.00) |
| 36 | 3.26 | 2 | OPEN | OPEN:opening_move:X=5,thr=0.5 | cont_both | es_confirms, opex_week | S1_R2 | 211 | broad (0.71) |
| 37 | 3.25 | 1 | RET | RET:open_retz_cross:thr=1.5 | cont_long | clvvol_aligned, on_aligned | S1_R3 | 232 | broad (0.83) |
| 38 | 3.25 | 3 | VWAP | VWAP:acceptance:N=10,anchor=rth | cont_both | trend240_aligned, vr_high | S2_T120 | 318 | broad (1.00) |
| 39 | 3.25 | 10 | OPEN | OPEN:overnight_return:X=15,thr=0.5 | cont_both | sgnvol_aligned, vwap_aligned | S1_T120 | 211 | broad (1.00) |
| 40 | 3.25 | 2 | XMKT | XMKT:vol_disagree:thr=0.7 | cont_both | jump_recent, trend240_aligned | S1_R2 | 257 | intermediate (0.50) |
| 41 | 3.22 | 1 | OPEN | OPEN:opening_move:X=1,thr=1.5 | cont_both | sgnvol_aligned, volreg_low | S2_T120 | 233 | broad (1.00) |
| 42 | 3.22 | 1 | PATH | PATH:clean_trend:H=30 | cont_both | rvol_cum_rth_high, vr_high | S1_EOD | 231 | broad (0.80) |
| 43 | 3.22 | 2 | JUMP | JUMP:jump_then_smooth: | cont_long | on_aligned, semi_aligned | S1_T60 | 202 | broad (0.80) |
| 44 | 3.21 | 33 | OPEN | OPEN:overnight_return:X=15,thr=0.5 | cont_long | vwap_aligned | S1_T60 | 227 | broad (1.00) |
| 45 | 3.21 | 3 | PATH | PATH:ols_t_cross:H=30,thr=3.0 | rev_long | open_aligned, range_top_for_long | S2_EOD | 722 | broad (0.86) |
| 46 | 3.21 | 6 | XMKT | XMKT:er_disagree:H=15,thr=0.4 | cont_both | corr_low, first_hour | S2_T60 | 311 | broad (1.00) |
| 47 | 3.19 | 18 | OPEN | OPEN:opening_move:X=30,thr=0.5 | cont_both | on_aligned, trend60_aligned | S2_T120 | 243 | broad (1.00) |
| 48 | 3.19 | 5 | RET | RET:trend_agree_full: | cont_long | er_high, sgnvol_aligned | S1_T120 | 206 | broad (0.80) |
| 49 | 3.19 | 3 | VOL | VOL:obv_cross:W=30,thr=0.2 | cont_long | trend240_aligned, vr_high | S2_EOD | 343 | broad (0.67) |
| 50 | 3.19 | 1 | VWAP | VWAP:acceptance:N=10,anchor=rth | cont_long | on_aligned, sgnvol_aligned | S1_EOD | 345 | broad (0.80) |
| 51 | 3.18 | 2 | DIST | DIST:semi_cross:W=30,thr=0.5 | cont_both | on_aligned, rvol_high | S2_T120 | 359 | intermediate (0.57) |
| 52 | 3.18 | 2 | CAL | CAL:time_of_day:sm=1079 | cont_both | on_aligned, trend240_aligned | S2_R2 | 232 | broad (0.67) |
| 53 | 3.17 | 1 | DIST | DIST:semi_cross:W=60,thr=0.5 | cont_both | corr_low, open_aligned | S2_R2 | 231 | broad (0.83) |
| 54 | 3.17 | 1 | RET | RET:open_retz_cross:thr=1.5 | cont_short | er_low, opex_week | S2_T60 | 367 | broad (0.71) |
| 55 | 3.16 | 16 | OPEN | OPEN:opening_move:X=5,thr=1.5 | cont_both | sgnvol_aligned, vwap_aligned | S2_EOD | 505 | broad (1.00) |
| 56 | 3.15 | 4 | JUMP | JUMP:jump_bar:thr=4.0 | cont_long | on_aligned, trend60_aligned | S1_R3 | 210 | broad (1.00) |
| 57 | 3.14 | 2 | TECH | TECH:rsi_extreme:hi=80,lo=20 | cont_long | sgnvol_aligned, trend240_aligned | S2_EOD | 462 | broad (1.00) |
| 58 | 3.13 | 2 | VOL | VOL:obv_cross:W=120,thr=0.2 | cont_long | on_aligned, trend240_aligned | S2_R2 | 296 | broad (1.00) |
| 59 | 3.13 | 1 | RET | RET:retz_cross:H=15,thr=2.5 | cont_both | er_low, on_range_high | S2_T60 | 330 | broad (0.67) |
| 60 | 3.13 | 1 | REOPEN | REOPEN:orb:X=15 | cont_long | first_hour, on_aligned | S1_T15 | 263 | broad (0.60) |
| 61 | 3.13 | 1 | TECH | TECH:dmi_cross_adx25: | cont_short | first_hour, sgnvol_aligned | S2_R3 | 337 | intermediate (0.50) |
| 62 | 3.13 | 1 | REOPEN | REOPEN:orb:X=15 | cont_long | on_aligned, open_aligned | S2_T120 | 224 | broad (0.83) |
| 63 | 3.12 | 1 | RET | RET:retz_cross:H=15,thr=2.0 | cont_both | monday, vr_high | S1_R3 | 285 | broad (0.75) |
| 64 | 3.12 | 2 | PATH | PATH:clean_trend:H=30 | cont_both | first_hour, semi_aligned | S1_EOD | 793 | broad (1.00) |
| 65 | 3.12 | 16 | RET | RET:retz_cross:H=30,thr=1.5 | cont_both | clvvol_aligned, corr_low | S1_T30 | 219 | broad (0.88) |
| 66 | 3.12 | 1 | VOL | VOL:rvol_cross_up:W=1,thr=3.0 | cont_long | on_aligned, open_aligned | S1_EOD | 273 | broad (0.86) |
| 67 | 3.11 | 1 | PERS | PERS:ac_neg_to_pos: | cont_long | jump_recent, semi_aligned | S1_R2 | 293 | broad (0.75) |
| 68 | 3.11 | 2 | RET | RET:retz_cross:H=5,thr=2.0 | cont_long | on_aligned, open_aligned | S1_R3 | 433 | broad (0.75) |
| 69 | 3.11 | 1 | XMKT | XMKT:er_disagree:H=15,thr=0.6 | cont_both | first_hour | S2_T120 | 291 | broad (1.00) |
| 70 | 3.10 | 1 | DIST | DIST:semi_cross:W=30,thr=0.7 | cont_both | es_confirms, trend60_aligned | S2_EOD | 1801 | broad (0.83) |
| 71 | 3.10 | 5 | TECH | TECH:cci_cross:thr=100.0 | rev_both | open_aligned, range_top_for_long | S2_R3 | 1563 | broad (0.80) |
| 72 | 3.10 | 2 | XMKT | XMKT:er_disagree:H=15,thr=0.4 | cont_both | jump_recent, monday | S2_T60 | 234 | broad (1.00) |
| 73 | 3.09 | 2 | TECH | TECH:keltner_break:thr=1.0 | cont_both | jump_recent, vr_high | S2_R3 | 367 | broad (0.75) |
| 74 | 3.09 | 1 | REOPEN | REOPEN:orb:X=30 | rev_both | er_low, on_range_low | S2_T120 | 245 | broad (1.00) |
| 75 | 3.09 | 1 | RET | RET:retz_cross:H=5,thr=2.0 | rev_both | er_low, on_rvol_high | S2_R3 | 689 | intermediate (0.50) |
| 76 | 3.09 | 1 | RET | RET:retz_cross:H=5,thr=1.5 | rev_long | range_top_for_long, semi_aligned | S2_R2 | 486 | intermediate (0.57) |
| 77 | 3.09 | 2 | RET | RET:retz_cross:H=60,thr=1.5 | cont_both | friday, rvol_high | S2_R3 | 248 | broad (1.00) |
| 78 | 3.09 | 1 | XMKT | XMKT:semi_disagree:thr=0.5 | cont_both | month_turn, range_top_for_long | S1_R3 | 203 | broad (0.75) |
| 79 | 3.08 | 2 | VOL | VOL:obv_cross:W=120,thr=0.2 | cont_long | es_confirms, on_aligned | S2_EOD | 280 | broad (1.00) |
| 80 | 3.08 | 1 | OPEN | OPEN:opening_move:X=5,thr=1.0 | cont_both | clvvol_aligned, jump_recent | S1_T30 | 498 | broad (0.89) |
| 81 | 3.08 | 2 | OPEN | OPEN:opening_move:X=3,thr=0.5 | cont_both | er_low, opex_week | S2_T60 | 228 | broad (0.88) |
| 82 | 3.07 | 4 | VWAP | VWAP:acceptance:N=10,anchor=rth | cont_long | on_aligned, trend240_aligned | S1_T120 | 327 | broad (1.00) |
| 83 | 3.07 | 1 | JUMP | JUMP:jump_bar:thr=4.0 | cont_long | monday, sgnvol_aligned | S1_T30 | 215 | broad (0.83) |
| 84 | 3.07 | 1 | VOL | VOL:rvol_cross_up:W=1,thr=2.0 | rev_both | er_low, trend60_aligned | S2_T120 | 2121 | broad (0.71) |
| 85 | 3.07 | 3 | VOL | VOL:obv_cross:W=120,thr=0.2 | cont_both | trend240_aligned, vr_high | S2_EOD | 397 | broad (1.00) |
| 86 | 3.06 | 13 | OPEN | OPEN:opening_move:X=5,thr=1.0 | cont_short | sgnvol_aligned, vwap_aligned | S2_EOD | 372 | broad (1.00) |
| 87 | 3.06 | 1 | PATH | PATH:er_cross:H=30,thr=0.5 | cont_long | rvol_high, semi_aligned | S2_R3 | 338 | intermediate (0.57) |
| 88 | 3.05 | 1 | RET | RET:retz_cross:H=15,thr=2.0 | cont_short | sgnvol_aligned, volreg_low | S2_T30 | 507 | intermediate (0.56) |
| 89 | 3.05 | 1 | OPEN | OPEN:opening_move:X=5,thr=0.5 | cont_both | jump_recent, monday | S1_T30 | 267 | broad (0.88) |
| 90 | 3.05 | 3 | PATH | PATH:er_cross:H=15,thr=0.7 | cont_both | on_against, range_top_for_long | S2_R3 | 346 | broad (1.00) |
| 91 | 3.05 | 1 | VOL | VOL:vol_accel_up:thr=1.0 | cont_long | friday, vwap_aligned | S2_R2 | 278 | broad (0.80) |
| 92 | 3.05 | 1 | REOPEN | REOPEN:orb:X=15 | cont_both | first_hour, on_aligned | S1_R2 | 422 | broad (0.60) |
| 93 | 3.05 | 2 | VOL | VOL:obv_cross:W=30,thr=0.35 | cont_short | clvvol_aligned, corr_low | S2_T30 | 212 | broad (0.71) |
| 94 | 3.05 | 1 | PATH | PATH:er_cross:H=15,thr=0.5 | cont_long | er_high, sgnvol_aligned | S2_T120 | 203 | broad (0.71) |
| 95 | 3.04 | 1 | OPEN | OPEN:opening_move:X=30,thr=0.5 | cont_both | on_aligned, range_top_for_long | S1_T30 | 211 | broad (0.75) |
| 96 | 3.04 | 1 | VOL | VOL:rvol_cross_up:W=5,thr=2.0 | rev_both | range_top_for_long, vol_accelerating | S2_R2 | 261 | intermediate (0.43) |
| 97 | 3.04 | 1 | RET | RET:open_retz_cross:thr=1.5 | cont_long | on_aligned, volreg_low | S2_T120 | 317 | broad (0.86) |
| 98 | 3.04 | 1 | JUMP | JUMP:jump_bar:thr=4.0 | cont_long | on_aligned, sgnvol_aligned | S1_EOD | 225 | broad (1.00) |
| 99 | 3.03 | 3 | PATH | PATH:er_cross:H=15,thr=0.7 | cont_short | friday, vwap_aligned | S2_R2 | 237 | broad (0.67) |
| 100 | 3.03 | 1 | RET | RET:open_retz_cross:thr=2.0 | cont_both | sgnvol_aligned, vr_high | S2_R3 | 483 | broad (1.00) |
| 101 | 3.03 | 2 | XMKT | XMKT:pers_disagree:thr=0.4 | cont_short | first_hour, open_aligned | S1_T120 | 238 | broad (1.00) |
| 102 | 3.03 | 1 | VOL | VOL:dirvol_cross:thr=1.2 | cont_long | first_hour, volreg_low | S2_EOD | 388 | broad (0.80) |
| 103 | 3.02 | 1 | XMKT | XMKT:semi_disagree:thr=0.5 | cont_both | on_aligned, range_top_for_long | S1_R3 | 203 | broad (0.75) |
| 104 | 3.02 | 7 | REOPEN | REOPEN:orb:X=30 | rev_both | er_low | S2_EOD | 1102 | broad (1.00) |
| 105 | 3.02 | 2 | VWAP | VWAP:dist_cross:anchor=glx,thr=3.0 | cont_long | sgnvol_aligned, volreg_low | S2_R3 | 495 | broad (0.80) |
| 106 | 3.02 | 1 | TECH | TECH:rsi_extreme:hi=80,lo=20 | cont_both | clvvol_aligned, volreg_low | S2_T30 | 527 | broad (0.80) |
| 107 | 3.02 | 1 | XMKT | XMKT:er_disagree:H=15,thr=0.4 | cont_both | first_hour, sgnvol_aligned | S2_T60 | 652 | broad (0.83) |
| 108 | 3.01 | 1 | VOL | VOL:sgnvol_cross:W=15,thr=0.5 | cont_both | first_hour, on_against | S2_T120 | 427 | intermediate (0.57) |
| 109 | 3.01 | 1 | VWAP | VWAP:dist_cross:anchor=glx,thr=3.0 | cont_both | midday, vol_accelerating | S2_R2 | 721 | broad (0.80) |
| 110 | 3.01 | 1 | RET | RET:retz_cross:H=30,thr=2.0 | cont_both | on_range_high, vol_accelerating | S2_R3 | 315 | broad (1.00) |
| 111 | 3.01 | 1 | XMKT | XMKT:vol_disagree:thr=0.7 | cont_both | first_hour, trend240_aligned | S2_R2 | 235 | broad (1.00) |
| 112 | 3.01 | 1 | REOPEN | REOPEN:orb:X=30 | cont_long | on_aligned, sgnvol_aligned | S1_R3 | 209 | broad (0.83) |
| 113 | 3.00 | 1 | VWAP | VWAP:dist_cross:anchor=glx,thr=1.5 | cont_long | jump_recent, on_aligned | S1_T120 | 200 | broad (0.83) |
| 114 | 3.00 | 2 | OPEN | OPEN:opening_move:X=5,thr=1.0 | cont_short | clvvol_aligned, vwap_aligned | S2_T60 | 323 | broad (0.89) |
