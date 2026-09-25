# QuantLabV4 research preregistration (campaign 1)

Frozen, hashed and git-tagged (`v4-prereg`) **before any real DISCOVERY strategy result is computed**.
Up to the freeze, the only computations on real bars were: the structural and data-quality audits
(V4_DATA_AUDIT.md), and one engineering **null** world (per-minute sign randomisation of the real bars,
which contains no directional information), used only to measure runtime and memory.
Machine-readable numbers: `config/prereg_v4.yaml`. The grammar, features, exits and costs are hashed in
the freeze manifest (`freezes/V4_PREREG_FREEZE.json`).

## 1. Question

Can a very large, mechanically defined search over causal NQ/ES 1-minute OHLCV features find intraday
NQ strategies that (a) produce more evidence than the *identical* search run on edge-free worlds,
(b) survive 2019-2022 unchanged, (c) survive the frozen 2023-2025 holdout and the sealed 2026 forward
test, (d) after realistic costs, and (e) fit a ~$2,000-loss-budget futures evaluation account using
fixed-dollar risk?
"NO ROBUST EDGE FOUND" is an acceptable outcome.

## 2. Data, periods, stages

| Period | Sessions | Stage / partition | Use |
|---|---|---|---|
| DISCOVERY | 2010-06-01..2018-12-31 | DISCOVERY | search, nulls, clustering, robustness |
| VALIDATION | 2019-01-01..2022-12-31 | CONFIRMATION | frozen candidates only; survival vs validation null; final selection |
| HOLDOUT | 2023-01-01..2025-12-31 | FINAL_HISTORICAL_HOLDOUT | frozen cohort only; report then seal (HOLDOUT_REPORT_FREEZE) |
| 2026 FORWARD (official V4 forward test) | 2026-01-01..2026-08-10 (NQ) | SEALED_2026_AUDIT | frozen cohort only |
| LIVE_FORWARD | sessions starting after FINAL_COHORT_FREEZE | TRUE_FORWARD | frozen cohort only |

Traded instrument: **NQ** (ES provides information only). Cleaning: `clean_v1_2026-09-23` (no bar changed;
causal roll-window flag masks volume features). The researchers' prior exposure (V2/V3) to 2019-2026 is a
disclosed limitation. The V4 system itself accesses each period only when the stage gate opens it.

## 3. Execution, exits, costs

The rules are inherited from V3 engine v2 and implemented identically in `engine/backtest.py` and
`v4/outcomes.py`, with the equivalence tested. A signal at a bar's close is executed at the next bar's
open. Entries are allowed 09:30-15:30 NY, and every position is flat by 16:00, at a session change or
at a roll. One position at a time per strategy. Same-bar stop and target is resolved as the stop
(pessimistic). A target fills only on a 1-tick trade-through. A gap through the stop fills at the open.

14 exits: stop = m × √10 × stop_scale, rounded up to the tick, with m ∈ {1, 2}. Each stop is paired
with T15 / T30 / T60 / T120 / EOD / 2R / 3R.

Costs per NQ round trip: baseline $14 (0.70 pt), moderate $9, stress $26 (V3-inherited). All discovery
statistics are **net of baseline cost**. Stress must also be net positive to be eligible.

## 4. Feature universe and grammar

`V4_FEATURE_CATALOG.md` lists 208 causal features (incl. 2 base scales) in 14 families, 223 signed triggers, 39 filters
(11 groups), 7 symbolic code sets and 102 ML signal sets. The causality of every feature, trigger,
filter and symbol is tested automatically.

Grammar V4G1 (`quantlab4/v4/grammar.py`):
* RULE = trigger × {cont, rev} × {both, long-only, short-only} × filter combination
  (none, 1 filter, or 2 filters from different groups: 721 combos) × 14 exits.
* SYM = symbolic sequence × {long, short} × 4 exits.
* ML = model × target × feature set × quantile × 14 exits.

**Total: 14,083,560 candidate specifications.** By family: RET 1,453,536; VOL 1,756,356;
VWAP 969,024; PATH 1,635,228; DIST 847,896; JUMP 726,768; PERS 787,332; OPEN 2,180,304;
XMKT 1,029,588; CAL 484,512; TECH 605,640; REOPEN 1,029,588; SYM 576,360; ML 1,428.
Ordered-ID fingerprint: `ad3b6d29aa6e23ad2552b7415676b42bdf0e8b82763dc0bf1df0e6573f7daa5c`.
Three-filter combinations are **not** searched in campaign 1. This is a deliberate breadth limit,
not a result-driven choice.

