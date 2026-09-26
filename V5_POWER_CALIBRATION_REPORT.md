# V5 planning power and archived calibration evidence

**Current role:** planning and historical method evidence only. Fully
synthetic and direct-null market calibration did not clear frozen gates,
so none of the market-null size/power conditions below authorizes or
blocks the revised holdout-confirmation design. No executable adaptive
market-null power estimate is claimed. The primary V5 inference is the
frozen independent validation procedure in
`V5_HOLDOUT_CONFIRMATION_PROTOCOL.md`; limited power yields an honest
`INCONCLUSIVE / UNDERPOWERED` label, never a relaxed validation threshold.
The original calculations and failed-route proposal remain below.

Status: **precalibration implementation / no final freeze**. The updated objective treats 0.01–0.03R as diagnostic, not a freeze blocker. The binding executable grid and acceptance gates are in `V5_PRECALIBRATION_SCIENCE_PROTOCOL.md`; the planning calculations and stream-proxy results below do not authorize real research. The original exact-rule pilot and hierarchical decomposition use synthetic dependent strategy streams, never a V5 market partition or real strategy outcome. Reproduce them with `python research/planning_power.py`, `python -m research.pilot_v5_stream_power --replications 100 --bootstrap-reps 99 --frequencies 100 500 --days 1034 --candidates 120`, and `python -m research.decompose_v5_power --frequencies 100 250 500 --worlds 120 --bootstrap-reps 99 --output reports/V5_HIERARCHICAL_POWER.json`.

## Planning calculation

Let `f` be trades per 252 sessions, `Y` the partition's sessions/252, and `D=1.5` an illustrative variance inflation for clustering. Assume net trade returns have standard deviation `1R`. Then `N_eff=fY/D` and the normal approximation to 80% minimum detectable mean is `(z_critical+0.842)/sqrt(N_eff)` R per trade. The 90% value uses 1.282. This is **not** calibrated power: heavy tails, correlated trades, nonstationarity, search selection, sizing skips, and uncertain true variance can worsen it. The discovery critical value 4.0 is illustrative of a large search, not an observed V5 null cutoff. Later columns use a one-sided 5% single-test critical value 1.645, before multiplicity correction.

| trades/year | discovery 80% | discovery 90% | validation 80% | audit 1 80% | audit 2 80% |
|---:|---:|---:|---:|---:|---:|
| 25 | 0.402R | 0.438R | 0.301R | 0.347R | 0.772R |
| 50 | 0.284R | 0.310R | 0.213R | 0.246R | 0.546R |
| 100 | 0.201R | 0.219R | 0.150R | 0.174R | 0.386R |
| 250 | 0.127R | 0.139R | 0.095R | 0.110R | 0.244R |
| 500 | 0.090R | 0.098R | 0.067R | 0.078R | 0.173R |
| 1000 | 0.063R | 0.069R | 0.048R | 0.055R | 0.122R |

Thus even a 500-trade/year strategy needs about 0.09R in discovery and 0.17R in the short second audit for 80% power under these favorable assumptions. An individual 0.01–0.03R edge is generally beyond reach. At 500 trades/year, a 0.03R edge needs roughly 6,870 effective trades for a *single* one-sided 5% test at 80% power, or about 20.6 years at design effect 1.5; a broad-search threshold needs about 26,000 effective trades, about 78 years. These are order-of-magnitude illustrations. Pooling distinct strategies does not create independent evidence when their trades and discovery choices overlap.

## Exact pre-result calibration

