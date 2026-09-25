# V4 FINAL HISTORICAL HOLDOUT report (2023-2025)

Sessions 2023-01-03 .. 2025-12-31 (775 sessions). The FROZEN cohort (SUPPORTED_COHORT) was run exactly as frozen in FINAL_COHORT_FREEZE (`1708eddc`, 2026-09-25T05:20:01Z): no tuning, replacement, reselection, filter change, exit change or sizing change. All members are reported, failures included.

## Cohort (each member traded as 1 NQ contract; net of baseline cost)

| trades | net pts | net $ (1 NQ each) | t | PF | expectancy pts | win rate | max DD pts | net pts moderate | net pts stress | preregistered cohort verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 1372 | 5,885.9 | 117,717 | 1.52 | 1.13 | 4.29 | 0.45 | 2,263.1 | 6,228.9 | 5,062.7 | **PASS** |

Cohort PASS rule (frozen): net > 0 at baseline AND at stress cost, AND cohort t >= 1.5.

## Strategies

| id | family | trigger | variant | filters | exit | trades | net pts | t | PF | max DD pts | stress net | class | net by year |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q4-60857891da97d59c25f0f86c | VWAP | VWAP:dist_cross:anchor=glx,thr=3.0 | cont_long | sgnvol_aligned, volreg_low | S2_R3 | 199 | 800.2 | 0.88 | 1.16 | 1,225.5 | 680.8 | **INCONCLUSIVE** | {"2023": 929.2, "2024": 252.4, "2025": -381.5} |
| Q4-9757cb9ee92c11b68d2ad60b | DIST | DIST:semi_cross:W=30,thr=0.7 | cont_both | es_confirms, trend60_aligned | S2_EOD | 639 | 1,686.2 | 0.51 | 1.06 | 2,263.2 | 1,302.8 | **INCONCLUSIVE** | {"2023": 1203.0, "2024": -61.7, "2025": 544.8} |
| Q4-14478681d690cde198df1979 | RET | RET:retz_cross:H=15,thr=2.0 | cont_short | sgnvol_aligned, volreg_low | S2_T30 | 196 | 1,359.5 | 1.86 | 1.46 | 727.0 | 1,241.9 | **SUPPORTED** | {"2023": 144.5, "2024": 990.3, "2025": 224.8} |
| Q4-40aae8a2c827fb779e4dd7b9 | RET | RET:open_retz_cross:thr=2.0 | cont_both | semi_aligned, volreg_low | S2_R3 | 291 | 2,392.1 | 1.50 | 1.25 | 1,138.5 | 2,217.5 | **SUPPORTED** | {"2023": 291.6, "2024": 814.2, "2025": 1286.3} |
| Q4-c790712e4f51f6f4268b0033 | XMKT | XMKT:er_disagree:H=15,thr=0.4 | cont_both | corr_low, first_hour | S2_T60 | 47 | -352.1 | -0.85 | 0.73 | 530.7 | -380.3 | **FAILED** | {"2023": -530.6, "2024": 226.2, "2025": -47.7} |

Classes (frozen): SUPPORTED if net > 0, PF >= 1.05 and t >= 1.0; FAILED if net <= 0; otherwise INCONCLUSIVE.

## Monthly net points per strategy

