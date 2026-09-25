# V4 null validation (synthetic calibration)

The complete V4 search (14.08M specifications, identical code) was run on synthetic 9-year NQ/ES worlds (`quantlab4/v4/synth.py: calibration_world`) and on null transforms of them. No real data is involved. Pass criteria were fixed in V4_RESEARCH_PREREGISTRATION.md section 8.

## Zero-edge worlds vs the null distribution of zero-edge world 1

| world | T_G (global max eligible t) | P_G (passing) | best family | p_A (vs 12 A-nulls of zero world 1) |
|---|---|---|---|---|
| zero_1 | 4.131 | 2 | VOL | 0.077 |
| zero_2 | 3.418 | 5 | VWAP | 0.308 |
| zero_3 | 2.907 | 0 | VWAP | 1.000 |
| zero_4 | 3.370 | 11 | XMKT | 0.462 |
| zero_5 | 3.082 | 1 | TECH | 0.846 |
| zero_6 | 3.130 | 1 | RET | 0.769 |

Null A of zero world 1 (n=12): T_G min 2.999, median 3.361, max 3.756; P_G median 5

Null C of zero world 1 (n=4): T_G min 3.114, median 3.161, max 3.682; P_G median 6

Null B of zero world 1 (n=4): T_G min 3.105, median 3.623, max 4.103; P_G median 31

**Criterion 1 (at most 2 of 6 zero-edge worlds with p_A <= 0.10): 1 -> PASS**

## Planted-edge worlds vs their own A-nulls

| plant | T_G | P_G | best family | max T_G of own A-nulls | detected (T_G > all nulls) | family plausible |
|---|---|---|---|---|---|---|
| momentum | 35.161 | 926824 | PATH | 4.113 (n=6) | True | True |
|  | family max t: {"RET": 33.81, "VOL": 24.77, "VWAP": 17.72, "PATH": 35.16, "DIST": 22.42, "JUMP": 10.52, "PERS": 25.11, "OPEN": 9.38, "XMKT": 29.67, "CAL": 5.83, "TECH": 28.64, "REOPEN": 21.41, "SYM": 15.83, "ML": 26.54} |||||| 
| volume | 3.970 | 10 | REOPEN | 3.661 (n=6) | True | True |
|  | family max t: {"RET": 2.85, "VOL": 3.06, "VWAP": 3.01, "PATH": 2.87, "DIST": 2.87, "JUMP": 2.61, "PERS": 2.82, "OPEN": 2.58, "XMKT": 2.77, "CAL": 2.31, "TECH": 3.01, "REOPEN": 3.97, "SYM": 1.02, "ML": null} |||||| 
| persistence | 3.634 | 7 | REOPEN | 3.632 (n=6) | True | False |
|  | family max t: {"RET": 3.32, "VOL": 2.8, "VWAP": 3.32, "PATH": 2.65, "DIST": 3.0, "JUMP": 2.72, "PERS": 2.64, "OPEN": 2.95, "XMKT": 2.48, "CAL": 2.73, "TECH": 2.89, "REOPEN": 3.63, "SYM": 1.5, "ML": null} |||||| 
| xmarket | 6.227 | 9613 | RET | 3.920 (n=6) | True | True |
|  | family max t: {"RET": 6.23, "VOL": 4.55, "VWAP": 3.67, "PATH": 3.35, "DIST": 4.95, "JUMP": 5.87, "PERS": 4.05, "OPEN": 3.78, "XMKT": 3.52, "CAL": 2.94, "TECH": 4.84, "REOPEN": 5.17, "SYM": 2.27, "ML": null} |||||| 

**Criterion 2 (>= 3 of 4 planted edges detected in a plausible family): 3 -> PASS**

## Verdict: null machinery CALIBRATED ENOUGH FOR INFERENCE

Notes: the zero-edge p-values have coarse resolution (1/13) and only 6 worlds; this is a sanity check of gross mis-calibration, not a precise size estimate. Null B is not edge-free inside a 30-minute block by design.

## Interpretation (written with the results, before any real discovery result)

* Criterion 2 passes only technically. Momentum (t=35) and the ES->NQ one-minute lead (t=6.2 vs own-null max 3.9) are clearly detected. The volume-conditioned plant (3.97 vs own-null max 3.66 from only 6 nulls; a zero-edge world reached 4.13) is at best marginal. The persistence plant is not detected.
* Power limit: with 14.08M specifications the chance maximum of the eligible t-statistic is ~3.0-4.1 in edge-free worlds. V4 can therefore only distinguish edges whose best candidate reaches roughly t >= 5 in DISCOVERY. Weaker true edges are expected to be MISSED; a negative V4 result does not rule them out.
* The null machinery itself behaves as designed (zero-edge worlds are not flagged; strong plants are).
* Addendum: 2x-strength volume and persistence plants were run to separate power from bugs (results/calibration/world_*_x2_*.json) -- see the addendum section appended below when complete.
