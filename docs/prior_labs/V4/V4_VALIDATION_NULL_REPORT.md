# V4 VALIDATION null report

The SAME frozen 114 candidates (rules unchanged; ML candidates use the frozen DISCOVERY models) were run on null transforms of the validation market: Null A (independent per-minute sign randomisation) and Null C (joint NQ/ES), with the preregistered seeds (A 4,000,000+i, C 5,000,000+i). The statistic is the number of survivors under the identical survival rule.

| | survivors |
|---|---|
| real 2019-2022 | **43** |
| Null A (n=100) | mean 4.6, median 4, 95% 12, max 18 |
| Null C (n=100) | mean 4.5, median 3, 95% 13, max 16 |

p_A = 0.0099, p_C = 0.0099; decision p = max = **0.0099** (resolution 1/101). Preregistered decision: survivor count **BEATS** the validation null.

Caveat: the validation nulls, like the discovery nulls, remove NQ's upward drift. For a long-biased candidate set, the null survivor rate is therefore a lower bar than a drift-preserving null would set. The post-hoc drift control in V4_VALIDATION_REPORT.md addresses this.
