# V5 synthetic holdout-confirmation architecture study

Status: **research design experiment, not a preregistration change**. No real V5 market partition was read. The existing 2010–2018 discovery / 2019–2022 validation / later-audit architecture remains unchanged. `reports/V5_HOLDOUT_ARCHITECTURES.json` is a paired 120-world-per-frequency synthetic dependent-stream study; `reports/V5_HOLDOUT_REPLICATION_500.json` is a disjoint 400-world replication at 500/year. The results test inference architecture around **30 families × four related rule streams**, not executable V5 A/B/C market signals. Do not create `v5-prereg` or start real discovery on this basis.

## Design and boundaries

Each synthetic world has 2,160 discovery sessions (approximately June 2010–December 2018) and an **independently generated** 1,008-session validation panel (approximately 2019–2022). The generator has clustered opportunities, persistent volatility/common shocks, Student-t event tails and overlapping neighboring rules. Plants of 0, 0.05, 0.075, 0.10 and 0.15 net R per affected event are applied as an isolated needle, local plateau, heterogeneous family and causal-regime effect. No event is treated as an independent inference row; tests use common-calendar daily streams. Independent null-reference worlds (199 for the main study, 399 for replication) preserve the joint rule dependence and calibrate the max/stepdown family statistics. The main planted worlds use disjoint seeds.

The deterministic **discovery nomination screen** requires at least 120 events for the median neighboring rule, positive mean R for three of four neighbors, positive family mean in each chronological half, and positive family mean after an additional illustrative 0.02R/event stress-cost increment. It picks the daily-path medoid as representative, tie by ID. The original simulation merged representatives in later canonical families with discovery-path correlation ≥0.85 into an earlier representative. The screen has since been corrected to annotate correlation **without removing a qualifier**. Thus the numerical results below are historical planning results from the earlier code, not recalibrated results under the corrected no-cap implementation. `tests/test_v5_holdout.py` now verifies that correlated qualifiers all nominate. This screen uses no validation outcome and makes no statistical confirmation claim. It is a provisional stream-level screen; actual V5 economic costs, MNQ coverage and executable behavior still need implementation.

The **current-gated proxy** adds an all-library discovery global-max gate and adjusted family gate before the frozen representative receives a Holm validation test. The **holdout-confirmation** options drop those discovery significance gates and apply Holm or common-null-world Romano-Wolf stepdown to only the frozen representative hypotheses. BH and BY FDR variants use frozen representatives; BH requires appropriate dependence assumptions, while BY is conservative under arbitrary dependence. FDR controls the *expected false-discovery proportion*, not the probability of any false survivor, and is not adopted here. The **hierarchical holdout** option tests the frozen four-rule daily family mean with joint stepdown across nominated families, then requires the medoid's own one-sided holdout p ≤0.05. The individual check prevents a family edge in a different neighbor from being described as confirmation of a null medoid. All variants use α=0.05; none lowers it to gain power.

## Paired 120-world power comparison

Each cell is the end-to-end probability that the planted family is nominated, a **truly affected** representative is frozen, and that representative survives the indicated independent holdout procedure. This is end-to-end for the **synthetic stream proxy**, not for executable Stage A→B→C market search. The table uses the current-gated proxy, Holm holdout, and hierarchical holdout; the JSON includes joint stepdown, BH and BY for every cell.

| Trades/year | Shape | Effect | Current proxy | Holm holdout | Hierarchical holdout |
|---:|---|---:|---:|---:|---:|
| 100 | Plateau | 0.05R / 0.075R / 0.10R / 0.15R | 0.0 / 0.0 / 6.7 / 41.7% | 5.0 / 14.2 / 25.0 / 54.2% | 4.2 / 12.5 / 24.2 / 55.8% |
| 250 | Plateau | 0.05R / 0.075R / 0.10R / 0.15R | 4.2 / 15.8 / 41.7 / 77.5% | 10.0 / 33.3 / 49.2 / 77.5% | 11.7 / 34.2 / 52.5 / 82.5% |
| 500 | Plateau | 0.05R / 0.075R / 0.10R / 0.15R | 3.3 / 24.2 / 62.5 / 98.3% | 23.3 / 46.7 / 70.8 / 98.3% | 27.5 / 49.2 / 75.8 / 100.0% |
| 500 | Heterogeneous family | 0.05R / 0.075R / 0.10R / 0.15R | 0.0 / 6.7 / 23.3 / 65.8% | 10.8 / 24.2 / 45.8 / 69.2% | 11.7 / 22.5 / 43.3 / 76.7% |
| 500 | Causal regime | 0.05R / 0.075R / 0.10R / 0.15R | 0.0 / 0.0 / 0.0 / 4.2% | 1.7 / 5.0 / 9.2 / 20.0% | 3.3 / 6.7 / 10.8 / 27.5% |
| 500 | Isolated needle | 0.05R / 0.075R / 0.10R / 0.15R | 0.0 / 0.0 / 0.0 / 0.0% | 0.0 / 0.0 / 0.0 / 0.0% | 0.0 / 0.0 / 0.0 / 0.0% |

