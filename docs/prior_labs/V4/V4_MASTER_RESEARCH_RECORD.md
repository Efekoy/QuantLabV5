# QuantLabV4 master research record

Campaign 1, run autonomously 2026-09-23 to 2026-09-25.
Project: `C:\Users\Administrator\Desktop\QuantLabV4`. Sealed vault: `C:\QuantLabV4_Vault`.

## 1. Research objective

Can mechanically executable intraday **NQ** strategies, discovered from NQ and ES 1-minute OHLCV data,
meet all of the following?
* Contain predictive information beyond what a very large search produces by chance.
* Survive sequential out-of-sample testing.
* Remain profitable after realistic costs.
* Produce P&L paths suitable for futures prop-firm evaluations under fixed-dollar risk.

## 2. Data provenance

* NQ: `Quant\data\NQ\nq_continuous_front_1m.parquet`, SHA-256 `63b8f16d…d013e7`, 5,459,797 rows.
* ES: `Quant\data\ES\es_continuous_front_1m.parquet`, SHA-256 `4a5dcac7…6edb2`, 5,633,953 rows.
* Both are Databento continuous front-contract bars, unadjusted, with the highest-previous-session-volume roll rule.
* The source files were never modified. See V4_BOOTSTRAP_REPORT.md.

## 3. Data quality

See V4_DATA_AUDIT.md. DISCOVERY had 0 timestamp, OHLC, tick-grid or volume integrity failures. Findings:
* Volume is single-front-contract volume. It collapses to about 0.4× in the session before each roll.
  Cleaning v1 therefore adds a causal roll-window flag, which masks volume features. No bars were changed.
* Missing minutes are absent rows, not zero-volume rows. The source and V4 session labels agreed on all 11.1M rows.

## 4. Exact partitions

Sessions run 18:00–17:00 New York and are labelled by their end date.

| stage | sessions (NQ) | rows NQ / ES | location |
|---|---|---|---|
| DISCOVERY | 2010-06-08 .. 2018-12-31 (2198) | 2,776,632 / 2,945,493 | project |
| VALIDATION (`CONFIRMATION`) | 2019-01-02 .. 2022-12-30 (1034) | 1,407,095 / 1,407,376 | vault |
| HOLDOUT | 2023-01-03 .. 2025-12-31 (775) | 1,060,967 / 1,060,571 | vault |
| 2026 FORWARD (`SEALED_2026_AUDIT`) | 2026-01-02 .. 2026-08-10 (157) | 214,983 / 220,513 | vault |
| LIVE_FORWARD (`TRUE_FORWARD`) | sessions after 2026-09-25T05:20:01Z | 0 | vault inbox |

## 5. Methodology

The campaign was preregistered before any real result (V4_RESEARCH_PREREGISTRATION.md; freeze `b5247043…`; tag `v4-prereg`).

* **Stage gate.** A one-way stage machine with pinned freezes. Every read went through `load_view`, and the
  hash-chained ledger holds 636 records, all of which verify.
* **Execution.** Next-bar execution, pessimistic same-bar stop/target resolution, and a 1-tick trade-through
  for targets. The fast outcome tables are proven identical to the reference engine.
* **Costs.** $14 (baseline), $9 (moderate) and $26 (stress) per NQ round trip.
* **Search-adjusted inference.** The identical search was replicated on null worlds.

**OS isolation was not active.** All research ran as Administrator. The isolation was software-level:
the stage gate, hash pins, the ledger and a vault ACL restricted to administrators.

## 6. Feature universe

There are 208 causal features in 14 families (V4_FEATURE_CATALOG.md). Every feature, trigger, filter and
symbol passes an automated test that rewrites the future and checks that the past is unchanged.

| code | family |
|---|---|
| RET | returns/price |
| VOL | participation/volume, time-of-day-normalised with 10–120-session causal baselines |
| VWAP | bar-based VWAP approximation |
| PATH | path geometry |
| DIST | return distribution/semivariance |
| JUMP | bipower-variation jumps |
| PERS | persistence and state transitions |
| SYM | symbolic sequences |
| OPEN | overnight/opening |
| XMKT | NQ/ES cross-market |
| CAL | calendar |
| TECH | technical indicators |
| REOPEN | old price events plus new information |
| ML | ridge, tree, gradient boosting and logistic models, walk-forward |

## 7–9. Strategy universe and candidate counts

The universe has **14,083,560 specifications**: 223 triggers × 721 filter combinations × 6 direction
variants × 14 exits, plus SYM (576,360) and ML (1,428).

| family | specifications |
|---|---|
| OPEN | 2.18M |
| VOL | 1.76M |
| PATH | 1.64M |
| RET | 1.45M |
| XMKT | 1.03M |
| REOPEN | 1.03M |
| VWAP | 0.97M |
| DIST | 0.85M |
| PERS | 0.79M |
| JUMP | 0.73M |
| TECH | 0.61M |
| SYM | 0.58M |
| CAL | 0.48M |
| ML | 1,428 |

