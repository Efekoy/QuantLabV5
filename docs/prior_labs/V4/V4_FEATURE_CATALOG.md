# V4 feature catalog

Library `featurelib_v4.0_2026-09-23` (`quantlab4/v4/featurelib.py`). Every feature is causal: its value at bar t uses bars <= t only (information time = bar close). This is verified automatically by `tests/test_v4_pipeline.py`, which rewrites the future and requires every feature, trigger, filter and symbol before the cut to stay bit-identical. An injected leak is caught.

Conventions: *group* = one session x one contract segment. Unless stated, lookbacks never cross a session or a roll. `sig1` = per-minute log-return scale (geometric mean of the 20-session time-of-day expected r^2 and the last-30-bar mean r^2). Volume features are NaN inside the cleaning-v1 roll window. Time-of-day baselines use only EARLIER sessions. VWAP is a BAR-BASED approximation (typical price (h+l+c)/3 x bar volume), not transaction-level VWAP.

**208 features, 223 triggers, 39 filters, 7 symbolic code sets, 102 ML signal sets.**

## Features

| name | family | columns | instruments | lookback | reset | params |
|---|---|---|---|---|---|---|
| `sig1` | BASE | c | NQ | 30 | across sessions (earlier only) | {"tod_sessions": 20, "recent_bars": 30} |
| `stop_scale` | BASE | h,l,c | NQ | 30 | across sessions (earlier only) | {} |
| `retz_1` | RET | c | NQ | 1 | session+roll | {"H": 1} |
| `retz_5` | RET | c | NQ | 5 | session+roll | {"H": 5} |
| `retz_15` | RET | c | NQ | 15 | session+roll | {"H": 15} |
| `retz_30` | RET | c | NQ | 30 | session+roll | {"H": 30} |
| `retz_60` | RET | c | NQ | 60 | session+roll | {"H": 60} |
| `retz_120` | RET | c | NQ | 120 | session+roll | {"H": 120} |
| `retz_240` | RET | c | NQ | 240 | session+roll | {"H": 240} |
| `dsma_15` | RET | c | NQ | 15 | session+roll | {"H": 15} |
| `dsma_60` | RET | c | NQ | 60 | session+roll | {"H": 60} |
| `dsma_240` | RET | c | NQ | 240 | session+roll | {"H": 240} |
| `pos_range_15` | RET | h,l,c | NQ | 15 | session+roll | {"H": 15} |
| `pos_range_60` | RET | h,l,c | NQ | 60 | session+roll | {"H": 60} |
| `pos_range_240` | RET | h,l,c | NQ | 240 | session+roll | {"H": 240} |
| `open_retz` | RET | o,c | NQ | 390 | session+roll | {"anchor": "09:30 open"} |
| `glx_retz` | RET | o,c | NQ | 1380 | session+roll | {"anchor": "session open 18:00"} |
| `trend_agree` | RET | c | NQ | 240 | session+roll | {"H": [5, 15, 60, 240]} |
| `gapz` | RET | c | NQ | 1380 | prior session close | {"ref": "prior session last RTH close"} |
| `lrvol_1_k20` | VOL | v | NQ | 1 | window in session; baseline previous 20 sessions (roll window excluded) | {"W": 1, "K": 20} |
| `lrvol_3_k20` | VOL | v | NQ | 3 | window in session; baseline previous 20 sessions (roll window excluded) | {"W": 3, "K": 20} |
| `lrvol_5_k20` | VOL | v | NQ | 5 | window in session; baseline previous 20 sessions (roll window excluded) | {"W": 5, "K": 20} |
| `lrvol_10_k20` | VOL | v | NQ | 10 | window in session; baseline previous 20 sessions (roll window excluded) | {"W": 10, "K": 20} |
| `lrvol_15_k20` | VOL | v | NQ | 15 | window in session; baseline previous 20 sessions (roll window excluded) | {"W": 15, "K": 20} |
| `lrvol_30_k20` | VOL | v | NQ | 30 | window in session; baseline previous 20 sessions (roll window excluded) | {"W": 30, "K": 20} |
| `lrvol_60_k20` | VOL | v | NQ | 60 | window in session; baseline previous 20 sessions (roll window excluded) | {"W": 60, "K": 20} |
| `lrvol_5_k10` | VOL | v | NQ | 5 | session+roll | {"W": 5, "K": 10} |
| `lrvol_5_k60` | VOL | v | NQ | 5 | session+roll | {"W": 5, "K": 60} |
| `lrvol_5_k120` | VOL | v | NQ | 5 | session+roll | {"W": 5, "K": 120} |
| `lrvol_15_k10` | VOL | v | NQ | 15 | session+roll | {"W": 15, "K": 10} |
| `lrvol_15_k60` | VOL | v | NQ | 15 | session+roll | {"W": 15, "K": 60} |
| `lrvol_15_k120` | VOL | v | NQ | 15 | session+roll | {"W": 15, "K": 120} |
| `lrvol_30_k10` | VOL | v | NQ | 30 | session+roll | {"W": 30, "K": 10} |
| `lrvol_30_k60` | VOL | v | NQ | 30 | session+roll | {"W": 30, "K": 60} |
| `lrvol_30_k120` | VOL | v | NQ | 30 | session+roll | {"W": 30, "K": 120} |
| `lrvol_cum_rth` | VOL | v | NQ | 390 | session+roll | {} |
| `lrvol_cum_sess` | VOL | v | NQ | 1380 | session+roll | {} |
| `vol_mom` | VOL | v | NQ | 60 | session+roll | {} |
| `vol_accel` | VOL | v | NQ | 10 | session+roll | {} |
| `vol_slope_t15` | VOL | v | NQ | 15 | session+roll | {} |
| `vol_conc_15` | VOL | v | NQ | 15 | session+roll | {} |
| `vol_conc_60` | VOL | v | NQ | 60 | session+roll | {} |
| `vol_entropy_15` | VOL | v | NQ | 15 | session+roll | {} |
| `upvol_15` | VOL | o,c,v | NQ | 15 | session+roll | {} |
| `sgnvol_15` | VOL | o,c,v | NQ | 15 | session+roll | {} |
| `clvvol_15` | VOL | h,l,c,v | NQ | 15 | session+roll | {} |
| `upvol_60` | VOL | o,c,v | NQ | 60 | session+roll | {} |
| `sgnvol_60` | VOL | o,c,v | NQ | 60 | session+roll | {} |
| `clvvol_60` | VOL | h,l,c,v | NQ | 60 | session+roll | {} |
| `obv_30` | VOL | c,v | NQ | 30 | session+roll | {} |
| `obv_120` | VOL | c,v | NQ | 120 | session+roll | {} |
| `pvt_30` | VOL | c,v | NQ | 30 | session+roll | {} |
| `ret_per_vol_15` | VOL | c,v | NQ | 15 | session+roll | {} |
| `range_per_vol_15` | VOL | h,l,c,v | NQ | 15 | session+roll | {} |
| `er_per_vol_15` | VOL | c,v | NQ | 15 | session+roll | {} |
| `dirvol_30` | VOL | c,v | NQ | 30 | session+roll | {} |
| `vol_expansion` | VOL | v | NQ | 30 | session+roll | {} |
| `vdist_rth` | VWAP | h,l,c,v | NQ | 1 | anchored at 09:30 | {"approximation": "bar typical price"} |
| `vdist_glx` | VWAP | h,l,c,v | NQ | 1 | anchored at 18:00 | {"approximation": "bar typical price"} |
| `vslope_rth` | VWAP | h,l,c,v | NQ | 15 | session+roll | {} |
| `vside_run_rth` | VWAP | c,v | NQ | 30 | session+roll | {} |
| `es_vside_rth` | VWAP | h,l,c,v | ES | 1 | session+roll | {} |
| `vwap_state_disagree` | VWAP | c | NQ,ES | 1 | session+roll | {} |
| `er_5` | PATH | c | NQ | 5 | session+roll | {"H": 5} |
| `er_15` | PATH | c | NQ | 15 | session+roll | {"H": 15} |
| `er_30` | PATH | c | NQ | 30 | session+roll | {"H": 30} |
| `er_60` | PATH | c | NQ | 60 | session+roll | {"H": 60} |
| `er_120` | PATH | c | NQ | 120 | session+roll | {"H": 120} |
| `er_240` | PATH | c | NQ | 240 | session+roll | {"H": 240} |
| `ols_t_15` | PATH | c | NQ | 15 | session+roll | {"H": 15} |
| `ols_r2_15` | PATH | c | NQ | 15 | session+roll | {"H": 15} |
| `ols_resid_15` | PATH | c | NQ | 15 | session+roll | {"H": 15} |
| `ols_t_30` | PATH | c | NQ | 30 | session+roll | {"H": 30} |
| `ols_r2_30` | PATH | c | NQ | 30 | session+roll | {"H": 30} |
| `ols_resid_30` | PATH | c | NQ | 30 | session+roll | {"H": 30} |
| `ols_t_60` | PATH | c | NQ | 60 | session+roll | {"H": 60} |
| `ols_r2_60` | PATH | c | NQ | 60 | session+roll | {"H": 60} |
| `ols_resid_60` | PATH | c | NQ | 60 | session+roll | {"H": 60} |
| `ols_t_120` | PATH | c | NQ | 120 | session+roll | {"H": 120} |
| `ols_r2_120` | PATH | c | NQ | 120 | session+roll | {"H": 120} |
| `ols_resid_120` | PATH | c | NQ | 120 | session+roll | {"H": 120} |
| `retr_15` | PATH | c | NQ | 15 | session+roll | {"H": 15} |
| `revs_15` | PATH | c | NQ | 15 | session+roll | {"H": 15} |
| `dfrac_15` | PATH | c | NQ | 15 | session+roll | {"H": 15} |
| `run_15` | PATH | c | NQ | 15 | session+roll | {"H": 15} |
| `big1_15` | PATH | c | NQ | 15 | session+roll | {"H": 15} |
| `top3_15` | PATH | c | NQ | 15 | session+roll | {"H": 15} |
| `early_15` | PATH | c | NQ | 15 | session+roll | {"H": 15} |
| `late_15` | PATH | c | NQ | 15 | session+roll | {"H": 15} |
| `retr_30` | PATH | c | NQ | 30 | session+roll | {"H": 30} |
| `revs_30` | PATH | c | NQ | 30 | session+roll | {"H": 30} |
| `dfrac_30` | PATH | c | NQ | 30 | session+roll | {"H": 30} |
| `run_30` | PATH | c | NQ | 30 | session+roll | {"H": 30} |
| `big1_30` | PATH | c | NQ | 30 | session+roll | {"H": 30} |
| `top3_30` | PATH | c | NQ | 30 | session+roll | {"H": 30} |
| `early_30` | PATH | c | NQ | 30 | session+roll | {"H": 30} |
| `late_30` | PATH | c | NQ | 30 | session+roll | {"H": 30} |
| `retr_60` | PATH | c | NQ | 60 | session+roll | {"H": 60} |
| `revs_60` | PATH | c | NQ | 60 | session+roll | {"H": 60} |
| `dfrac_60` | PATH | c | NQ | 60 | session+roll | {"H": 60} |
| `run_60` | PATH | c | NQ | 60 | session+roll | {"H": 60} |
| `big1_60` | PATH | c | NQ | 60 | session+roll | {"H": 60} |
| `top3_60` | PATH | c | NQ | 60 | session+roll | {"H": 60} |
| `early_60` | PATH | c | NQ | 60 | session+roll | {"H": 60} |
| `late_60` | PATH | c | NQ | 60 | session+roll | {"H": 60} |
| `retr_120` | PATH | c | NQ | 120 | session+roll | {"H": 120} |
| `revs_120` | PATH | c | NQ | 120 | session+roll | {"H": 120} |
| `dfrac_120` | PATH | c | NQ | 120 | session+roll | {"H": 120} |
| `run_120` | PATH | c | NQ | 120 | session+roll | {"H": 120} |
| `big1_120` | PATH | c | NQ | 120 | session+roll | {"H": 120} |
| `top3_120` | PATH | c | NQ | 120 | session+roll | {"H": 120} |
| `early_120` | PATH | c | NQ | 120 | session+roll | {"H": 120} |
| `late_120` | PATH | c | NQ | 120 | session+roll | {"H": 120} |
| `body_30` | PATH | o,c | NQ | 30 | session+roll | {} |
| `wick_30` | PATH | o,h,l,c | NQ | 30 | session+roll | {} |
| `hhi_30` | PATH | c | NQ | 30 | session+roll | {} |
| `rvratio_15` | DIST | c | NQ | 15 | window in session; tod baseline 20 sessions | {} |
| `semi_15` | DIST | c | NQ | 15 | session+roll | {} |
| `skew_15` | DIST | c | NQ | 15 | session+roll | {} |
| `kurt_15` | DIST | c | NQ | 15 | session+roll | {} |
| `mabs_15` | DIST | c | NQ | 15 | session+roll | {} |
| `rvratio_30` | DIST | c | NQ | 30 | window in session; tod baseline 20 sessions | {} |
| `semi_30` | DIST | c | NQ | 30 | session+roll | {} |
| `skew_30` | DIST | c | NQ | 30 | session+roll | {} |
| `kurt_30` | DIST | c | NQ | 30 | session+roll | {} |
| `mabs_30` | DIST | c | NQ | 30 | session+roll | {} |
| `rvratio_60` | DIST | c | NQ | 60 | window in session; tod baseline 20 sessions | {} |
| `semi_60` | DIST | c | NQ | 60 | session+roll | {} |
| `skew_60` | DIST | c | NQ | 60 | session+roll | {} |
| `kurt_60` | DIST | c | NQ | 60 | session+roll | {} |
| `mabs_60` | DIST | c | NQ | 60 | session+roll | {} |
| `rvratio_120` | DIST | c | NQ | 120 | window in session; tod baseline 20 sessions | {} |
| `semi_120` | DIST | c | NQ | 120 | session+roll | {} |
| `skew_120` | DIST | c | NQ | 120 | session+roll | {} |
| `kurt_120` | DIST | c | NQ | 120 | session+roll | {} |
| `mabs_120` | DIST | c | NQ | 120 | session+roll | {} |
| `tailfreq_30` | DIST | c | NQ | 30 | session+roll | {} |
| `tailfreq_60` | DIST | c | NQ | 60 | session+roll | {} |
| `maxpos_30` | DIST | c | NQ | 30 | session+roll | {} |
| `maxneg_30` | DIST | c | NQ | 30 | session+roll | {} |
| `jz` | JUMP | c | NQ | 61 | session+roll | {"bv_window": 60, "uses": "previous bars only for scale"} |
| `jr_30` | JUMP | c | NQ | 30 | session+roll | {"W": 30} |
| `jr_60` | JUMP | c | NQ | 60 | session+roll | {"W": 60} |
| `jcount_pos_30` | JUMP | c | NQ | 30 | session+roll | {} |
| `jcount_neg_30` | JUMP | c | NQ | 30 | session+roll | {} |
| `bars_since_jump` | JUMP | c | NQ | 1380 | session+roll | {} |
| `es_jz` | JUMP | c | ES | 61 | session+roll | {} |
| `vr5_120` | PERS | c | NQ | 125 | session+roll | {} |
| `vr15_120` | PERS | c | NQ | 135 | session+roll | {} |
| `vr5_60` | PERS | c | NQ | 65 | session+roll | {} |
| `ac1_120` | PERS | c | NQ | 121 | session+roll | {} |
| `ac1_30` | PERS | c | NQ | 31 | session+roll | {} |
| `sac1_60` | PERS | c | NQ | 61 | session+roll | {} |
| `entropy_60` | PERS | c | NQ | 62 | session+roll | {} |
| `vr_ch` | PERS | c | NQ | 155 | session+roll | {} |
| `ac_ch` | PERS | c | NQ | 151 | session+roll | {} |
| `er_ch` | PERS | c | NQ | 60 | session+roll | {} |
| `ent_ch` | PERS | c | NQ | 92 | session+roll | {} |
| `rvol_ch` | PERS | v | NQ | 45 | session+roll | {} |
| `volreg_ch` | PERS | c | NQ | 60 | session+roll | {} |
| `on_retz` | OPEN | o,h,l,c,v | NQ | 930 | per session: overnight bars 18:00-09:29, constant through RTH | {} |
| `on_range` | OPEN | o,h,l,c,v | NQ | 930 | per session: overnight bars 18:00-09:29, constant through RTH | {} |
| `on_er` | OPEN | o,h,l,c,v | NQ | 930 | per session: overnight bars 18:00-09:29, constant through RTH | {} |
| `on_lrvol` | OPEN | o,h,l,c,v | NQ | 930 | per session: overnight bars 18:00-09:29, constant through RTH | {} |
| `on_loc` | OPEN | o,h,l,c,v | NQ | 930 | per session: overnight bars 18:00-09:29, constant through RTH | {} |
| `on_semi` | OPEN | o,h,l,c,v | NQ | 930 | per session: overnight bars 18:00-09:29, constant through RTH | {} |
| `on_jumps` | OPEN | o,h,l,c,v | NQ | 930 | per session: overnight bars 18:00-09:29, constant through RTH | {} |
| `on_r2` | OPEN | o,h,l,c,v | NQ | 930 | per session: overnight bars 18:00-09:29, constant through RTH | {} |
| `on_final15z` | OPEN | o,h,l,c,v | NQ | 930 | per session: overnight bars 18:00-09:29, constant through RTH | {} |
| `on_final30z` | OPEN | o,h,l,c,v | NQ | 930 | per session: overnight bars 18:00-09:29, constant through RTH | {} |
| `on_final60z` | OPEN | o,h,l,c,v | NQ | 930 | per session: overnight bars 18:00-09:29, constant through RTH | {} |
| `pm_retz` | OPEN | o,h,l,c,v | NQ | 930 | per session: overnight bars 18:00-09:29, constant through RTH | {} |
| `pm_lrvol` | OPEN | o,h,l,c,v | NQ | 930 | per session: overnight bars 18:00-09:29, constant through RTH | {} |
| `es_retz_5` | XMKT | c | ES | 5 | session+roll | {} |
| `es_retz_15` | XMKT | c | ES | 15 | session+roll | {} |
| `es_retz_30` | XMKT | c | ES | 30 | session+roll | {} |
| `es_lrvol_5` | XMKT | v | ES | 5 | session+roll | {} |
| `es_lrvol_15` | XMKT | v | ES | 15 | session+roll | {} |
| `rel_lrvol_15` | XMKT | v | NQ,ES | 15 | session+roll | {} |
| `rel_lrvol_ch` | XMKT | v | NQ,ES | 45 | session+roll | {} |
| `rel_semi_30` | XMKT | c | NQ,ES | 30 | session+roll | {} |
| `rel_er_15` | XMKT | c | NQ,ES | 15 | session+roll | {} |
| `rel_er_60` | XMKT | c | NQ,ES | 60 | session+roll | {} |
| `rel_r2_60` | XMKT | c | NQ,ES | 60 | session+roll | {} |
| `corr_60` | XMKT | c | NQ,ES | 60 | session+roll | {} |
| `corr_240` | XMKT | c | NQ,ES | 240 | session+roll | {} |
| `corr_ch` | XMKT | c | NQ,ES | 240 | session+roll | {} |
| `beta_120` | XMKT | c | NQ,ES | 120 | session+roll | {} |
| `beta_ch` | XMKT | c | NQ,ES | 180 | session+roll | {} |
| `residz_15` | XMKT | c | NQ,ES | 135 | session+roll | {} |
| `vol_disagree_30` | XMKT | c | NQ,ES | 30 | session+roll | {} |
| `pers_disagree` | XMKT | c | NQ,ES | 125 | session+roll | {} |
| `dow` | CAL |  | NQ | 0 | calendar | {} |
| `month` | CAL |  | NQ | 0 | calendar | {} |
| `tdom` | CAL |  | NQ | 0 | calendar (count of sessions so far this month) | {} |
| `weekdays_left_in_month` | CAL |  | NQ | 0 | calendar (weekday approximation; holidays ignored) | {} |
| `opex_week` | CAL |  | NQ | 0 | calendar (third-Friday week) | {} |
| `tod` | CAL |  | NQ | 0 | clock | {} |
| `rsi_14` | TECH | c | NQ | 14 | session+roll | {} |
| `macd_hist` | TECH | c | NQ | 35 | session+roll | {} |
| `adx_14` | TECH | h,l,c | NQ | 28 | session+roll | {} |
| `di_diff_14` | TECH | h,l,c | NQ | 14 | session+roll | {} |
| `cci_20` | TECH | h,l,c | NQ | 20 | session+roll | {"mad_approx": "0.8*std"} |
| `stoch_14` | TECH | h,l,c | NQ | 14 | session+roll | {} |
| `aroon_osc_25` | TECH | h,l | NQ | 25 | session+roll | {} |
| `bb_pb` | TECH | c | NQ | 20 | session+roll | {} |
| `keltner_pos` | TECH | h,l,c | NQ | 20 | session+roll | {} |
| `dist_prev_hi` | REOPEN | h,c | NQ | 1380 | prior session RTH high | {} |