Symbolic code sets with zero occurrences are counted as specifications, but can never trade.
The report gives both the specification count and the count of candidates with ≥ 200 trades.

## 5. Discovery screen (`quantlab4/v4/screen.py`)

A candidate is **eligible** if it has ≥ 200 trades, ≥ 6 active years, is positive in ≥ 2/3 of its
active years, has both halves of its active years positive, has PF ≥ 1.10, and is net positive at
stress cost. It **passes** if it is eligible and t_net ≥ 3.0.

Discovery PF is never used to rank. The ranking statistic is t_net, and selection additionally requires
null-relative evidence, clustering and robustness.

## 6. Null architecture (`quantlab4/nulls/base.py`) — the SAME search runs on every null world

* **Null A** (primary): every 1-minute bar's move is multiplied by an independent random sign
  (high/low swapped), and each session is re-anchored at its real open.
  * Preserves |returns|, ranges, volatility clustering, time-of-day seasonality, and volume
    together with its link to |moves|.
  * Destroys all directional and serial predictability, as well as the NQ/ES sign co-movement.
* **Null C** (primary): as A, but NQ and ES share the sign at the same minute.
  * Also preserves contemporaneous NQ/ES correlation and common volatility/volume shocks.
  * Destroys temporal directional information, including lead-lag.
* **Null B** (secondary): each 30-minute time-of-day block is taken from a random donor session
  (joint for NQ/ES), with bars carrying their own offsets and volume.
  * Preserves realistic within-block paths.
  * Destroys cross-block and cross-day chronology.
  * **Not edge-free** for effects that live entirely within one block, so it is reported, not decisive.
* A and C cannot contain a tradable edge by construction: every trade stays inside one session, and
  its path is sign-randomised bar by bar.

**Planned worlds: A = 150, C = 150, B = 40.** Seeds: base A 1,000,000, B 2,000,000, C 3,000,000,
plus the world index. Achievable p-value resolution is 1/151 ≈ 0.0066 for A and C, and 1/41 ≈ 0.024 for B.
The engineering world (seed 900001) is **excluded** from inference.

## 7. Inference (`quantlab4/v4/inference.py`)

* Family statistic T_f = max t over eligible candidates in the family. P_f = number of passing candidates.
* Global statistic T_G = max over all families of T_f. P_G = total passing.
* p = (1 + #null ≥ real)/(1 + N) for each null kind.
* A **family beats its null** if max(p_A, p_C) ≤ 0.05.
* The **search beats the global null** if max(p_A, p_C) ≤ 0.05 for T_G.
* Holm-adjusted family p-values are reported as well. The global test is the primary multiplicity control.
* No p-value is reported below the resolution.

## 8. Null calibration before trusting nulls (`V4_NULL_VALIDATION_REPORT.md`)

Synthetic 9-year worlds with the same machinery: 6 zero-edge worlds, plus one planted edge each for
momentum, volume-conditioned, persistence and cross-market (ES leads NQ by one minute).

* Nulls: 12 × A, 4 × C and 4 × B of zero-edge world 1, and 6 × A of each planted world.
* **Pass criteria:**
  1. At most 2 of the 6 zero-edge worlds have p_A(T_G) ≤ 0.10 against the zero-world null distribution.
  2. At least 3 of the 4 planted worlds have T_G above the maximum of their own A-nulls, and the top
     candidate belongs to the planted mechanism's family (VOL/PATH/RET for volume, momentum and
     persistence; XMKT/RET for cross-market). Detection is judged by T_G against the world's own nulls.
* Failure would require fixing the machinery before any real result is computed.

## 9. Clustering, robustness, representatives (`research/s07_discovery_selection.py`)

* Input: all passing candidates, capped at the top 5000 by t. If none pass, the 300 eligible
  candidates with the highest t are used instead.
* Streams: daily net P&L over DISCOVERY.
* Clustering: greedy in descending t, joining a cluster if the correlation with its seed is ≥ 0.60.
* Neighbours: an adjacent trigger parameter, an adjacent exit, the other stop multiplier, or one filter removed.
* Robustness score = fraction of neighbours with t ≥ 1 and net > 0. Broad if ≥ 0.60, needle if < 0.30.
  Needles are reported but not rejected.