The ordered-ID fingerprint is `ad3b6d29…`.

## 10. Discovery results (V4_DISCOVERY_REPORT.md)

| measure | count |
|---|---|
| candidates with ≥ 200 trades | 3,841,538 |
| eligible | 77,666 (see note) |
| **passing (t ≥ 3)** | **1,201** |

The global maximum eligible t was 4.48 (REOPEN).

Note: the selection step (s07) re-screened the float32-saved statistics and counted 77,669 eligible. Three borderline candidates flip on float32 rounding. The passing count is 1,201 either way, so no passing or selection decision is affected.

## 11–13. Nulls, calibration and planted edges

* **Null A:** per-minute sign randomisation, independent for NQ and ES.
* **Null C:** the same with joint NQ/ES signs.
* **Null B:** 30-minute time-of-day block resampling, which preserves real paths. It is not edge-free
  inside a block and is reported as secondary.
* **Discovery nulls:** 150 A + 150 C + 40 B, the full preregistered set. The first 65 used the
  pre-optimisation code, and the rest used verified bit-identical optimised code (V4_NULL_PERFORMANCE_PROFILE.md).
* **Calibration** (V4_NULL_VALIDATION_REPORT.md and addendum). Zero-edge worlds were not flagged.
  * Detected strongly: planted momentum (t = 35) and the ES→NQ one-minute lead (t = 6.2).
  * Missed at 1× strength: the volume-conditioned and persistence plants. Both were detected at 2×
    (t = 9.3 and 4.2).
  * Power limit: the chance maximum is about 3.0–4.1, so V4 only resolves edges whose best discovery t is ≳ 5.

## 14–15. Family-level and global search-adjusted evidence (V4_DISCOVERY_NULL_REPORT.md)

**Global:**

| statistic | real | p_A | p_C | decision p (max) | p_B (secondary) |
|---|---|---|---|---|---|
| T_G (max eligible t) | 4.48 | 0.020 | 0.0066 | **0.020** | 0.17 |
| P_G (passing count) | 1,201 | 0.0066 | 0.0066 | **0.0066** | 0.049 |

Null medians and 99th percentiles for P_G: A 24 and 261, C 16 and 187.

**The search beats the primary global null.** It does **not** clearly beat the path-preserving Null B.

**Families:**
* Unadjusted decision p ≤ 0.05 for RET, VOL, VWAP, PATH, JUMP, PERS, OPEN, XMKT, TECH and REOPEN.
* DIST and CAL do not beat their nulls.
* **No family survives Holm adjustment** (smallest adjusted p 0.093).
* The ML p is mechanical: most nulls had no eligible ML candidate, and **ML found nothing** (max t 2.16).
* SYM had 0 passing.

## 16–17. Behavioural clustering and robustness

* The 1,201 passing candidates fall into **114 clusters** (daily P&L correlation ≥ 0.6).
* Representatives, the most robust member of each cluster, are 104 of 114 continuation variants.
* 105 are "broad" under a lenient neighbourhood rule (V4_CLUSTER_REPORT.md).

## 18. Validation 2019–2022 (V4_VALIDATION_REPORT.md, V4_VALIDATION_NULL_REPORT.md)

* **43 of 114** frozen representatives survived.
* The validation nulls averaged 4.5 survivors with a maximum of 18 (100 A + 100 C worlds), so
  **p = 0.0099 (A and C), the resolution floor**.
* POST-HOC drift/time-of-day control: all 43 survivors had positive excess, with a median excess t of 2.0.

## 19. Final cohort (V4_FINAL_SELECTION_REPORT.md)

Frozen at FINAL_COHORT_FREEZE `1708eddc…`, 2026-09-25T05:20:01Z. Status SUPPORTED_COHORT.

| # | id | family | description | exit |
|---|---|---|---|---|
| 1 | Q4-60857891… | VWAP | long when price is ≥ 3σ above the session VWAP, with signed volume aligned, in low volatility | 2× stop, 3R |
| 2 | Q4-9757cb9e… | DIST | continuation after a semivariance imbalance, with ES confirming and the 60-minute trend aligned | 2× stop, EOD |
| 3 | Q4-14478681… | RET | short continuation after a sharp 15-minute drop, with signed volume aligned, in low volatility | 2× stop, T30 |
| 4 | Q4-40aae8a2… | RET | continuation of a strong move from the RTH open, with semivariance aligned, in low volatility | 2× stop, 3R |
| 5 | Q4-c790712e… | XMKT | NQ/ES efficiency disagreement in the first hour when correlation is low | 2× stop, T60 |

