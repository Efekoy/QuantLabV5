# V4 VALIDATION report (2019-01-01 .. 2022-12-31; frozen candidates, unchanged)

The 114 DISCOVERY cluster representatives frozen in DISCOVERY_FREEZE (`e10e0c0d`) were run unchanged on the CONFIRMATION partition (warm-up: the last 130 DISCOVERY sessions; only trades from 2019-01-01 onward count). Survival rule: >= 40 trades, mean net > 0, t >= 1.5, PF >= 1.05, >= 2 of 4 years positive, and stress-cost net > 0. Net of the baseline cost.

**Survivors: 43 of 114** (search-adjusted evidence: V4_VALIDATION_NULL_REPORT.md).

Survivor families: {"OPEN": 6, "PATH": 5, "RET": 12, "PERS": 1, "JUMP": 2, "XMKT": 4, "VWAP": 3, "DIST": 2, "TECH": 3, "VOL": 1, "REOPEN": 4}

Survivor variants: {"cont_both": 23, "cont_long": 15, "rev_long": 2, "rev_both": 2, "cont_short": 1}

POST-HOC (not used for any decision): the drift/time-of-day control compares each trade with the average outcome of the same exit and direction entered at the same clock minute on every validation session. Survivors' excess-over-baseline t: median 2.00; 38 of 43 are >= 1.5. The validation performance is therefore mostly NOT explained by NQ drift or by time-of-day bias alone.