## Triggers (signed events at a bar close)

### CAL (8)
- `CAL:time_of_day:sm=929`
- `CAL:time_of_day:sm=959`
- `CAL:time_of_day:sm=1019`
- `CAL:time_of_day:sm=1079`
- `CAL:time_of_day:sm=1139`
- `CAL:time_of_day:sm=1199`
- `CAL:time_of_day:sm=1259`
- `CAL:time_of_day:sm=1284`

### DIST (14)
- `DIST:semi_cross:W=30,thr=0.5`
- `DIST:semi_cross:W=30,thr=0.7`
- `DIST:semi_cross:W=60,thr=0.5`
- `DIST:semi_cross:W=60,thr=0.7`
- `DIST:skew_cross:W=60,thr=1.0`
- `DIST:skew_cross:W=60,thr=2.0`
- `DIST:skew_cross:W=120,thr=1.0`
- `DIST:skew_cross:W=120,thr=2.0`
- `DIST:rv_shock:W=15,thr=2.0`
- `DIST:rv_shock:W=15,thr=3.0`
- `DIST:rv_shock:W=30,thr=2.0`
- `DIST:rv_shock:W=30,thr=3.0`
- `DIST:tail_cluster:W=30`
- `DIST:tail_cluster:W=60`

### JUMP (12)
- `JUMP:jump_bar:thr=4.0`
- `JUMP:jump_bar:thr=6.0`
- `JUMP:double_jump_same_dir:`
- `JUMP:opposing_jumps:`
- `JUMP:trend_then_jump_same:`
- `JUMP:trend_then_jump_against:`
- `JUMP:jump_then_smooth:`
- `JUMP:jr_cross:W=60,thr=0.4`
- `JUMP:jr_cross:W=60,thr=0.6`
- `JUMP:nq_only_jump:`
- `JUMP:es_only_jump:`
- `JUMP:joint_jump:`