* Pairwise daily correlations run from −0.10 to 0.35.
* The cohort is behaviourally concentrated: 4 of 5 are continuation strategies, and 3 of 5 use the
  low-volatility filter.

## 20–22. Fixed-risk, prop and portfolio (V4_PROP_RESEARCH_REPORT.md)

The research profiles are generic, not any firm's rules: $50k account, $3k target, $2k maximum loss,
EOD or intraday trailing, $1k daily limit, 50% consistency. Sizing used MNQ micros with fixed-dollar
risk and the SKIP policy.

* The frozen rule chose **$200 per trade with a stop-after-−$300-day policy**, and an open-risk cap of $400.
* On 2010–2022 this gave 54% pass and 44% fail, a median of 44 days to pass, and 78% 60-day funded survival.

## 23. HOLDOUT 2023–2025 (V4_HISTORICAL_HOLDOUT_REPORT.md; sealed by HOLDOUT_REPORT_FREEZE `470eda93…`)

**Cohort, one NQ contract per member: PASS**, narrowly at the preregistered t ≥ 1.5.
* 1,372 trades, net +5,886 pts ($117.7k), t 1.52, PF 1.13.
* Net at stress cost is +5,063 pts. The maximum drawdown is 2,263 pts.

Strategies:
* **SUPPORTED:** RET short-continuation (t 1.86, PF 1.46) and RET open-continuation (t 1.50, PF 1.25).
* **INCONCLUSIVE:** VWAP (t 0.88) and DIST (t 0.51).
* **FAILED:** XMKT (−352 pts).

Frozen prop system:
* Fixed-risk net +$10,761 on 1,017 trades, with a maximum drawdown of $6,465 (more than 3× a $2k evaluation budget).
* Evaluations: 45% pass, 49% fail.

## 24. Official 2026 forward test (V4_2026_FORWARD_REPORT.md)

The period ran 2026-01-02 to 2026-08-10 (157 sessions). The cohort was frozen before V4 accessed 2026.

**Cohort, one NQ contract per member: PASS.**
* 309 trades, net +3,945 pts, t 1.58, PF 1.27.
* Net at stress cost is +3,760 pts. The maximum drawdown is 1,709 pts.

**Almost all of that came from one strategy.** RET open-continuation made +3,271 pts (t 2.36, PF 2.13,
7 of 8 months positive, **SUPPORTED**). The others: VWAP, DIST and RET short-continuation were
INCONCLUSIVE (all slightly positive), and XMKT FAILED (6 trades, −12 pts).

**The frozen prop system failed.**
* Fixed-risk net was −$2,725 on 115 trades.
* **0 of 38 evaluation starts passed**, and 71% failed.

POST-HOC diagnosis (p01):
* At 2026 volatility the frozen 2× volatility stops (median 85–142 pts) make even one MNQ exceed the
  $200 budget, so the frozen SKIP rule excluded **183 of 309 trades**.
* Those skipped trades carried **+4,923 pts**, while the trades the system could take lost 977 pts.
* The winning strategy had 50 of its 74 trades skipped (+3,346 pts).

This is a mechanical interaction between the frozen sizing and the regime. It was recorded and not repaired.

## 25. LIVE_FORWARD

**WAITING_FOR_DATA.** No NQ/ES session after the freeze exists on this machine. The ingestion and
evaluation commands are in V4_LIVE_FORWARD_PROTOCOL.md.

## 26. Cost sensitivity

* The cohort stays positive at stress cost ($26 per round trip) in the holdout (+5,063 pts) and in 2026 (+3,760 pts).
* Costs are small relative to the per-trade expectancy of these 2×-stop strategies (4.3 pts in the holdout
  and 12.8 in 2026, against 0.7–1.3 pts of cost).
* MNQ commission is an unvalidated placeholder.

## 27–28. Limitations and prior exposure

* OS isolation was not active (Administrator). The raw data folder grants Modify to CodexSandboxUsers.
* The primary nulls remove NQ's upward drift, and many discovery candidates were long-biased. Only a
  POST-HOC drift control addresses this.
* In the holdout, only the RET short-continuation strategy (excess t 2.16) and partly RET open-continuation
  (1.33) show timing information beyond drift and time of day. VWAP, DIST and XMKT do not (excess t ≤ 0.54).
* The real result is not distinguishable from the path-preserving Null B. The evidence is for generic
  intraday continuation structure, not a unique pattern.
* Power: edges with a discovery t below about 5 are not detectable at this search size.
* Three-filter combinations were not searched. There was no economic-event calendar.
* Prop profiles are generic, not verified firm rules.
* Earlier V2/V3 research exposed the researchers to 2019–2026 behaviour. The V4 system itself accessed each
  period only after freezing, as the ledger shows, but the 2026 test is not perfectly researcher-blind.