The 100/250-year needle, family and regime rows are in the JSON. Needle recovery is intentionally poor because a medoid of four nearby rules usually does not choose the sole affected specification. The regime screen also struggles because the gated rule is not the center of its broader neighborhood. Those are mechanism-selection limitations, not validation-test power alone.

The **independent 400-world replication at 500/year** found 0.10R plateau survival of 68.0% current proxy, 74.0% Holm, 73.8% joint stepdown, 74.0% BH, 69.8% BY and **77.3% hierarchical holdout**. The last is 309/400 with a two-sided exact 95% binomial interval of about **72.8–81.3%**; its one-sided 95% lower bound is about 73.5%. Nomination occurred in 99.5% of planted plateau worlds. The redesigned architecture improves recovery, but **reliable ≥80% recovery is not established**. At 0.05R and 0.075R, hierarchical holdout recovery was 24.5% and 48.0%; at 0.15R it was 98.5%. No 0.01–0.03R run was needed for this revised go/no-go target.

| 500/year replication plant | Hierarchical holdout 0.05R | 0.075R | 0.10R | 0.15R |
|---|---:|---:|---:|---:|
| Needle | 0.3% | 0.0% | 0.0% | 0.0% |
| Plateau | 24.5% | 48.0% | 77.3% | 98.5% |
| Heterogeneous family | 10.8% | 26.8% | 41.3% | 78.8% |
| Regime | 1.5% | 4.5% | 10.5% | 25.8% |

## Error rates and frozen hypothesis counts

At 500/year in the 400-world independent replication, the all-null discovery screen froze a mean **3.47 representative hypotheses** per world out of 30 possible families. Its confirmatory false-survivor results were:

| Validation procedure | Any false survivor, all-null | Mean false survivors, all-null | Mean FDP, 0.10R plateau partial-null |
|---|---:|---:|---:|
| Current-gated proxy + Holm | 0.0% | 0.000 | 0.0% |
| Holm on frozen representatives | 3.5% | 0.045 | 1.7% |
| Joint stepdown on frozen representatives | 3.8% | 0.048 | 1.9% |
| BH FDR on frozen representatives | 3.8% | 0.052 | 2.3% |
| BY FDR on frozen representatives | 2.8% | 0.037 | 1.6% |
| Hierarchical family + individual representative | 3.3% | 0.040 | 1.6% |

The partial-null mean false-survivor counts are 0.037–0.060 across the plateau procedures. Under a 0.10R needle plant, mean FDP for hierarchical holdout was **4.8%**, because some null representatives from the genuine family or other null families can survive even with the individual check. These are empirical estimates under the simulated dependence, not strong-FWER or universal FDR proofs. At 100/year the 120-world all-null false-survivor rates were 5.8% Holm/stepdown/BH and 6.7% hierarchical; 120 worlds cannot resolve whether these modest nominal deviations reflect calibration error. At 250/year they were 3.3% Holm, 4.2% stepdown/hierarchical and 3.3% BH. A full market-level adaptive null and partial-null audit remains mandatory.

## Family statistic comparison

Four dependence-calibrated, max-over-30 family tests were compared: HAC t of the daily mean stream, maximum of four rule t values, average of the top two t values, and median t. At 500/year in the 400-world replication, **0.10R plateau** target-family rejection rates were **55.5%, 61.8%, 59.5% and 54.2%**, respectively. The max detects an isolated 0.10R needle in **58.5%** of worlds, while top-two detects it in **12.5%** and median in **0.3%**. Thus max has the highest plateau power but does not express the desired stable-neighborhood preference. **Top-two is the best exploratory compromise** among these four: it improves on daily mean for plateaus and heterogeneous families while suppressing one-rule needles. It was not used to choose survivors in this study, and selecting it after seeing these results requires a fresh prespecified calibration before adoption. Related rules remained daily streams; their trades were never pooled as independent observations.

## Decision and engine status

The holdout-confirmation architecture is statistically plausible and materially more powerful than redundant discovery significance gates in this stream model. **Do not change the real preregistration yet.** The historical stream-proxy 77.3% planning result does not contain executable A/B/C strategy generation and predates the no-cap correlation correction. The outcome-blind structural inventory is **60 A rules, 220 applicable B variants, at most 57 reachable C interactions per run**, with 728 possible IDs across conditional branches. `quantlab5/v5/duplicate_accounting.py` can fingerprint exact signals and annotate behavioral correlation once market signals exist. The 30 executable V5 signal families and complete adaptive market-level null search runner are still missing; existing null generators and `quantlab5/v5/replay.py` are infrastructure, not a completed replay. No final freeze, commit or tag is justified.

All qualifying representatives advance to validation in the synthetic screen with **no top-N cap**. The user requirement that every actual validation-qualified V5 strategy advance individually into both audits remains a design obligation, not an implemented real-market result. No sealed V5 partition was opened.