### OPEN (36)
- `OPEN:opening_move:X=1,thr=0.5`
- `OPEN:opening_move:X=1,thr=1.0`
- `OPEN:opening_move:X=1,thr=1.5`
- `OPEN:opening_move:X=3,thr=0.5`
- `OPEN:opening_move:X=3,thr=1.0`
- `OPEN:opening_move:X=3,thr=1.5`
- `OPEN:opening_move:X=5,thr=0.5`
- `OPEN:opening_move:X=5,thr=1.0`
- `OPEN:opening_move:X=5,thr=1.5`
- `OPEN:opening_move:X=10,thr=0.5`
- `OPEN:opening_move:X=10,thr=1.0`
- `OPEN:opening_move:X=10,thr=1.5`
- `OPEN:opening_move:X=15,thr=0.5`
- `OPEN:opening_move:X=15,thr=1.0`
- `OPEN:opening_move:X=15,thr=1.5`
- `OPEN:opening_move:X=30,thr=0.5`
- `OPEN:opening_move:X=30,thr=1.0`
- `OPEN:opening_move:X=30,thr=1.5`
- `OPEN:opening_move:X=60,thr=0.5`
- `OPEN:opening_move:X=60,thr=1.0`
- `OPEN:opening_move:X=60,thr=1.5`
- `OPEN:overnight_return:X=0,thr=0.5`
- `OPEN:overnight_return:X=0,thr=1.0`
- `OPEN:overnight_return:X=0,thr=1.5`
- `OPEN:overnight_return:X=5,thr=0.5`
- `OPEN:overnight_return:X=5,thr=1.0`
- `OPEN:overnight_return:X=5,thr=1.5`
- `OPEN:overnight_return:X=15,thr=0.5`
- `OPEN:overnight_return:X=15,thr=1.0`
- `OPEN:overnight_return:X=15,thr=1.5`
- `OPEN:overnight_final30:thr=1.0`
- `OPEN:overnight_final30:thr=1.5`
- `OPEN:overnight_acceptance:`
- `OPEN:overnight_rejection:`
- `OPEN:gap:thr=0.5`
- `OPEN:gap:thr=1.0`