* 25f0f86c (VWAP): 2023-01 +390, 2023-02 +34, 2023-03 +84, 2023-04 +280, 2023-05 +139, 2023-06 -26, 2023-07 -21, 2023-08 +62, 2023-09 -24, 2023-10 -35, 2023-11 -28, 2023-12 +72, 2024-01 -31, 2024-02 +1, 2024-03 +125, 2024-04 -169, 2024-05 +166, 2024-06 +23, 2024-07 +206, 2024-08 +260, 2024-09 -213, 2024-10 -139, 2024-11 -41, 2024-12 +64, 2025-01 -382, 2025-02 -58, 2025-03 -103, 2025-04 +48, 2025-05 -248, 2025-06 +67, 2025-07 -66, 2025-08 +70, 2025-09 +60, 2025-10 +188, 2025-11 +197, 2025-12 -154
* 8d2ad60b (DIST): 2023-01 +105, 2023-02 -294, 2023-03 +453, 2023-04 -147, 2023-05 +208, 2023-06 +34, 2023-07 -201, 2023-08 +418, 2023-09 +98, 2023-10 +546, 2023-11 +56, 2023-12 -73, 2024-01 +41, 2024-02 -874, 2024-03 -186, 2024-04 +730, 2024-05 +18, 2024-06 -382, 2024-07 +26, 2024-08 -216, 2024-09 -872, 2024-10 +584, 2024-11 +266, 2024-12 +804, 2025-01 -1389, 2025-02 +1098, 2025-03 -293, 2025-04 +1574, 2025-05 -1, 2025-06 -1436, 2025-07 +27, 2025-08 -385, 2025-09 -221, 2025-10 +1103, 2025-11 +246, 2025-12 +222
* 98df1979 (RET): 2023-01 +99, 2023-02 -7, 2023-03 -139, 2023-04 -65, 2023-05 +72, 2023-06 -37, 2023-07 +151, 2023-08 -47, 2023-09 -26, 2023-11 -74, 2023-12 +217, 2024-01 +44, 2024-02 -1, 2024-03 +70, 2024-04 +184, 2024-05 -45, 2024-06 -44, 2024-07 +28, 2024-08 +136, 2024-09 +148, 2024-10 +368, 2024-11 +145, 2024-12 -43, 2025-01 +170, 2025-02 -9, 2025-03 +66, 2025-04 +496, 2025-05 -288, 2025-06 -215, 2025-07 -99, 2025-08 +24, 2025-09 -7, 2025-10 +10, 2025-11 +101, 2025-12 -24
* 9e4dd7b9 (RET): 2023-01 -0, 2023-02 -215, 2023-03 -119, 2023-04 -9, 2023-05 +309, 2023-06 +147, 2023-07 +65, 2023-08 +457, 2023-09 -264, 2023-10 -164, 2023-11 +163, 2023-12 -77, 2024-01 -236, 2024-02 -168, 2024-03 +56, 2024-04 -303, 2024-05 +187, 2024-06 +117, 2024-07 +171, 2024-08 +274, 2024-09 +94, 2024-10 -128, 2024-11 +360, 2024-12 +391, 2025-01 +82, 2025-02 +170, 2025-03 +303, 2025-04 +64, 2025-05 -34, 2025-06 -490, 2025-07 -186, 2025-08 +378, 2025-09 -106, 2025-10 +746, 2025-11 -84, 2025-12 +444
* 268b0033 (XMKT): 2023-03 -16, 2023-04 -114, 2023-05 -272, 2023-06 +151, 2023-07 -120, 2023-10 -77, 2023-12 -83, 2024-01 +35, 2024-02 +153, 2024-03 +19, 2024-05 -22, 2024-06 -53, 2024-07 -10, 2024-09 -116, 2024-10 +75, 2024-12 +146, 2025-10 +98, 2025-12 -146

## Correlation of daily net P&L

```
25f0f86c  +1.00  +0.12  -0.05  +0.35  +0.01
8d2ad60b  +0.12  +1.00  +0.14  +0.24  +0.03
98df1979  -0.05  +0.14  +1.00  +0.06  +0.01
9e4dd7b9  +0.35  +0.24  +0.06  +1.00  +0.07
268b0033  +0.01  +0.03  +0.01  +0.07  +1.00
```
Worst combined day: -495.9 NQ points.

## Fixed-dollar risk and prop evaluation (frozen policy: $200 per trade in MNQ, daily policy `stop_after_daily_loss_300`, max open risk $400)

* Fixed-risk result: 1017 trades, net $10,761, max drawdown $6,464

* GENERIC_EVAL_EOD: 656 rolling starts; pass 0.45, fail 0.49, incomplete 0.05; median days to pass 75.0, p90 92.0; funded 60-day survival 0.82
* GENERIC_EVAL_INTRADAY: 656 rolling starts; pass 0.45, fail 0.50, incomplete 0.05; median days to pass 75.0, p90 92.0; funded 60-day survival 0.82