1. Before examining real V5 strategy outcomes, pin the candidate generator, complete adaptive search algorithm, costs, trade/R definition, selection/classification rules, random seeds, and simulator version. Separate a **zero-edge** world generator from planted worlds. Synthetic worlds must retain NQ/ES joint dependence, volume seasonality, session gaps, volatility clusters, roll masks, and missing-minute patterns; verify these properties against DISCOVERY-only structural summaries. Never fit a synthetic generator using later partitions.
2. **Broad conditional map:** create synthetic daily candidate-stream panels at 25, 50, 100, 250, 500 and 1000 trades/year, with realistic shared-day clustering and `D` scenarios 1, 1.5, 2 and 3. On the targeted stream inject expected *net* executable-trade edge `0, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15 R`; include long and short. Run 2,000 independent panel replications per cell through the fixed-library max-t/stepdown and validation rule. Retain all candidate streams in each panel so multiplicity is represented. Report false positives, detection probability, binomial intervals, and conditional MDE80/MDE90. This is **conditional on an already specified candidate** and does not measure whether the adaptive generator finds the mechanism.
3. **Full pipeline check:** run the entire Stage A→B→C algorithm on independent synthetic market worlds, including endogenous expansion and the intended validation simulation. Use 50 zero-edge worlds first and extend to 100 then 200 if the false-positive interval still cannot resolve the gross size gate. Run at least 20 worlds each for four prespecified sentinel plants: event-time continuation at 250/year and 0.05R; change point at 100/year and 0.10R; targeted TAKE/SKIP at 500/year and 0.03R; NQ/ES tail state at 50/year and 0.15R. The full market plant changes conditional *net return* for the causal target after baseline costs, and realized shift is reported. Determine whether the planted family/rule was recovered, not merely whether any unrelated strategy passed. These sentinel probabilities are noisy and are **not** a full-pipeline MDE curve; do not extrapolate the conditional MDE as an end-to-end guarantee.
4. An observed zero-world false positive rate is acceptable only if the one-sided 95% Clopper-Pearson upper bound is at most 0.10 when nominal alpha is 0.05. With only 50 worlds this may be unresolved even at zero false positives; extend the batch rather than treating zero as proof. This is a gross size sanity gate, not proof of exact 5% size. To claim 80% or 90% *conditional* power for a grid cell, its one-sided 95% lower binomial bound must meet that target; otherwise label the estimate uncertain. Report all cells and intervals, including zero detections.
5. On independent null worlds, compare market-surrogate and stream-bootstrap p-value distributions. If type-I error fails the gate, fix the method **before** real discovery results and rerun with fresh seeds. If full-pipeline sentinel power is poor despite conditional power, diagnose candidate-generation failure without using real outcomes. If power is low but size passes, retain thresholds and label affected claims underpowered. No threshold is relaxed to obtain survivors.

The broad panel grid is cheap relative to complete synthetic searches; full worlds are batched and checkpointed. The calibration report must be completed and reviewed before real V5 search begins; this document records the protocol and planning calculation, not fabricated calibration outcomes.

## Conditional synthetic pilot, 2026-09-25 — STOP gate triggered

`reports/V5_STREAM_POWER_PILOT.json` records 100 independently seeded dependent-stream worlds per frequency, 1,034 validation sessions, 120 fixed candidate streams and 99 common-index stationary-bootstrap resamples per world. Opportunity counts cluster by day; the streams contain a persistent common shock, changing volatility, Student-t tails and shared candidate shocks. The plant adds the stated net R per executed opportunity to one prespecified candidate. The actual `quantlab5.v5.inference.fixed_family_inference` max-t and Romano-Wolf stepdown implementation tests it at adjusted p ≤0.05. This is **conditional stream power**, not full 30-family strategy generation, A/B/C selection, or full-market replay.

| Trades/year | 0R exact-spec FP | 0R any-family FP | 0.01R | 0.02R | 0.03R | 0.05R | 0.075R | 0.10R | 0.15R | empirical conditional MDE80 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 100 | 0% | 4% | 0% | 0% | 0% | 1% | 3% | 8% | 28% | >0.15R on tested grid |
| 500 | 0% | 5% | 0% | 0% | 2% | 5% | 18% | 50% | 87% | (0.10R, 0.15R] |

At 500/year, empirical 90% power was **not** reached at 0.15R (87/100); MDE90 is above the tested grid. The planning validation MDE80 at 500/year was 0.067R, so the observed conditional MDE80 is at least ~1.5× and as much as ~2.2× that planning estimate. The 100/year 0.15R detection rate (28%) is also far below the single-test planning expectation at 0.15R. Joint multiplicity, clustered opportunities, serial shocks, volatility variation and heavy tails explain why the independent-trade normal approximation was optimistic. Because 100 worlds give wide binomial intervals and only 99 bootstrap draws were used, the pilot does **not** establish final type-I calibration or precise MDE. The 0R any-family rate of 4–5% is a preliminary observation, not a passed size gate.

This pilot prompted the hierarchical redesign below. Its exact-rule result alone is insufficient to judge whether a correlated plateau or family effect is detectable. The two pilots use different synthetic generators; their absolute power percentages must not be treated as an apples-to-apples before/after comparison.

## Hierarchical power-loss decomposition, 2026-09-25