## 29. Deviations from preregistration (RESEARCH_DECISION_LOG entries)

* **#17** Post-prereg code edits:
  * a memory-light cache;
  * a crash fix for categorical-parameter neighbours (the conservative reading of "adjacent value");
  * post-hoc drift-control reporting in s09.
* **#19** Implementation-only performance optimisation during the null campaign. It was user-requested and
  verified bit-identical on inputs and outputs of four completed worlds.
* The planned validation nulls were 100 + 100, as written in the preregistration.
* Bugs:
  * #1, the bootstrap freeze R1 was superseded;
  * #15, the neighbour crash above;
  * a pinned evaluator (s11) was briefly edited and then restored byte-identically before any read (NOTE entry).

## 30. POST-HOC analyses (never used for any decision)

* Drift/time-of-day controls at validation, holdout and 2026.
* The SKIP/cap/policy decomposition of the prop system (results/posthoc/POSTHOC_DIAGNOSTICS.json).

## 31. Should be retired

* **ML**: nothing found.
* **SYM**: 0 passing.
* **XMKT efficiency-disagreement**: failed in the holdout and in 2026.
* **CAL** and **DIST** as families: they did not beat the null.
* The **"stop after first winner"** daily policy: it destroyed the edge.
* The frozen **$200 fixed-dollar MNQ configuration with 2× volatility stops**: it is unusable at 2026 volatility.

## 32. Appears supported (modestly)

* **Intraday continuation of strong moves in calm regimes, specifically RET open-continuation.** It is
  SUPPORTED in both the holdout and 2026 and carries post-hoc drift-adjusted timing evidence. It is the one
  consistently positive member.
* **RET short-continuation**: SUPPORTED in the holdout and weak in 2026.
* The search as a whole produces more passing strategies than edge-free worlds. The validation survival
  rate far exceeds its null.

## 33. Remaining uncertainty

* The cohort-level passes rest on t ≈ 1.5–1.6, which is marginal, and on one strategy in 2026.
* The effect is not separated from path-preserving nulls.
* Prop viability under realistic risk budgets is unproven: the evaluation pass rate is ≤ 54%, and the
  holdout drawdown is far above $2k.
* LIVE_FORWARD evidence is still missing.

## 34. Freeze hashes (body SHA-256)

| freeze | hash | notes |
|---|---|---|
| V4_BOOTSTRAP_FREEZE | `b10f8c7f0476f2ccf1dd574855ead09673acc66470db161f117d9dc0ca8d79fa` | R1 superseded: `e6327288…` |
| V4_PREREG_FREEZE | `b524704309412a65c879d45e85efb439ed703ac586b748fd55d0dc6cc54f0ac9` | |
| DISCOVERY_FREEZE | `e10e0c0d456bfae76ae482bdf839f044e3307ac53b56bb30abbaf73a30fbe0ff` | |
| CONFIRMATION_FREEZE | `fb67e008ca5d859f24efd101b8b25d90e401941093e96c9c4a741831b7084a9e` | |
| FINAL_COHORT_FREEZE | `1708eddcf919a46daef57cf8b01014f8e196f4e39f20acb08842fb2604b7f307` | 2026-09-25T05:20:01Z |
| HOLDOUT_REPORT_FREEZE | `470eda93ea19e834f4d122a716989ef897cc609ccb87fd1d55658d7df3d572d4` | |

## 35. Git references

| tag | meaning |
|---|---|
| `v4-bootstrap` | bootstrap checkpoint |
| `v4-prereg` | preregistration freeze |
| `v4-pre-optimization` | implementation used for the first 65 null worlds |
| `v4-optimized` | verified-identical optimised implementation used from null world 66 onward |
| `v4-discovery-freeze` | DISCOVERY_FREEZE |
| `v4-validation-freeze` | CONFIRMATION_FREEZE |
| `v4-final-cohort-freeze` | FINAL_COHORT_FREEZE |
| `v4-holdout-sealed` | HOLDOUT_REPORT_FREEZE |
| `v4-campaign1-complete` | this record |

## Verdict

* **Statistically**, V4 found real, search-adjusted intraday structure, mainly continuation of strong
  moves, that survives 2019–2022 far above chance.
* **Out of sample**, the frozen five-strategy cohort was marginally positive in 2023–2025 and 2026. That
  result is driven chiefly by one strategy (RET open-continuation), and two members added little or failed.
* **As a prop-evaluation system under the frozen $200 fixed-dollar policy**, it is **not viable**: 45%
  pass in the holdout, 0% in 2026, with drawdowns far above a $2k budget.
* A realistic prop application would require a new, separately preregistered sizing design. That would
  be a new experiment, and its evidence would have to come from LIVE_FORWARD data.