| id | family | trigger | variant | filters | exit | trades | net pts | t | PF | yrs+ | stress net | survives | drift-excess t (post-hoc) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q4-60857891da97d59c25f0f86c | VWAP | VWAP:dist_cross:anchor=glx,thr=3.0 | cont_long | sgnvol_aligned, volreg_low | S2_R3 | 317 | 3305.4 | 3.47 | 1.69 | 3 | 3115.2 | YES | 3.04 |
| Q4-14478681d690cde198df1979 | RET | RET:retz_cross:H=15,thr=2.0 | cont_short | sgnvol_aligned, volreg_low | S2_T30 | 346 | 2398.3 | 3.45 | 1.72 | 3 | 2190.7 | YES | 3.89 |
| Q4-9757cb9ee92c11b68d2ad60b | DIST | DIST:semi_cross:W=30,thr=0.7 | cont_both | es_confirms, trend60_aligned | S2_EOD | 921 | 9111.8 | 3.29 | 1.36 | 3 | 8559.2 | YES | 2.98 |
| Q4-40aae8a2c827fb779e4dd7b9 | RET | RET:open_retz_cross:thr=2.0 | cont_both | semi_aligned, volreg_low | S2_R3 | 418 | 5335.4 | 3.22 | 1.52 | 4 | 5084.6 | YES | 2.84 |
| Q4-0175e8eb4fea121c87655234 | RET | RET:open_retz_cross:thr=1.5 | cont_long | on_aligned, volreg_low | S2_T120 | 190 | 2006.0 | 3.02 | 1.81 | 3 | 1892.0 | YES | 2.98 |
| Q4-c790712e4f51f6f4268b0033 | XMKT | XMKT:er_disagree:H=15,thr=0.4 | cont_both | corr_low, first_hour | S2_T60 | 147 | 1804.8 | 2.99 | 1.94 | 3 | 1716.6 | YES | 3.17 |
| Q4-1dbad4cded1e659fd193e15c | TECH | TECH:cci_cross:thr=100.0 | rev_both | open_aligned, range_top_for_long | S2_R3 | 784 | 6250.0 | 2.87 | 1.32 | 3 | 5779.6 | YES | 2.65 |
| Q4-326df064b2c927151d6fc24c | RET | RET:trend_agree_full: | cont_both | er_high, trend240_aligned | S2_R3 | 190 | 3308.8 | 2.82 | 1.80 | 3 | 3194.8 | YES | 2.68 |
| Q4-efad812f7fec4376c24b34f6 | TECH | TECH:rsi_extreme:hi=80,lo=20 | cont_both | clvvol_aligned, volreg_low | S2_T30 | 347 | 1957.8 | 2.79 | 1.56 | 4 | 1749.6 | YES | 3.14 |
| Q4-db0a91353062ca891caf8eda | XMKT | XMKT:pers_disagree:thr=0.4 | cont_both | first_hour, volreg_low | S1_T120 | 173 | 2274.2 | 2.76 | 1.79 | 2 | 2170.4 | YES | 2.77 |
| Q4-4c2674436a7c2e911ab1ce4c | PATH | PATH:er_cross:H=30,thr=0.5 | cont_long | rvol_high, semi_aligned | S2_R3 | 102 | 1836.3 | 2.68 | 2.07 | 3 | 1775.1 | YES | 2.47 |
| Q4-47c1bbe9fc1427e364d86bf5 | XMKT | XMKT:er_disagree:H=15,thr=0.6 | cont_both | first_hour | S2_T120 | 205 | 2556.5 | 2.49 | 1.60 | 3 | 2433.5 | YES | 2.51 |
| Q4-8f2ddfeac6111992489eb2e1 | RET | RET:retz_cross:H=30,thr=1.5 | cont_both | corr_low, open_aligned | S2_R2 | 92 | 1434.8 | 2.47 | 1.93 | 2 | 1379.6 | YES | 2.31 |
| Q4-d24243de4d067e4f945b7e1b | RET | RET:open_retz_cross:thr=2.0 | cont_both | sgnvol_aligned, vr_high | S2_R3 | 340 | 4511.5 | 2.47 | 1.43 | 4 | 4307.5 | YES | 2.25 |
| Q4-158e68845ba80d9490e4b658 | PATH | PATH:er_cross:H=15,thr=0.5 | cont_long | er_high, sgnvol_aligned | S2_T120 | 122 | 1475.8 | 2.41 | 1.93 | 4 | 1402.6 | YES | 2.44 |
| Q4-ec4109445a1e4b4ef7b4805c | OPEN | OPEN:opening_move:X=5,thr=1.0 | cont_both | clvvol_aligned, jump_recent | S1_T30 | 277 | 1852.8 | 2.41 | 1.45 | 4 | 1686.6 | YES | 2.84 |
| Q4-39346c8ab50d60a228f53624 | TECH | TECH:rsi_extreme:hi=80,lo=20 | cont_long | sgnvol_aligned, trend240_aligned | S2_EOD | 230 | 3229.3 | 2.40 | 1.64 | 4 | 3091.3 | YES | 2.04 |
| Q4-e27abc9c40a95808b286aaf8 | PATH | PATH:er_cross:H=15,thr=0.5 | cont_both | volreg_low, vr_high | S2_EOD | 425 | 3481.3 | 2.30 | 1.35 | 3 | 3226.3 | YES | 1.99 |
| Q4-ae7eecdc86608a558045b27d | RET | RET:open_retz_cross:thr=1.5 | cont_long | on_aligned, trend60_aligned | S1_R3 | 188 | 1603.4 | 2.12 | 1.48 | 4 | 1490.6 | YES | 1.95 |
| Q4-d3ae0d688762e49eeec25e7a | JUMP | JUMP:jump_then_smooth: | cont_both | on_aligned, trend240_aligned | S2_T120 | 106 | 1542.1 | 2.04 | 1.78 | 4 | 1478.5 | YES | 2.08 |
| Q4-ba1e53e93129e12bb7d777b0 | RET | RET:open_retz_cross:thr=1.5 | cont_long | clvvol_aligned, on_aligned | S1_R3 | 146 | 1342.8 | 2.02 | 1.53 | 4 | 1255.2 | YES | 1.96 |
| Q4-0d7c8bc571764e5378bc4112 | OPEN | OPEN:opening_move:X=30,thr=0.5 | cont_both | on_aligned, sgnvol_aligned | S1_T60 | 112 | 1095.1 | 2.01 | 1.63 | 4 | 1027.9 | YES | 2.15 |
| Q4-653fc4dadbcc80f6ed658dc3 | REOPEN | REOPEN:orb:X=15 | cont_both | first_hour, on_aligned | S1_R2 | 227 | 2080.1 | 1.99 | 1.36 | 4 | 1943.9 | YES | 2.00 |
| Q4-f6922976879d5e719f7e99c8 | PATH | PATH:ols_t_cross:H=30,thr=3.0 | rev_long | open_aligned, range_top_for_long | S2_EOD | 368 | 2433.6 | 1.98 | 1.34 | 3 | 2212.8 | YES | 1.44 |
| Q4-b5e4721bee9e34f41277388e | VWAP | VWAP:acceptance:N=10,anchor=rth | cont_long | on_aligned, sgnvol_aligned | S1_EOD | 190 | 1643.5 | 1.94 | 1.49 | 3 | 1529.5 | YES | 1.49 |
| Q4-dc5c4f1370da762131955beb | DIST | DIST:semi_cross:W=30,thr=0.5 | cont_both | on_aligned, rvol_high | S2_T120 | 128 | 1584.2 | 1.93 | 1.59 | 4 | 1507.4 | YES | 2.00 |
| Q4-d525041d0b7efeb68425a975 | OPEN | OPEN:opening_move:X=30,thr=0.5 | cont_both | on_aligned, range_top_for_long | S1_T30 | 114 | 805.0 | 1.92 | 1.62 | 3 | 736.6 | YES | 2.20 |
| Q4-b2319ed6a27466f8ef78245e | REOPEN | REOPEN:orb:X=30 | cont_long | on_aligned, sgnvol_aligned | S1_R3 | 107 | 1149.1 | 1.91 | 1.60 | 3 | 1084.9 | YES | 1.71 |
| Q4-b6a51de64a0447c802114a4a | RET | RET:retz_cross:H=5,thr=1.5 | rev_long | range_top_for_long, semi_aligned | S2_R2 | 253 | 2010.4 | 1.88 | 1.37 | 4 | 1858.6 | YES | 1.69 |
| Q4-744a501fbc00d68e9d8e0ad5 | OPEN | OPEN:opening_move:X=5,thr=1.0 | cont_both | clvvol_aligned, jump_recent | S2_T120 | 277 | 2505.4 | 1.88 | 1.34 | 4 | 2339.2 | YES | 1.87 |
| Q4-edbc44bde03d4bba60783c4b | RET | RET:trend_agree_full: | cont_long | er_high, sgnvol_aligned | S1_T120 | 127 | 1088.3 | 1.87 | 1.62 | 3 | 1012.1 | YES | 1.86 |
| Q4-a6afc475d401ac496658b786 | PERS | PERS:momentum_at_persistence_onset: | cont_both | open_aligned, trend240_aligned | S1_EOD | 497 | 2748.1 | 1.85 | 1.27 | 4 | 2449.9 | YES | 1.63 |
| Q4-98cb83b1751ac82049ea446c | RET | RET:retz_cross:H=30,thr=1.5 | cont_both | clvvol_aligned, corr_low | S1_T30 | 69 | 409.2 | 1.83 | 1.81 | 2 | 367.8 | YES | 2.02 |
| Q4-96fe2d187f77585a991b6695 | RET | RET:retz_cross:H=30,thr=1.5 | cont_both | corr_low, range_top_for_long | S1_T60 | 104 | 696.2 | 1.79 | 1.64 | 2 | 633.8 | YES | 1.92 |
| Q4-f0e425918ed9c2e32b39322b | OPEN | OPEN:opening_move:X=30,thr=0.5 | cont_both | on_aligned, trend60_aligned | S2_T120 | 130 | 1547.5 | 1.77 | 1.52 | 3 | 1469.5 | YES | 1.90 |
| Q4-941bd1394023b222a84fb0ab | PATH | PATH:er_cross:H=15,thr=0.5 | cont_both | semi_aligned, vr_high | S2_R3 | 599 | 3839.7 | 1.74 | 1.21 | 3 | 3480.3 | YES | 1.55 |
| Q4-3315e536ae22ccdb042483ab | REOPEN | REOPEN:orb:X=15 | cont_long | on_aligned, open_aligned | S2_T120 | 129 | 1154.7 | 1.70 | 1.46 | 3 | 1077.3 | YES | 1.75 |
| Q4-d24a71f3f98b73539e298d5d | XMKT | XMKT:pers_disagree:thr=0.4 | cont_both | first_hour, vr_high | S2_EOD | 126 | 2357.8 | 1.69 | 1.52 | 3 | 2282.2 | YES | 1.58 |
| Q4-e61bf49122da50003c554a54 | VOL | VOL:obv_cross:W=120,thr=0.2 | cont_long | on_aligned, trend240_aligned | S2_R2 | 134 | 1254.9 | 1.64 | 1.45 | 3 | 1174.5 | YES | 1.41 |
| Q4-6d8c3050c62a8e590ae96486 | OPEN | OPEN:overnight_return:X=15,thr=0.5 | cont_long | vwap_aligned | S1_T60 | 128 | 830.9 | 1.63 | 1.43 | 4 | 754.1 | YES | 1.60 |
| Q4-969b7274b473016b12b50cda | REOPEN | REOPEN:orb:X=30 | rev_both | er_low | S2_EOD | 471 | 4121.3 | 1.62 | 1.24 | 3 | 3838.7 | YES | 1.45 |
| Q4-adf881cbaba224976c11c316 | VWAP | VWAP:dist_cross:anchor=glx,thr=1.5 | cont_long | jump_recent, on_aligned | S1_T120 | 124 | 928.5 | 1.58 | 1.46 | 4 | 854.1 | YES | 1.44 |
| Q4-01e36ea2e3f5fba896554d38 | JUMP | JUMP:jump_then_smooth: | cont_long | on_aligned, semi_aligned | S1_T60 | 96 | 620.5 | 1.56 | 1.51 | 2 | 562.9 | YES | 1.58 |
| Q4-b1b297a48062469e7759a1a0 | DIST | DIST:semi_cross:W=60,thr=0.5 | cont_both | corr_low, open_aligned | S2_R2 | 95 | 926.0 | 1.49 | 1.45 | 3 | 869.0 | no | 1.32 |
| Q4-6993194deda5ddf662374f3d | OPEN | OPEN:opening_move:X=5,thr=0.5 | cont_both | jump_recent, monday | S1_T30 | 134 | 796.7 | 1.48 | 1.38 | 4 | 716.3 | no | 1.79 |
| Q4-ff02aca17069416636ebb615 | VOL | VOL:vol_accel_up:thr=1.0 | cont_long | friday, vwap_aligned | S2_R2 | 48 | 418.9 | 1.48 | 1.75 | 3 | 390.1 | no | 1.25 |
| Q4-18d816e18d093ab9040237c3 | OPEN | OPEN:opening_move:X=5,thr=1.5 | cont_both | sgnvol_aligned, vwap_aligned | S2_EOD | 320 | 3056.8 | 1.48 | 1.25 | 4 | 2864.8 | no | 1.22 |
| Q4-5b42dbb9d7f1688742c8cf81 | OPEN | OPEN:opening_move:X=1,thr=1.5 | cont_both | sgnvol_aligned, volreg_low | S2_T120 | 127 | 1301.1 | 1.46 | 1.40 | 3 | 1224.9 | no | 1.56 |
| Q4-457727d4b81cc849ae88058b | REOPEN | REOPEN:orb:X=15 | cont_both | on_aligned, trend240_aligned | S1_EOD | 181 | 1715.0 | 1.44 | 1.38 | 3 | 1606.4 | no | 1.28 |
| Q4-953bf6bb49935bef8d91e4c3 | PATH | PATH:ols_t_cross:H=60,thr=5.0 | cont_both | on_range_high, vol_accelerating | S2_R3 | 100 | 1030.8 | 1.44 | 1.53 | 4 | 970.8 | no | 1.40 |
| Q4-bb40618ba9e67857359db485 | VOL | VOL:obv_cross:W=30,thr=0.2 | cont_long | trend240_aligned, vr_high | S2_EOD | 281 | 1858.3 | 1.43 | 1.26 | 4 | 1689.7 | no | 1.00 |
| Q4-facbbdf380b038425cb544f4 | RET | RET:open_retz_cross:thr=2.0 | cont_long | on_aligned, range_top_for_long | S2_R3 | 105 | 1104.0 | 1.42 | 1.42 | 3 | 1041.0 | no | 1.11 |
| Q4-123add6e35a6633b7cd00bdf | VOL | VOL:dirvol_cross:thr=1.2 | cont_long | first_hour, volreg_low | S2_EOD | 161 | 1722.6 | 1.41 | 1.35 | 3 | 1626.0 | no | 1.04 |
| Q4-3eb4f7d3d860aba81f33b773 | PATH | PATH:r2_cross:H=60,thr=0.85 | cont_long | on_aligned, open_aligned | S1_R3 | 142 | 798.8 | 1.41 | 1.38 | 2 | 713.6 | no | 1.17 |
| Q4-2d8d674b2e347c500c9cab0b | XMKT | XMKT:pers_disagree:thr=0.4 | cont_short | first_hour, open_aligned | S1_T120 | 123 | 1115.9 | 1.34 | 1.40 | 3 | 1042.1 | no | 1.45 |
| Q4-877410e3d2a44f774b790a6b | OPEN | OPEN:overnight_return:X=15,thr=0.5 | cont_both | sgnvol_aligned, vwap_aligned | S1_T120 | 126 | 958.8 | 1.32 | 1.37 | 3 | 883.2 | no | 1.40 |
| Q4-5fc689ecd97c279975877646 | REOPEN | REOPEN:orb:X=15 | cont_long | first_hour, on_aligned | S1_T15 | 130 | 415.7 | 1.32 | 1.35 | 4 | 337.7 | no | 1.38 |
| Q4-15cbee7fbdcac8a8b503ac41 | RET | RET:retz_cross:H=5,thr=2.0 | cont_both | corr_low, sgnvol_aligned | S2_R3 | 70 | 838.8 | 1.23 | 1.50 | 3 | 796.8 | no | 1.10 |
| Q4-b2993b942e335774c73c677e | VOL | VOL:obv_cross:W=30,thr=0.35 | cont_short | clvvol_aligned, corr_low | S2_T30 | 37 | 346.1 | 1.23 | 1.75 | 3 | 323.9 | no | 1.32 |
| Q4-0ecb4fdb6faf99373826d29f | VOL | VOL:obv_cross:W=120,thr=0.2 | cont_both | trend240_aligned, vr_high | S2_EOD | 273 | 1761.1 | 1.22 | 1.24 | 2 | 1597.3 | no | 1.02 |
| Q4-0f0529deddc99fe0ff0441e3 | XMKT | XMKT:vol_disagree:thr=0.7 | cont_long | on_aligned, open_aligned | S1_R3 | 97 | 508.1 | 1.12 | 1.35 | 4 | 449.9 | no | 1.18 |
| Q4-d025af7d860fd5c9c75cfb66 | PATH | PATH:clean_trend:H=30 | cont_both | first_hour, semi_aligned | S1_EOD | 417 | 1761.9 | 1.08 | 1.16 | 3 | 1511.7 | no | 0.69 |
| Q4-f9d4d6306d0cab7238d62c0a | PATH | PATH:er_cross:H=15,thr=0.7 | cont_both | on_against, range_top_for_long | S2_R3 | 204 | 1405.9 | 1.08 | 1.23 | 4 | 1283.5 | no | 1.00 |
| Q4-b46aa39ae649e7e18eda443b | REOPEN | REOPEN:orb:X=15 | cont_long | on_aligned, sgnvol_aligned | S2_T30 | 115 | 422.0 | 1.04 | 1.33 | 3 | 353.0 | no | 1.13 |
| Q4-1421443bd3eaab404db684de | PATH | PATH:clean_trend:H=30 | cont_both | jump_recent, vr_high | S1_EOD | 178 | 938.4 | 1.01 | 1.23 | 2 | 831.6 | no | 0.82 |
| Q4-d9f436b5061953d23fbc5638 | VOL | VOL:vol_accel_up:thr=1.0 | cont_long | on_aligned, open_aligned | S1_R3 | 61 | 279.3 | 0.98 | 1.44 | 3 | 242.7 | no | 0.92 |
| Q4-6b3e4586071b0d201962ae28 | REOPEN | REOPEN:failed_breakout:N=240 | rev_both | trend60_aligned, vr_high | S1_R3 | 682 | 1555.4 | 0.98 | 1.10 | 3 | 1146.2 | no | 0.93 |
| Q4-9cb4aa609cb5349de577d75c | XMKT | XMKT:vol_disagree:thr=0.7 | cont_both | clvvol_aligned, trend240_aligned | S1_EOD | 144 | 814.0 | 0.98 | 1.32 | 3 | 727.6 | no | 0.88 |
| Q4-e94cc0b285dfae530450773d | VOL | VOL:obv_cross:W=120,thr=0.2 | cont_long | es_confirms, on_aligned | S2_EOD | 144 | 812.9 | 0.96 | 1.24 | 2 | 726.5 | no | 0.56 |
| Q4-05ca7c62c899a9a919564827 | REOPEN | REOPEN:orb:X=15 | cont_both | on_aligned, trend240_aligned | S1_T60 | 181 | 614.8 | 0.90 | 1.20 | 2 | 506.2 | no | 1.03 |
| Q4-7b95befaec01ed5a5288ec6f | RET | RET:open_retz_cross:thr=2.0 | cont_long | clvvol_aligned, on_aligned | S2_T120 | 124 | 518.2 | 0.88 | 1.23 | 2 | 443.8 | no | 0.89 |
| Q4-583856a0f51a21313291c7a4 | XMKT | XMKT:semi_disagree:thr=0.5 | cont_both | month_turn, range_top_for_long | S1_R3 | 95 | 414.3 | 0.86 | 1.27 | 2 | 357.3 | no | 0.86 |
| Q4-77ae4f4378c323eeaa4bdb4b | VWAP | VWAP:acceptance:N=10,anchor=rth | cont_long | on_aligned, trend240_aligned | S1_T120 | 181 | 535.3 | 0.85 | 1.18 | 3 | 426.7 | no | 0.74 |
| Q4-47347460ca85eb73d6ec3411 | PERS | PERS:momentum_at_persistence_onset: | cont_short | first_hour, range_top_for_long | S1_EOD | 124 | 899.9 | 0.84 | 1.25 | 3 | 825.5 | no | 0.84 |
| Q4-963e95351d8df33ea3cb4e32 | RET | RET:retz_cross:H=5,thr=2.0 | rev_both | er_low, on_rvol_high | S2_R3 | 315 | 1655.8 | 0.82 | 1.13 | 1 | 1466.8 | no | 0.67 |
| Q4-1d03003236e546d3fd060f93 | VOL | VOL:vol_accel_up:thr=1.0 | cont_long | volreg_high, vwap_aligned | S1_R3 | 43 | 255.2 | 0.82 | 1.39 | 2 | 229.4 | no | 0.76 |
| Q4-a136b1bc883820d8c88d5408 | RET | RET:retz_cross:H=30,thr=2.0 | cont_both | on_range_high, vol_accelerating | S2_R3 | 173 | 838.9 | 0.81 | 1.18 | 2 | 735.1 | no | 0.81 |
| Q4-9108c4facba8a37017f052ff | VWAP | VWAP:dist_cross:anchor=glx,thr=3.0 | cont_both | midday, vol_accelerating | S2_R2 | 280 | 862.3 | 0.79 | 1.13 | 2 | 694.3 | no | 0.93 |
| Q4-1086f774b0444aa198bbf6ff | VOL | VOL:dirvol_cross:thr=0.7 | cont_long | on_aligned, trend240_aligned | S2_R3 | 191 | 751.6 | 0.76 | 1.16 | 2 | 637.0 | no | 0.42 |
| Q4-833bd8ca820cc4c9ec8ab51c | JUMP | JUMP:jump_bar:thr=4.0 | cont_long | monday, sgnvol_aligned | S1_T30 | 112 | 280.6 | 0.70 | 1.18 | 3 | 213.4 | no | 1.18 |
| Q4-a2ca2bb6b468f3caf67fef94 | XMKT | XMKT:vol_disagree:thr=0.7 | cont_both | first_hour, trend240_aligned | S2_R2 | 102 | 670.1 | 0.64 | 1.18 | 3 | 608.9 | no | 0.52 |
| Q4-f1b412237a5ee747df3a86f4 | JUMP | JUMP:jump_then_smooth: | cont_long | on_aligned, vwap_aligned | S2_T120 | 108 | 354.9 | 0.63 | 1.18 | 2 | 290.1 | no | 0.56 |
| Q4-eaace38d44dda1ca502bb86e | PATH | PATH:r2_cross:H=30,thr=0.7 | cont_both | on_aligned, trend240_aligned | S1_T120 | 583 | 783.4 | 0.62 | 1.07 | 3 | 433.6 | no | 0.80 |
| Q4-fdba0dd21d7483880ae6e68a | XMKT | XMKT:corr_breakdown:thr=0.5 | cont_both | first_hour | S2_T120 | 110 | 347.8 | 0.58 | 1.15 | 1 | 281.8 | no | 0.61 |
| Q4-ff2d771aa5c8b47bbdd5dc29 | PATH | PATH:er_cross:H=15,thr=0.7 | cont_short | friday, vwap_aligned | S2_R2 | 136 | 565.8 | 0.52 | 1.13 | 2 | 484.2 | no | 0.62 |
| Q4-f24dd456af801cca1707ccc8 | XMKT | XMKT:er_disagree:H=15,thr=0.4 | cont_both | jump_recent, monday | S2_T60 | 122 | 299.9 | 0.48 | 1.13 | 3 | 226.7 | no | 0.59 |
| Q4-80f1346153ffa83260ea7e50 | TECH | TECH:keltner_break:thr=1.0 | cont_both | jump_recent, vr_high | S2_R3 | 251 | 734.1 | 0.45 | 1.08 | 2 | 583.5 | no | 0.29 |
| Q4-fb020a119dc1ec51428f45d3 | OPEN | OPEN:opening_move:X=5,thr=1.0 | cont_short | sgnvol_aligned, vwap_aligned | S2_EOD | 206 | 689.6 | 0.43 | 1.08 | 2 | 566.0 | no | 0.62 |
| Q4-0ae9f714ba9a20b246e79a65 | TECH | TECH:bollinger_break:thr=1.0 | rev_both | rvol_cum_rth_high, semi_aligned | S2_T120 | 179 | 395.2 | 0.40 | 1.09 | 3 | 287.8 | no | 0.42 |
| Q4-fa7316acbbe8ea12eccbb75d | RET | RET:retz_cross:H=15,thr=2.0 | cont_both | monday, vr_high | S1_R3 | 190 | 272.2 | 0.35 | 1.06 | 3 | 158.2 | no | 0.33 |
| Q4-d7a5c01907bca0b77449a3ac | VWAP | VWAP:acceptance:N=10,anchor=rth | cont_both | trend240_aligned, vr_high | S2_T120 | 272 | 384.6 | 0.35 | 1.06 | 2 | 221.4 | no | 0.40 |
| Q4-877cd985cb8f83f6a405b628 | CAL | CAL:time_of_day:sm=1079 | cont_both | on_aligned, trend240_aligned | S2_R2 | 116 | 156.8 | 0.28 | 1.07 | 2 | 87.2 | no | 0.45 |
| Q4-57e9ee7d0626477f7e7436f1 | JUMP | JUMP:jump_bar:thr=4.0 | cont_long | on_aligned, sgnvol_aligned | S1_EOD | 110 | 92.2 | 0.16 | 1.04 | 1 | 26.2 | no | 0.06 |
| Q4-a5ae2d96e127e12f8a7fefbd | RET | RET:retz_cross:H=60,thr=1.5 | cont_both | friday, rvol_high | S2_R3 | 112 | 123.1 | 0.12 | 1.03 | 2 | 55.9 | no | 0.14 |
| Q4-9ecd9fceb0ee4349a2b9ce33 | TECH | TECH:dmi_cross_adx25: | cont_short | first_hour, sgnvol_aligned | S2_R3 | 125 | 146.3 | 0.11 | 1.03 | 2 | 71.3 | no | 0.09 |
| Q4-0a6ddc3e70edb76b51eb8daa | JUMP | JUMP:jump_bar:thr=4.0 | cont_long | on_aligned, trend60_aligned | S1_R3 | 109 | 50.4 | 0.09 | 1.02 | 2 | -15.0 | no | 0.15 |
| Q4-ac847597959a9d34db9750d4 | VOL | VOL:rvol_cross_up:W=1,thr=2.0 | rev_both | er_low, trend60_aligned | S2_T120 | 738 | 134.7 | 0.07 | 1.01 | 2 | -308.1 | no | 0.19 |
| Q4-d1376634046213f4668e83d8 | PATH | PATH:clean_trend:H=30 | cont_short | vr_high, vwap_aligned | S1_EOD | 271 | 41.8 | 0.03 | 1.01 | 2 | -120.8 | no | 0.06 |
| Q4-4ef4f88aa5b6a59fcf14e97a | XMKT | XMKT:vol_disagree:thr=0.7 | cont_both | jump_recent, trend240_aligned | S1_R2 | 72 | 13.1 | 0.03 | 1.01 | 2 | -30.1 | no | 0.17 |
| Q4-118dbe4e8970aa86c5879e73 | XMKT | XMKT:er_disagree:H=15,thr=0.4 | cont_both | first_hour, sgnvol_aligned | S2_T60 | 319 | 3.4 | 0.00 | 1.00 | 1 | -188.0 | no | 0.24 |
| Q4-308e128ade2b7cb36519a890 | PATH | PATH:clean_trend:H=30 | cont_both | rvol_cum_rth_high, vr_high | S1_EOD | 107 | 0.6 | 0.00 | 1.00 | 2 | -63.6 | no | -0.17 |
| Q4-228e91d30bfd0f702af16440 | OPEN | OPEN:opening_move:X=5,thr=1.5 | cont_short | sgnvol_aligned | S2_T120 | 155 | -67.2 | -0.06 | 0.99 | 2 | -160.2 | no | 0.08 |
| Q4-75ff43364a5bcb7e06bcda80 | PERS | PERS:ac_neg_to_pos: | cont_long | jump_recent, semi_aligned | S1_R2 | 141 | -52.7 | -0.08 | 0.98 | 2 | -137.3 | no | -0.13 |
| Q4-70a36093565549dd876c3247 | RET | RET:open_retz_cross:thr=1.5 | cont_short | er_low, opex_week | S2_T60 | 200 | -197.7 | -0.29 | 0.95 | 1 | -317.7 | no | -0.01 |
| Q4-9f259773a69a9ad37c6f9513 | RET | RET:retz_cross:H=5,thr=2.0 | cont_long | on_aligned, open_aligned | S1_R3 | 246 | -359.0 | -0.47 | 0.93 | 1 | -506.6 | no | -0.70 |
| Q4-ea7c79b88c3ec3687cdc160e | VOL | VOL:sgnvol_cross:W=15,thr=0.5 | cont_both | first_hour, on_against | S2_T120 | 245 | -596.0 | -0.48 | 0.92 | 2 | -743.0 | no | -0.40 |
| Q4-8fe28f34b668202da8ab310d | RET | RET:retz_cross:H=15,thr=2.5 | cont_both | er_low, on_range_high | S2_T60 | 332 | -704.6 | -0.57 | 0.92 | 2 | -903.9 | no | -0.43 |
| Q4-1c82052d368c6dba61f04c2f | VOL | VOL:rvol_cross_up:W=1,thr=3.0 | cont_long | on_aligned, open_aligned | S1_EOD | 89 | -271.1 | -0.71 | 0.82 | 1 | -324.5 | no | -0.97 |
| Q4-6cefbd8b62cce2b45c298c6d | VOL | VOL:rvol_cross_up:W=5,thr=2.0 | rev_both | range_top_for_long, vol_accelerating | S2_R2 | 46 | -333.9 | -0.79 | 0.74 | 1 | -361.5 | no | -0.77 |
| Q4-e4d85d5b22fb63158ec99aca | OPEN | OPEN:opening_move:X=5,thr=1.0 | cont_short | clvvol_aligned, vwap_aligned | S2_T60 | 156 | -709.7 | -0.84 | 0.84 | 1 | -803.3 | no | -0.44 |
| Q4-9ad36407ce5bad937fe241f6 | REOPEN | REOPEN:orb:X=30 | rev_both | er_low, on_range_low | S2_T120 | 43 | -350.8 | -0.96 | 0.68 | 1 | -376.6 | no | -0.88 |
| Q4-054af6f446b3be82ed591fec | XMKT | XMKT:semi_disagree:thr=0.5 | cont_both | on_aligned, range_top_for_long | S1_R3 | 116 | -495.4 | -0.99 | 0.78 | 1 | -565.0 | no | -0.96 |
| Q4-0ac1e237fd43709851f97e21 | OPEN | OPEN:opening_move:X=5,thr=0.5 | cont_both | es_confirms, opex_week | S1_R2 | 89 | -535.8 | -1.07 | 0.77 | 1 | -589.2 | no | -1.00 |
| Q4-de6865f9bc5dab004abc3f2a | OPEN | OPEN:opening_move:X=3,thr=0.5 | cont_both | er_low, opex_week | S2_T60 | 95 | -814.0 | -1.33 | 0.71 | 2 | -871.0 | no | -1.26 |
