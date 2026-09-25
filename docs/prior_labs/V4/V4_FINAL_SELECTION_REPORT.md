# V4 final selection report (written before 2023 was opened)

Status: **SUPPORTED_COHORT**. Eligible: the 43 validation survivors (validation null p = 0.0099). Frozen rule: rank by pooled DISCOVERY+VALIDATION t; accept if pooled t >= 3.0, at most 2 per family, and pairwise daily-P&L correlation < 0.50 with every strategy already accepted; stop at 5. The first 5 ranked survivors were all accepted.

| id | family | trigger | variant | filters | exit | validation n | validation t | validation PF | pooled n | pooled t |
|---|---|---|---|---|---|---|---|---|---|---|
| Q4-60857891da97d59c25f0f86c | VWAP | VWAP:dist_cross:anchor=glx,thr=3.0 | cont_long | sgnvol_aligned, volreg_low | S2_R3 | 317 | 3.47 | 1.69 | 812 | 4.25 |
| Q4-9757cb9ee92c11b68d2ad60b | DIST | DIST:semi_cross:W=30,thr=0.7 | cont_both | es_confirms, trend60_aligned | S2_EOD | 921 | 3.29 | 1.36 | 2722 | 4.20 |
| Q4-14478681d690cde198df1979 | RET | RET:retz_cross:H=15,thr=2.0 | cont_short | sgnvol_aligned, volreg_low | S2_T30 | 346 | 3.45 | 1.72 | 853 | 4.20 |
| Q4-40aae8a2c827fb779e4dd7b9 | RET | RET:open_retz_cross:thr=2.0 | cont_both | semi_aligned, volreg_low | S2_R3 | 418 | 3.22 | 1.52 | 1066 | 4.12 |
| Q4-c790712e4f51f6f4268b0033 | XMKT | XMKT:er_disagree:H=15,thr=0.4 | cont_both | corr_low, first_hour | S2_T60 | 147 | 2.99 | 1.94 | 458 | 4.04 |

Daily net-P&L correlations (DISCOVERY+VALIDATION):

```
25f0f86c  +1.00  +0.19  -0.10  +0.35  -0.01
8d2ad60b  +0.19  +1.00  +0.10  +0.35  +0.06
98df1979  -0.10  +0.10  +1.00  +0.12  +0.12
9e4dd7b9  +0.35  +0.35  +0.12  +1.00  +0.12
268b0033  -0.01  +0.06  +0.12  +0.12  +1.00
```

Concentration: 4 of 5 are continuation variants, and 3 of 5 use the `volreg_low` (low-volatility regime) filter. The cohort is therefore largely one behavioural theme, intraday continuation in calm regimes, expressed through different triggers. It is not five independent bets.

Cohort parameters, IDs, exits, costs, sizing, the prop policy and the evaluation rules are frozen in `freezes/FINAL_COHORT_FREEZE.json` (mirror `V4_FINAL_COHORT_FREEZE.json`).