### PATH (27)
- `PATH:er_cross:H=15,thr=0.5`
- `PATH:er_cross:H=15,thr=0.7`
- `PATH:er_cross:H=30,thr=0.5`
- `PATH:er_cross:H=30,thr=0.7`
- `PATH:er_cross:H=60,thr=0.5`
- `PATH:er_cross:H=60,thr=0.7`
- `PATH:er_cross:H=120,thr=0.5`
- `PATH:er_cross:H=120,thr=0.7`
- `PATH:ols_t_cross:H=15,thr=3.0`
- `PATH:ols_t_cross:H=15,thr=5.0`
- `PATH:ols_t_cross:H=30,thr=3.0`
- `PATH:ols_t_cross:H=30,thr=5.0`
- `PATH:ols_t_cross:H=60,thr=3.0`
- `PATH:ols_t_cross:H=60,thr=5.0`
- `PATH:r2_cross:H=30,thr=0.7`
- `PATH:r2_cross:H=30,thr=0.85`
- `PATH:clean_trend:H=30`
- `PATH:low_concentration_trend:H=30`
- `PATH:late_acceleration:H=30`
- `PATH:r2_cross:H=60,thr=0.7`
- `PATH:r2_cross:H=60,thr=0.85`
- `PATH:clean_trend:H=60`
- `PATH:low_concentration_trend:H=60`
- `PATH:late_acceleration:H=60`
- `PATH:directional_run:H=30,N=6`
- `PATH:directional_run:H=30,N=8`
- `PATH:body_dominance:H=30`

