# V4 DISCOVERY null report (search-adjusted evidence)

The identical 14.08M-specification search was run on **150 Null-A, 150 Null-C and 40 Null-B worlds**, with the preregistered counts and seeds. The first 65 worlds used the pre-optimisation code and the rest used the optimised code, which was verified identical (V4_NULL_PERFORMANCE_PROFILE.md). p = (1 + #null >= real)/(1 + N). Resolution: A/C 1/151 = 0.0066, B 1/41 = 0.024.

## Global evidence (the primary multiplicity control)

| statistic | real | p_A | p_C | p_B (secondary) | decision p = max(p_A, p_C) |
|---|---|---|---|---|---|
| T_G (max eligible t over the whole search) | 4.483 | 0.0199 | 0.0066 | 0.1707 | **0.0199** |
| P_G (number passing t >= 3) | 1201 | 0.0066 | 0.0066 | 0.0488 | **0.0066** |

Null distributions (quantiles 50 / 95 / 99 %):

* Null A: T_G [3.55, 4.11, 4.48]; P_G [24, 120, 261]
* Null C: T_G [3.52, 4.03, 4.34]; P_G [16, 113, 187]
* Null B: T_G [3.96, 4.65, 4.78]; P_G [166, 510, 1532]

**Preregistered decision: the V4 search BEATS the global primary nulls** (decision p = 0.020 for T_G; 0.0066 for P_G, at the resolution limit).

Against the secondary, path-preserving Null B, the real search is **not** distinguishable on T_G (p = 0.171) and is only marginally different on P_G (p = 0.049). Null B keeps the real 30-minute intraday paths and destroys the chronology across blocks and days. Much of the real market's excess over the sign-randomised worlds is reproduced when realistic short-horizon paths are re-ordered at random. The evidence therefore points to generic intraday path structure (continuation within about 30 minutes, plus long drift), not to a specific cross-block pattern.

## Family evidence

| family | max t | p_A | p_C | p_B | decision p | Holm | beats null (unadjusted) | passing | p_A(passing) | p_C(passing) |
|---|---|---|---|---|---|---|---|---|---|---|
| RET | 3.90 | 0.026 | 0.040 | 0.073 | 0.040 | 0.238 | True | 207 | 0.007 | 0.007 |
| VOL | 4.16 | 0.020 | 0.007 | 0.073 | 0.020 | 0.238 | True | 113 | 0.007 | 0.007 |
| VWAP | 3.78 | 0.020 | 0.020 | 0.098 | 0.020 | 0.238 | True | 41 | 0.007 | 0.007 |
| PATH | 4.40 | 0.007 | 0.007 | 0.024 | 0.007 | 0.093 | True | 271 | 0.007 | 0.007 |
| DIST | 3.40 | 0.166 | 0.126 | 0.610 | 0.166 | 0.238 | False | 15 | 0.046 | 0.060 |
| JUMP | 3.64 | 0.007 | 0.026 | 0.293 | 0.026 | 0.238 | True | 28 | 0.007 | 0.007 |
| PERS | 3.70 | 0.007 | 0.020 | 0.024 | 0.020 | 0.238 | True | 27 | 0.007 | 0.026 |
| OPEN | 3.94 | 0.013 | 0.020 | 0.293 | 0.020 | 0.238 | True | 190 | 0.007 | 0.007 |
| XMKT | 3.98 | 0.020 | 0.007 | 0.049 | 0.020 | 0.238 | True | 36 | 0.007 | 0.007 |
| CAL | 3.32 | 0.020 | 0.053 | 0.098 | 0.053 | 0.238 | False | 6 | 0.040 | 0.060 |
| TECH | 3.86 | 0.020 | 0.026 | 0.122 | 0.026 | 0.238 | True | 68 | 0.007 | 0.007 |
| REOPEN | 4.48 | 0.007 | 0.007 | 0.049 | 0.007 | 0.093 | True | 199 | 0.007 | 0.007 |
| SYM | 2.74 | 0.046 | 0.020 | 0.073 | 0.046 | 0.238 | True | 0 | 1.000 | 1.000 |
| ML | 2.16 | 0.033 | 0.013 | 0.024 | 0.033 | 0.238 | True | 0 | 1.000 | 1.000 |

Notes (an honest reading):
* **No family survives Holm adjustment** (the smallest adjusted p is 0.093). The 0.05 'beats null' flags are unadjusted, and the families overlap.
* **ML**: 121 of 150 A-nulls and 118 of 150 C-nulls had NO eligible ML candidate, so the ML family p (0.033) is mechanical. The real ML maximum (t = 2.16, 0 passing) is not evidence of an ML edge. ML found nothing.
* **SYM**: max t 2.74 with 0 passing. The small p reflects slightly higher eligible maxima than typical nulls, not a usable edge.
* DIST and CAL do not beat their nulls.
* The families overlap strongly. The same continuation behaviour appears in RET, PATH, REOPEN, OPEN and TECH triggers, so the family p-values are not independent evidence.
