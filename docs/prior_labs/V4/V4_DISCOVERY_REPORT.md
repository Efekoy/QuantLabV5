# V4 DISCOVERY report (sessions 2010-06-08 .. 2018-12-31; NQ traded, ES as information)

Complete preregistered search (V4_RESEARCH_PREREGISTRATION.md, frozen at tag `v4-prereg`). All P&L is net of baseline cost ($14 per NQ round trip).

* Specifications: **14,083,560** (223 triggers x 721 filter combos x 6 variants x 14 exits, plus SYM and ML)
* Candidates with >= 200 trades: **3,841,538**; eligible (every screen condition except t): **77,666**; passing (t >= 3): **1,201**
* Global max eligible t (T_G): **4.483** (REOPEN family)

| family | specifications | >=200 trades | eligible | passing | max t | top-5 t |
|---|---|---|---|---|---|---|
| RET | 1,453,536 | 707,304 | 11,987 | 207 | 3.9 | [3.8956, 3.7932, 3.7752, 3.6924, 3.6805] |
| VOL | 1,756,356 | 597,938 | 10,779 | 113 | 4.16 | [4.1627, 4.1489, 3.9561, 3.7722, 3.7591] |
| VWAP | 969,024 | 388,445 | 5,847 | 41 | 3.78 | [3.7816, 3.6475, 3.5398, 3.426, 3.355] |
| PATH | 1,635,228 | 659,516 | 11,922 | 271 | 4.4 | [4.3965, 4.1393, 4.1104, 4.064, 4.0361] |
| DIST | 847,896 | 202,183 | 5,311 | 15 | 3.4 | [3.399, 3.2578, 3.2329, 3.206, 3.1792] |
| JUMP | 726,768 | 73,325 | 2,386 | 28 | 3.64 | [3.6393, 3.5012, 3.4023, 3.3092, 3.295] |
| PERS | 787,332 | 70,710 | 2,015 | 27 | 3.7 | [3.699, 3.695, 3.6383, 3.5665, 3.5421] |
| OPEN | 2,180,304 | 113,223 | 12,095 | 190 | 3.94 | [3.9377, 3.9377, 3.8305, 3.8067, 3.7478] |
| XMKT | 1,029,588 | 82,426 | 1,723 | 36 | 3.98 | [3.9765, 3.9671, 3.5198, 3.5198, 3.5105] |
| CAL | 484,512 | 65,184 | 1,170 | 6 | 3.32 | [3.3151, 3.3151, 3.1766, 3.1766, 3.1333] |
| TECH | 605,640 | 418,424 | 5,108 | 68 | 3.86 | [3.8619, 3.7857, 3.7053, 3.6437, 3.6405] |
| REOPEN | 1,029,588 | 454,347 | 7,261 | 199 | 4.48 | [4.4827, 4.3856, 4.3717, 4.2705, 4.1831] |
| SYM | 576,360 | 7,122 | 59 | 0 | 2.74 | [2.7435, 2.2148, 2.2038, 2.1796, 2.0508] |
| ML | 1,428 | 1,391 | 3 | 0 | 2.16 | [2.1589, 1.089, 1.0556] |

## Passing candidates by direction variant

{"cont_both": 357, "cont_long": 614, "cont_short": 157, "rev_long": 49, "rev_both": 24}

The passing set is dominated by long-biased variants (cont_long + rev_long). NQ rose strongly over 2010-2018, and the primary nulls remove that drift, so part of the discovery evidence may be drift harvesting rather than timing skill. This is a logged limitation; a POST-HOC drift/time-of-day control is reported at validation. Short-side continuation candidates also pass (up to t ~ 3.96), and drift cannot explain those.

## Interpretation

* Discovery t-statistics are the maxima selected from a 14M-specification search, so on their own they are NOT evidence. The search-adjusted evidence is in V4_DISCOVERY_NULL_REPORT.md.
* Discovery PF was never used for ranking. Timing of the real world (s): {"features": 82.2, "outcomes": 2.8, "rules": 97.7, "sym": 0.4, "ml": 38.2, "total": 221.3}