### PERS (13)
- `PERS:vr_low_to_high:hi=1.2,lo=0.9`
- `PERS:vr_low_to_high:hi=1.4,lo=1.0`
- `PERS:vr_high_to_low:`
- `PERS:ac_neg_to_pos:`
- `PERS:ac_pos_to_neg:`
- `PERS:er_low_to_high:thr=0.5`
- `PERS:er_low_to_high:thr=0.7`
- `PERS:entropy_high_to_low:`
- `PERS:rvol_normal_to_abnormal:`
- `PERS:vol_low_to_high:`
- `PERS:choppy_to_directional:`
- `PERS:momentum_at_persistence_onset:`
- `PERS:momentum_in_mature_persistence:`

### REOPEN (17)
- `REOPEN:orb:X=15`
- `REOPEN:orb:X=30`
- `REOPEN:orb:X=60`
- `REOPEN:rolling_breakout:N=60`
- `REOPEN:rolling_breakout:N=120`
- `REOPEN:rolling_breakout:N=240`
- `REOPEN:failed_breakout:N=60`
- `REOPEN:failed_breakout:N=240`
- `REOPEN:compression_expansion:bar=2.5,range=2.0`
- `REOPEN:compression_expansion:bar=3.0,range=1.5`
- `REOPEN:displacement:thr=3.0`
- `REOPEN:displacement:thr=4.0`
- `REOPEN:prior_session_level_break:`
- `REOPEN:prior_session_failed_break:`
- `REOPEN:overnight_level_break:`
- `REOPEN:fvg:thr=0.5`
- `REOPEN:fvg:thr=1.0`

