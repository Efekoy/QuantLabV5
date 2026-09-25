# POST-HOC null-survivor extension

Each original A/C validation null world contributes its full set of candidates that pass the frozen validation rule. No top-five selection is applied. Those same candidates run unchanged on independently generated, equivalent 2023–25 and 2026 surrogate markets of the same null kind. The original warm-up and frozen holdout/forward support rule are retained. This comparison was designed after seeing the real five-strategy and all-43 later results; it is post hoc.

The saved validation files contain the full 114-candidate t array and exact survivor count, but not survivor IDs. Where the number with t ≥ 1.5 equals the recorded survivor count, those IDs are mathematically determined because t ≥ 1.5 is mandatory. Every ambiguous world was regenerated and its full frozen validation rule and survivor count reproduced. In total, 187 ID sets follow by exact count proof and 13 worlds were recomputed (including three initial pilot worlds). The per-world derivation is in the machine-readable file.

## Real versus null distributions

| Statistic | Real | A median / 95th / max | A worlds ≥ real | A p (+1) | C median / 95th / max | C worlds ≥ real | C p (+1) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Validation survivors | **43** | 4.0 / 12.0 / 18 | 0/100 | 0.0099 | 3.0 / 13.0 / 16 | 0/100 | 0.0099 |
| Supported in holdout | **16** | 0.0 / 2.0 / 4 | 0/100 | 0.0099 | 0.0 / 2.0 / 4 | 0/100 | 0.0099 |
| Supported in 2026 | **13** | 0.0 / 3.0 / 5 | 0/100 | 0.0099 | 0.0 / 3.0 / 6 | 0/100 | 0.0099 |
| Supported in both | **4** | 0.0 / 1.0 / 1 | 0/100 | 0.0099 | 0.0 / 1.0 / 2 | 0/100 | 0.0099 |
| Distinct dual-supported behaviours | **3** | 0.0 / 1.0 / 1 | 0/100 | 0.0099 | 0.0 / 1.0 / 2 | 0/100 | 0.0099 |

Each p is the within-kind empirical upper-tail value `(1 + worlds >= real) / 101`. These are descriptive post-hoc empirical tails, not preregistered confirmatory p-values. A and C are related null constructions, not 200 independent confirmations. The real four dual-supported IDs form roughly three behaviours under the same descriptive copy screen used in the all-43 report (pooled daily correlation ≥ 0.60 or at least 50% exact holdout entry overlap of the smaller stream).

For scale, supported counts divided by the total number of null-validation survivors give A holdout/forward/both rates of 10.5% / 17.4% / 1.3%; C rates are 11.0% / 15.7% / 2.9%. The corresponding real descriptive fractions are 16/43 = 37.2%, 13/43 = 30.2%, and 4/43 = 9.3%. These fraction comparisons are not count-matched significance tests.

The nulls remove directional predictability and also remove the market's upward drift. Counts of later-supported null survivors are affected by the nulls' much smaller initial validation cohorts (mean about 4.5 versus real 43); this is a full-pipeline benchmark, not a count-matched test of conditional generalization. It does not establish that all four real dual-supported strategies are independent or live-tradable. MNQ sizing and prop evaluation are outside this null comparison.

Full per-world counts, survivor IDs, dual-support IDs, cluster edges, and seeds: `V4_POSTHOC_NULL_SURVIVOR_EXTENSION.json`. Individual world checkpoints: `results/posthoc/null_all_survivors/`. Reproduce with `research/p08_null_survivor_extension.py` and this aggregation script.
