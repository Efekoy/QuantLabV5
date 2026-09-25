# V4 OFFICIAL 2026 FORWARD TEST report (sealed 2026 partition)

Sessions 2026-01-02 .. 2026-08-10 (157 sessions). The FROZEN cohort (SUPPORTED_COHORT) was run exactly as frozen in FINAL_COHORT_FREEZE (`1708eddc`, 2026-09-25T05:20:01Z): no tuning, replacement, reselection, filter change, exit change or sizing change. All members are reported, failures included.

**Disclosure.** Earlier V2/V3 research exposed the researchers to some information about 2026 market behaviour, so 2026 is not perfectly researcher-blind. However, QuantLabV4's exact strategies, parameters, exits, sizing and prop policy were frozen before the V4 system accessed the 2026 partition (stage gate plus ledger), so 2026 is treated as the V4 system's sealed out-of-sample forward test. The NQ data ends 2026-08-10 (the last complete session in the source file).

## Cohort (each member traded as 1 NQ contract; net of baseline cost)

| trades | net pts | net $ (1 NQ each) | t | PF | expectancy pts | win rate | max DD pts | net pts moderate | net pts stress | preregistered cohort verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 309 | 3,945.5 | 78,909 | 1.58 | 1.27 | 12.77 | 0.48 | 1,708.6 | 4,022.7 | 3,760.1 | **PASS** |

Cohort PASS rule (frozen): net > 0 at baseline AND at stress cost, AND cohort t >= 1.5.

## Strategies

| id | family | trigger | variant | filters | exit | trades | net pts | t | PF | max DD pts | stress net | class | net by year |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q4-60857891da97d59c25f0f86c | VWAP | VWAP:dist_cross:anchor=glx,thr=3.0 | cont_long | sgnvol_aligned, volreg_low | S2_R3 | 50 | 266.3 | 0.39 | 1.15 | 474.5 | 236.3 | **INCONCLUSIVE** | {"2026": 266.3} |
| Q4-9757cb9ee92c11b68d2ad60b | DIST | DIST:semi_cross:W=30,thr=0.7 | cont_both | es_confirms, trend60_aligned | S2_EOD | 131 | 151.8 | 0.08 | 1.02 | 1,708.6 | 73.2 | **INCONCLUSIVE** | {"2026": 151.8} |
| Q4-14478681d690cde198df1979 | RET | RET:retz_cross:H=15,thr=2.0 | cont_short | sgnvol_aligned, volreg_low | S2_T30 | 48 | 268.9 | 0.47 | 1.22 | 348.0 | 240.1 | **INCONCLUSIVE** | {"2026": 268.9} |
| Q4-40aae8a2c827fb779e4dd7b9 | RET | RET:open_retz_cross:thr=2.0 | cont_both | semi_aligned, volreg_low | S2_R3 | 74 | 3,270.5 | 2.36 | 2.13 | 468.4 | 3,226.1 | **SUPPORTED** | {"2026": 3270.5} |
| Q4-c790712e4f51f6f4268b0033 | XMKT | XMKT:er_disagree:H=15,thr=0.4 | cont_both | corr_low, first_hour | S2_T60 | 6 | -11.9 | -0.03 | 0.97 | 266.1 | -15.5 | **FAILED** | {"2026": -11.9} |

Classes (frozen): SUPPORTED if net > 0, PF >= 1.05 and t >= 1.0; FAILED if net <= 0; otherwise INCONCLUSIVE.

## Monthly net points per strategy

* 25f0f86c (VWAP): 2026-01 -208, 2026-02 -73, 2026-03 +36, 2026-04 +206, 2026-05 -331, 2026-06 +277, 2026-07 -99, 2026-08 +459
* 8d2ad60b (DIST): 2026-01 -385, 2026-02 +273, 2026-03 -281, 2026-04 +168, 2026-05 +3, 2026-06 +938, 2026-07 -646, 2026-08 +82
* 98df1979 (RET): 2026-01 -25, 2026-02 -133, 2026-03 +106, 2026-04 -197, 2026-05 -5, 2026-06 +334, 2026-07 +189
* 9e4dd7b9 (RET): 2026-01 +411, 2026-02 -207, 2026-03 +717, 2026-04 +492, 2026-05 +491, 2026-06 +979, 2026-07 +154, 2026-08 +234
* 268b0033 (XMKT): 2026-01 -108, 2026-05 +362, 2026-06 -77, 2026-08 -189

## Correlation of daily net P&L

```
25f0f86c  +1.00  +0.11  +0.00  +0.36  -0.16
8d2ad60b  +0.11  +1.00  +0.18  +0.36  -0.01
98df1979  +0.00  +0.18  +1.00  +0.39  +0.04
9e4dd7b9  +0.36  +0.36  +0.39  +1.00  -0.02
268b0033  -0.16  -0.01  +0.04  -0.02  +1.00
```
Worst combined day: -513.2 NQ points.

## Fixed-dollar risk and prop evaluation (frozen policy: $200 per trade in MNQ, daily policy `stop_after_daily_loss_300`, max open risk $400)

* Fixed-risk result: 115 trades, net $-2,724, max drawdown $2,724

* GENERIC_EVAL_EOD: 38 rolling starts; pass 0.00, fail 0.71, incomplete 0.29; median days to pass None, p90 None; funded 60-day survival -
* GENERIC_EVAL_INTRADAY: 38 rolling starts; pass 0.00, fail 0.71, incomplete 0.29; median days to pass None, p90 None; funded 60-day survival -