### RET (24)
- `RET:retz_cross:H=1,thr=1.5`
- `RET:retz_cross:H=1,thr=2.0`
- `RET:retz_cross:H=1,thr=2.5`
- `RET:retz_cross:H=1,thr=3.0`
- `RET:retz_cross:H=5,thr=1.5`
- `RET:retz_cross:H=5,thr=2.0`
- `RET:retz_cross:H=5,thr=2.5`
- `RET:retz_cross:H=5,thr=3.0`
- `RET:retz_cross:H=15,thr=1.5`
- `RET:retz_cross:H=15,thr=2.0`
- `RET:retz_cross:H=15,thr=2.5`
- `RET:retz_cross:H=15,thr=3.0`
- `RET:retz_cross:H=30,thr=1.5`
- `RET:retz_cross:H=30,thr=2.0`
- `RET:retz_cross:H=30,thr=2.5`
- `RET:retz_cross:H=30,thr=3.0`
- `RET:retz_cross:H=60,thr=1.5`
- `RET:retz_cross:H=60,thr=2.0`
- `RET:retz_cross:H=60,thr=2.5`
- `RET:retz_cross:H=60,thr=3.0`
- `RET:open_retz_cross:thr=1.0`
- `RET:open_retz_cross:thr=1.5`
- `RET:open_retz_cross:thr=2.0`
- `RET:trend_agree_full:`

### TECH (10)
- `TECH:rsi_extreme:hi=70,lo=30`
- `TECH:rsi_extreme:hi=80,lo=20`
- `TECH:macd_zero_cross:`
- `TECH:dmi_cross_adx25:`
- `TECH:cci_cross:thr=100.0`
- `TECH:cci_cross:thr=200.0`
- `TECH:stoch_extreme:`
- `TECH:aroon_cross:thr=50.0`
- `TECH:bollinger_break:thr=1.0`
- `TECH:keltner_break:thr=1.0`