`reports/V5_HIERARCHICAL_POWER.json` contains 120 independently seeded 1,034-session worlds at each of 100, 250 and 500 approximate trades per year per rule. Each world contains **30 families × four strongly overlapping neighboring rules**, serial common shocks, clustered daily opportunity counts, persistent volatility and Student-t event tails. Four plants are tested separately: a one-rule needle; a 1.0/0.9/0.8/0.7R-strength local plateau; a heterogeneous 1.0/0.75/0.5/0.25R-strength family; and a low-volatility causal regime plateau whose target rule trades only in that state. Effect values are net R per affected event: 0, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10 and 0.15. The same world and bootstrap indices are used across effects, so the within-world power comparison is paired. This is still **fixed-library conditional power**, not adaptive A→B→C discovery or independent validation power.

The table shows detection at 500/year for a 0.03R plant; all entries are percentages of 120 worlds. A = one target HAC test, B = one target centered stationary bootstrap, C = the same target in the 120-rule panel without adjustment, D = Holm on continuous HAC marginal p-values, E = exact-rule Romano-Wolf stepdown, and F = the hierarchical global test followed by adjusted family and neighborhood support. B and C coincide mathematically. The 99-draw bootstrap has minimum marginal p=0.01, so using those marginal p-values for 120-way Holm would make D incapable of rejection; D deliberately uses HAC normal p-values instead.

| Plant | A | B/C | D | E | F global | F family | F neighborhood |
|---|---:|---:|---:|---:|---:|---:|---:|
| Isolated needle | 28.3 | 27.5 | 1.7 | 2.5 | 7.5 | 0.8 | 0.8 |
| Local plateau | 28.3 | 27.5 | 1.7 | 2.5 | 7.5 | 2.5 | 2.5 |
| Heterogeneous family | 28.3 | 27.5 | 1.7 | 2.5 | 7.5 | 2.5 | 2.5 |
| Causal regime | 21.7 | 23.3 | 1.7 | 2.5 | 9.2 | 1.7 | 1.7 |

The large loss from B/C to D/E is **multiplicity**. The target family test loses more when the effect is confined to one rule, heterogeneous across neighbors, or active only in a subset of sessions. At 100/year the one-rule bootstrap detects 0.03R in 10% of worlds and the family detects it in 0–0.8%; at 250/year those figures are 25–27.5% and 0–0.8%. The 500/year one-rule result is only 27.5% for the full-state plants, so **sample size and same-session dependence already limit power before multiplicity**. More trades within correlated sessions do not scale like independent observations. The regime gate reduces its effective opportunity count.

At 500/year, the following shape-specific family support rates show where hierarchical pooling helps. The neighborhood criterion (≥3/4 positive neighboring means and positive family mean in both chronological halves) has the same observed rates in this run; it is a robustness condition, not another independent sample or p-value.

| Net effect per affected event | Needle | Plateau | Family | Regime |
|---:|---:|---:|---:|---:|
| 0R | 0.0% | 0.0% | 0.0% | 0.0% |
| 0.01R | 0.0% | 0.8% | 0.8% | 0.0% |
| 0.02R | 0.0% | 1.7% | 1.7% | 0.0% |
| 0.03R | 0.8% | 2.5% | 2.5% | 1.7% |
| 0.05R | 1.7% | 11.7% | 4.2% | 1.7% |
| 0.075R | 1.7% | 28.3% | 15.8% | 1.7% |
| 0.10R | 3.3% | 50.0% | 28.3% | 5.0% |
| 0.15R | 9.2% | 90.8% | 64.2% | 17.5% |

At 0.15R, the 500/year plateau has 109/120 family detections (90.8%; two-sided exact 95% interval about 84–95%), versus 11/120 for the needle. The 0.03R plateau has 3/120 (2.5%; interval about 0.5–7.1%). This supports a genuine plateau much better than a needle while leaving the small-effect design underpowered.

**Observed MDE80 grid crossings**, not guaranteed detectable effects: at 500/year, exact-rule stepdown crosses 80% somewhere in `(0.10R, 0.15R]` for every shape. Family and neighborhood support cross only for the local plateau, also in `(0.10R, 0.15R]`; the heterogeneous family, needle and regime have MDE80 **above 0.15R on this grid**. At 100 and 250/year, exact, family and neighborhood MDE80 are all above 0.15R on the grid. At 500/year the single-rule bootstrap crosses at `(0.05R, 0.075R]` for full-state shapes, but 98/120 detections at 0.075R have a one-sided 95% lower bound about 75%, so this crossing is uncertain. The plateau's 109/120 at 0.15R has a lower bound about 85%, clearing the 80% benchmark. No end-to-end A→B→C plus validation MDE can be stated, because executable grammar, market-level replay and validation simulation are not yet connected.