* Representative = the member with the highest robustness, ties broken by t.
* **Validation set = up to 300 representatives**, ordered by descending t.

## 10. Validation 2019-2022

* The validation set is run unchanged.
* **Survive:** ≥ 40 trades, mean net > 0, t ≥ 1.5, PF ≥ 1.05, ≥ 2 of 4 years positive, and stress net > 0.
* **Validation null:** the same frozen candidates on 100 A and 100 C null transforms of the 2019-2022 data
  (planned 200 + 200 were reduced to 100 + 100 in this preregistration for compute).
* Survivor-count evidence if max(p_A, p_C) ≤ 0.05.

Implementation notes (frozen):
* Warm-up: features for 2019+ are computed on a market that starts ~130 sessions earlier (the DISCOVERY
  tail), so the causal baselines are initialised. Only trades whose session is 2019-01-01 or later count.
* ML candidates in the validation set are refit ONCE on all DISCOVERY decision bars (same hyperparameters,
  subsample and purge rules) and saved with the discovery freeze. The frozen models are applied unchanged to
  2019-2022. Validation nulls apply the same frozen models to null-transformed validation data.
* Validation-null worlds transform the combined (warm-up + validation) market with Null A / Null C seeds
  base 4,000,000 / 5,000,000 + index.

## 11. Final selection (before 2023 is opened)

* Rank the survivors by pooled DISCOVERY+VALIDATION t.
* Require pooled t ≥ 3.0, at most 5 strategies, at most 2 per family, and pairwise daily P&L
  correlation < 0.5 (greedy in rank order).
* **If the result is empty:** an `UNSUPPORTED_BEST_EFFORT` cohort is formed from the top 3 validation
  representatives by validation t, one per family. It is tested on the holdout and 2026 purely as
  falsification, is not prop-eligible, and is explicitly not a claim of edge.

## 12. Prop protocol (selection data = DISCOVERY + VALIDATION only)

* Sizing: MNQ micro contracts, fixed-dollar risk ∈ {$100, $150, $200, $250}, SKIP if one micro
  contract exceeds the budget.
* Daily policies:
  * none
  * stop after -$300
  * stop after the first winner
  * stop after ±2R
* Profiles (research profiles, not any firm's rules):
  * GENERIC_EVAL_EOD: $50k, target $3,000, max loss $2,000, EOD trailing, daily limit $1,000 (halt),
    consistency 50%, minimum 5 days.
  * GENERIC_EVAL_INTRADAY: identical but with intraday trailing.
* Evaluations start on every session and are capped at 120 days.
* Choose the (risk, policy) that maximises P(pass) − P(fail) on the EOD profile, ties going to the
  lower risk.
* Portfolio: equal risk per strategy, with maximum simultaneous open risk of 2 × risk.
* Only final-cohort strategies that passed the predictive gate are prop-eligible.

## 13. Holdout 2023-2025 and 2026 forward

* No changes of any kind.
* Per strategy:
  * SUPPORTED if net > 0 at baseline, PF ≥ 1.05 and t ≥ 1.0.
  * FAILED if net ≤ 0.
  * INCONCLUSIVE otherwise.
* Cohort PASS if net > 0 at both baseline and stress cost and cohort t ≥ 1.5.
* The holdout report is frozen (HOLDOUT_REPORT_FREEZE) before 2026 opens, and the stage gate enforces this.
* All members are reported, including failures.

## 14. Deviations and post-hoc work

* Any deviation is logged in `ledgers/RESEARCH_DECISION_LOG.jsonl` as DEVIATION, together with its reason.
* Post-hoc analyses are labelled POST_HOC and can never change the frozen cohort.
* A methodological ambiguity is resolved conservatively and logged.

## 15. Calibration outcome recorded at freeze time (before any real DISCOVERY result)

The null calibration (V4_NULL_VALIDATION_REPORT.md) **passed both criteria**, and the second one passed
only technically:
* Detected clearly: planted momentum and the ES→NQ one-minute lead.
* Marginal: the volume-conditioned plant.
* Not detected: persistence.

Consequence, stated in advance: V4 can only distinguish edges whose best candidate reaches
roughly t ≥ 5 in DISCOVERY. The chance maximum over 14.08M specifications is ~3.0–4.1 in edge-free
worlds. A negative V4 result therefore does not rule out weaker true edges.