### VOL (29)
- `VOL:rvol_cross_up:W=1,thr=2.0`
- `VOL:rvol_cross_up:W=1,thr=3.0`
- `VOL:rvol_cross_up:W=1,thr=5.0`
- `VOL:rvol_cross_up:W=5,thr=2.0`
- `VOL:rvol_cross_up:W=5,thr=3.0`
- `VOL:rvol_cross_up:W=5,thr=5.0`
- `VOL:rvol_cross_up:W=15,thr=2.0`
- `VOL:rvol_cross_up:W=15,thr=3.0`
- `VOL:rvol_cross_up:W=15,thr=5.0`
- `VOL:vol_accel_up:thr=1.0`
- `VOL:vol_accel_up:thr=1.5`
- `VOL:sgnvol_cross:W=15,thr=0.3`
- `VOL:clvvol_cross:W=15,thr=0.3`
- `VOL:sgnvol_cross:W=15,thr=0.5`
- `VOL:clvvol_cross:W=15,thr=0.5`
- `VOL:sgnvol_cross:W=60,thr=0.3`
- `VOL:clvvol_cross:W=60,thr=0.3`
- `VOL:sgnvol_cross:W=60,thr=0.5`
- `VOL:clvvol_cross:W=60,thr=0.5`
- `VOL:obv_cross:W=30,thr=0.2`
- `VOL:obv_cross:W=30,thr=0.35`
- `VOL:obv_cross:W=120,thr=0.2`
- `VOL:obv_cross:W=120,thr=0.35`
- `VOL:vol_conc_spike:thr=0.35`
- `VOL:vol_conc_spike:thr=0.5`
- `VOL:absorption:rvol=2.0`
- `VOL:absorption:rvol=3.0`
- `VOL:dirvol_cross:thr=0.7`
- `VOL:dirvol_cross:thr=1.2`

### VWAP (16)
- `VWAP:cross:anchor=rth`
- `VWAP:dist_cross:anchor=rth,thr=1.5`
- `VWAP:dist_cross:anchor=rth,thr=2.0`
- `VWAP:dist_cross:anchor=rth,thr=3.0`
- `VWAP:reclaim:N=15,anchor=rth`
- `VWAP:reclaim:N=30,anchor=rth`
- `VWAP:acceptance:N=5,anchor=rth`
- `VWAP:acceptance:N=10,anchor=rth`
- `VWAP:rejection:anchor=rth`
- `VWAP:cross:anchor=glx`
- `VWAP:dist_cross:anchor=glx,thr=1.5`
- `VWAP:dist_cross:anchor=glx,thr=2.0`
- `VWAP:dist_cross:anchor=glx,thr=3.0`
- `VWAP:rejection:anchor=glx`
- `VWAP:slope_cross:thr=1.0`
- `VWAP:slope_cross:thr=2.0`

### XMKT (17)
- `XMKT:rel_rvol_nq_dominant:thr=0.7`
- `XMKT:rel_rvol_es_dominant:thr=0.7`
- `XMKT:rel_rvol_nq_dominant:thr=1.0`
- `XMKT:rel_rvol_es_dominant:thr=1.0`
- `XMKT:nq_only_participation_shock:`
- `XMKT:es_only_participation_shock:`
- `XMKT:joint_participation_shock:`
- `XMKT:corr_breakdown:thr=0.5`
- `XMKT:corr_breakdown:thr=0.3`
- `XMKT:residual_cross:thr=2.0`
- `XMKT:residual_cross:thr=3.0`
- `XMKT:er_disagree:H=15,thr=0.4`
- `XMKT:er_disagree:H=15,thr=0.6`
- `XMKT:semi_disagree:thr=0.5`
- `XMKT:vol_disagree:thr=0.7`
- `XMKT:pers_disagree:thr=0.4`
- `XMKT:es_volume_lead:`

## Filters (state at the decision bar; directional filters are defined relative to the trade direction)

| bit | id | group | directional | description |
|---|---|---|---|---|
| 0 | `rvol_high` | volume | False | RVOL15 > 1.5 |
| 1 | `rvol_low` | volume | False | RVOL15 < 0.7 |
| 2 | `rvol_cum_rth_high` | volume | False | cumulative RTH RVOL > 1.3 |
| 3 | `vol_accelerating` | volume | False | RVOL5 > 1.5 x RVOL60 |
| 4 | `on_rvol_high` | volume | False | overnight RVOL > 1.3 |
| 5 | `volreg_high` | volatility | False | RV60 > 1.5 x tod baseline |
| 6 | `volreg_low` | volatility | False | RV60 < 0.7 x tod baseline |
| 7 | `on_range_high` | volatility | False | overnight range high |
| 8 | `on_range_low` | volatility | False | overnight range low |
| 9 | `jump_recent` | volatility | False | |jz|>4 in last 30 |
| 10 | `er_high` | persistence | False | |ER60| > 0.4 |
| 11 | `er_low` | persistence | False | |ER60| < 0.15 |
| 12 | `vr_high` | persistence | False | VR(5,120) > 1.2 |
| 13 | `vr_low` | persistence | False | VR(5,120) < 0.8 |
| 14 | `entropy_low` | persistence | False | 3-bar pattern entropy < 0.9 |
| 15 | `first_hour` | time | False | decision 09:29-10:28 |
| 16 | `midday` | time | False | decision 10:49-13:48 |
| 17 | `last_90` | time | False | decision 13:49-15:29 |
| 18 | `monday` | calendar | False |  |
| 19 | `friday` | calendar | False |  |
| 20 | `month_turn` | calendar | False | first 3 / last 2 sessions of month |
| 21 | `opex_week` | calendar | False |  |
| 22 | `corr_low` | cross | False | corr60(NQ,ES) < 0.6 |
| 23 | `es_confirms` | cross | True | ES 15m z agrees with trade (>0.5) |
| 24 | `es_diverges` | cross | True | ES 15m z against trade |
| 25 | `trend240_aligned` | trend | True |  |
| 26 | `trend60_aligned` | trend | True |  |
| 27 | `trend60_against` | trend | True |  |
| 28 | `range_top_for_long` | trend | True |  |
| 29 | `range_bottom_for_long` | trend | True |  |
| 30 | `vwap_aligned` | vwap | True | long above / short below RTH VWAP |
| 31 | `vwap_against` | vwap | True |  |
| 32 | `on_aligned` | overnight | True |  |
| 33 | `on_against` | overnight | True |  |
| 34 | `open_aligned` | flow | True |  |
| 35 | `sgnvol_aligned` | flow | True |  |
| 36 | `clvvol_aligned` | flow | True |  |
| 37 | `semi_aligned` | flow | True |  |
| 38 | `rsi_stretched_against` | oscillator | True | long when RSI<30 / short when RSI>70 |