The session-level HAC test and properly **day/block-clustered event-mean test have the same null t statistic**: the event-count denominator cancels under the zero-mean null. Event-level rows therefore provide no legitimate power increase here. An independent-event t test is invalid under the simulated same-day shocks: at 500/year its zero-edge rejection rate is 12.5% versus 5.8% for daily HAC and 6.7% for one-rule block bootstrap. The 250/year naive-event rate is 10.0%. Retain sessions as the inferential unit and events as descriptive performance units.

The 120-world zero-edge global rejection rates are 10.0%, 5.8% and 6.7% at 100, 250 and 500/year; the planted target family's false-positive rate is 0/120 at each frequency, but this does **not** measure the chance that *any* family is falsely claimed. An independent larger null-only check is recorded separately in `reports/V5_HIERARCHICAL_NULL.json` below. These finite-world results cannot certify strong FWER under partial nulls or adaptive search.

## Independent zero-edge size check

`python -m research.calibrate_v5_hierarchy_null --frequencies 100 250 500 --worlds 300 --output reports/V5_HIERARCHICAL_NULL.json` used disjoint world and bootstrap seeds, 300 worlds per frequency, the same 30×4 fixed library and 99 resamples. The table gives false rejections per 300 worlds; parenthesized values are one-sided 95% exact-binomial upper bounds on the rate. The family/neighborhood columns concern the **preidentified target family**. Since any hierarchical claim also requires the global gate, the all-null chance of *any* family claim is bounded by the observed global rejection rate, but partial-null strong control has not been established.

| Trades/year | One-rule HAC | One-rule block | Holm exact | Stepdown exact | Global search | Target family | Target neighborhood | Naive independent events |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 16 (8.0%) | 15 (7.6%) | 0 (1.0%) | 0 (1.0%) | 17 (8.4%) | 0 (1.0%) | 0 (1.0%) | 19 (9.2%) |
| 250 | 16 (8.0%) | 17 (8.4%) | 0 (1.0%) | 0 (1.0%) | 16 (8.0%) | 0 (1.0%) | 0 (1.0%) | 33 (14.4%) |
| 500 | 13 (6.8%) | 17 (8.4%) | 1 (1.6%) | 1 (1.6%) | 16 (8.0%) | 1 (1.6%) | 1 (1.6%) | 31 (13.7%) |

The observed global rates are 5.7%, 5.3% and 5.3%; their one-sided upper bounds stay below the preregistered **10% gross size sanity threshold** for this *all-null fixed library*. This does not validate the adaptive market search, later validation, strong FWER with some real families, or the proposed cluster rule with variable neighborhoods. The naive independent-event test shows material inflation at 250 and 500/year. The earlier 100/year global 12/120 result was sampling variability consistent with the larger independent check; no threshold was adjusted.

## Stop decision and remaining implementation

The 0.01–0.03R plants remain poorly detectable even as plateaus at the highest tested frequency. A 0.03R **net** edge at 500 executed trades/year corresponds to 15R/year in expectation before uncertainty and risk-budget skips, a potentially material research target, yet family support was only 3/120 worlds for the plateau. The dominant measured limitations are the number of independent sessions and shared-day dependence for the single-rule test, followed by multiplicity across 30 families/120 rules. Heterogeneous family strength and regime gating further lower family power. Adaptive candidate generation and the shorter 2019–2022 validation can only be assessed after full replay; their power loss is **unknown**, not estimated by this study. The iid normal/HAC and one-rule bootstrap tests in `tests/test_v5_hierarchy.py` match approximate 5% size and 80% theoretical power at a known iid MDE, so the low dependent-stream power is not explained by that basic implementation check. This is not proof that every implementation detail or null is correct.

The later updated objective supersedes the small-edge stop rationale. **STOP remains in force because 0.10R robust effects are insufficiently recovered under the proposed family gate**; see `V5_UPDATED_POWER_GATE_INVESTIGATION.md`. Keep stage `DISCOVERY`; do not run V5 discovery, open validation/audits, or create `v5-prereg`. A corrected outcome-blind structural inventory enumerates 60 A specifications, 220 applicable B variants and at most 57 reachable conditional C slots per run (337 maximum evaluated; 728 IDs across all branches), but it is not executable and cannot establish the final search count after signal-level duplicate audit. Complete market-level surrogate generation, adaptive hierarchy replay and end-to-end discovery-plus-validation MDE remain unavailable.