## Symbolic states

5-minute buckets (session-minute aligned). Return state = the 5-min log return / (sig1*sqrt5), 3 levels (+-0.5) or 5 levels (+-0.5, +-1.5). Volume state = bucket RVOL vs the 20-session tod baseline (<0.7, 0.7-1.5, >1.5). Close location = close within the bucket range (thirds). Sequences of L consecutive complete buckets within a session.

- `A9`: {'ret_levels': 3, 'vol_levels': 3, 'loc_levels': 1, 'lengths': (2, 3, 4, 5)}
- `A15`: {'ret_levels': 5, 'vol_levels': 3, 'loc_levels': 1, 'lengths': (2, 3)}
- `A45`: {'ret_levels': 5, 'vol_levels': 3, 'loc_levels': 3, 'lengths': (2,)}

## Exits (canonical, 14)

Stop = mult x 3.1623 x stop_scale, rounded up to the tick. stop_scale = sqrt(tod-expected true range x mean true range of the last 30 bars).

- `S1_T15`: {'id': 'S1_T15', 'stop_mult': 1.0, 'hold': 15, 'target_R': 0.0}
- `S1_T30`: {'id': 'S1_T30', 'stop_mult': 1.0, 'hold': 30, 'target_R': 0.0}
- `S1_T60`: {'id': 'S1_T60', 'stop_mult': 1.0, 'hold': 60, 'target_R': 0.0}
- `S1_T120`: {'id': 'S1_T120', 'stop_mult': 1.0, 'hold': 120, 'target_R': 0.0}
- `S1_EOD`: {'id': 'S1_EOD', 'stop_mult': 1.0, 'hold': -1, 'target_R': 0.0}
- `S1_R2`: {'id': 'S1_R2', 'stop_mult': 1.0, 'hold': -1, 'target_R': 2.0}
- `S1_R3`: {'id': 'S1_R3', 'stop_mult': 1.0, 'hold': -1, 'target_R': 3.0}
- `S2_T15`: {'id': 'S2_T15', 'stop_mult': 2.0, 'hold': 15, 'target_R': 0.0}
- `S2_T30`: {'id': 'S2_T30', 'stop_mult': 2.0, 'hold': 30, 'target_R': 0.0}
- `S2_T60`: {'id': 'S2_T60', 'stop_mult': 2.0, 'hold': 60, 'target_R': 0.0}
- `S2_T120`: {'id': 'S2_T120', 'stop_mult': 2.0, 'hold': 120, 'target_R': 0.0}
- `S2_EOD`: {'id': 'S2_EOD', 'stop_mult': 2.0, 'hold': -1, 'target_R': 0.0}
- `S2_R2`: {'id': 'S2_R2', 'stop_mult': 2.0, 'hold': -1, 'target_R': 2.0}
- `S2_R3`: {'id': 'S2_R3', 'stop_mult': 2.0, 'hold': -1, 'target_R': 3.0}

## Candidate counts

```
{
 "n_triggers": 223,
 "n_filters": 39,
 "n_combos": 721,
 "n_variants": 6,
 "n_exits": 14,
 "per_family": {
  "RET": 1453536,
  "VOL": 1756356,
  "VWAP": 969024,
  "PATH": 1635228,
  "DIST": 847896,
  "JUMP": 726768,
  "PERS": 787332,
  "OPEN": 2180304,
  "XMKT": 1029588,
  "CAL": 484512,
  "TECH": 605640,
  "REOPEN": 1029588,
  "SYM": 576360,
  "ML": 1428
 },
 "rule_total": 13505772,
 "sym_total": 576360,
 "total": 14083560
}
```

Ordered candidate-ID fingerprint: `ad3b6d29aa6e23ad2552b7415676b42bdf0e8b82763dc0bf1df0e6573f7daa5c` over 14,083,560 IDs.
