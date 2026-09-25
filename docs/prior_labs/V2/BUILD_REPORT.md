# QuantLabV2 build report

*Built 2026-09-21. It shares no code, philosophy or rules with the older `Quant`
project; that project was not modified. Only its two data files are referenced,
read-only.*

> **Read the "Update 2026-09-21: trade management" section at the end first.**
> It supersedes the search-size, exit, test-count and smoke figures of the
> original build described below. The data, guardrail, freeze and validation
> design are unchanged.

## Location

`C:\Users\Administrator\Desktop\QuantLabV2` (`~/Desktop/QuantLabV2`)

## Architecture

| Layer | Modules | Responsibility |
|---|---|---|
| Config | `config/*.yaml`, `config.py` | Periods, costs, sessions, search space. Every file is hashed. |
| Data | `data/loader.py`, `split_guard.py`, `sessions.py`, `resample.py`, `validation.py`, `schema.py`, `fingerprint.py` | Guarded, read-only `DataView` per window. The Parquet filter is pushed down so later rows are never loaded. Permits gate unseen years. NY sessions and DST. Causal higher-timeframe bars. Integrity checks. |
| Features | `features/indicators.py`, `cache.py` | Numba indicators, all causal and roll-aware, plus a memory-budgeted cache. |
| Engine | `engine/backtest.py`, `execution.py`, `costs.py`, `metrics.py` | Numba execution core with conservative fills, centralised costs (gross/baseline/stressed) and all metrics. |
| Strategies | `strategies/base.py`, `registry.py`, `parameters.py`, `families/*` | 20 families, deterministic spec IDs (SHA-256), grids, neighbour positions. |
| Discovery | `discovery/enumerate.py`, `runner.py`, `evaluate.py`, `results.py`, `deduplicate.py` | Resumable, deterministic and memory-aware parallel search. **Every** spec stored in Parquet; trade-list dedup. |
| Freeze | `freeze/manifest.py`, `hashing.py` | Immutable cohort of every unique profitable spec, manifest and hashes, refuses to overwrite. |
| Validation | `validation/sequential.py`, `cohort.py` | One year at a time, cohort shrinks, failures preserved; funnel, status, postmortem. |
| Robustness | `robustness/parameter_neighborhood.py`, `plateau.py` | Grid neighbourhood metrics and heatmaps, discovery data only. |
| Diagnostics | `diagnostics/causality.py`, `execution_checks.py`, `concentration.py`, `cost_sensitivity.py`, `similarity.py`, `transfer.py` | Look-ahead detector, trade invariants, warning flags, cost curve, similarity, cross-instrument transfer. |
| Reporting | `reporting/cohort_report.py`, `candidate_report.py`, `describe.py`, `yearly_report.py`, `html.py`, `tables.py` | Static HTML dashboard, candidate pages, plain-English `describe`. |
| CLI | `cli.py` | `doctor`, `status`, `space`, `discover`, `freeze`, `validate`, `postmortem`, `describe`, `report`, `smoke`, `data-check`, `check-causality`, `similar` |

## Strategy families implemented (20)

A `time_of_day` · B `momentum` · C `consecutive_bars` · D `displacement` ·
E `rolling_breakout` · F `failed_breakout` · G `mean_deviation` ·
H `range_position` · I `session_open_distance` · J `prior_session_levels` ·
K `overnight_range` · L `opening_range` · M `gap` (with gap-fill exits) ·
N `candles` · O `compression_expansion` · P `volatility_regime` (tier 2) ·
Q `price_structure` · R `multi_timeframe` (tier 2) · S `fvg` · T `cross_market`

Exits: time (5/15/30/60/120 min, or hold to 16:00), ATR bracket, opposite
signal, gap fill. Directions: long, short and both, tested separately.
Full search space: **1,938 signal configurations → 46,164 specifications**
(NQ and ES as separate universes).

## Tests: 59, all passing

`python -m pytest` → **59 passed**. Each requirement from the brief is covered:

| Requirement | Test |
|---|---|
| Look-ahead: mutate all future bars, the past must not change | `test_lookahead.py`: every one of the 20 families, every default-grid combination, 2 cut points, time/EOD/bracket/opposite/gap-fill exits |
| Rolling high/low excludes the current bar | `test_engine_timing.py::test_rolling_high_excludes_the_breakout_bar`, `...breakout_family_fires_on_breaking_bar...` |
| Close signal enters at the next open, never earlier | `test_close_signal_enters_at_next_open_never_same_bar` |
| Resampling: HTF never early | `test_resample.py` (3 tests, including a missing last minute) |
| Stop and target in the same bar → pessimistic | `test_same_bar_stop_and_target_is_pessimistic_by_default`; gap-through-stop fills at the open; target never better |
| Costs exact | `test_costs_metrics.py::test_cost_per_trade_exact`, `test_known_trades_gross_and_net` |
| Profit factor, including no losers → inf | `test_profit_factor` |
| Drawdown and streak | `test_drawdown_and_streak` |
| Sessions and DST | `test_sessions_dst.py` (09:30 in winter and summer, Sunday → Monday session, UTC boundaries) |
| Split guard | `test_split_guard.py`: discovery physically excludes 2021; a 2021 view excludes 2022+; permits required; read-only arrays; non-official configs refused |
| Cross-market lag | `test_cross_market.py`: ES future mutation leaves NQ signals unchanged; an ES jump acts only after its own bar closes; missing ES bars are not forward-filled |
| Determinism | `test_pipeline.py::test_determinism...`; 1 worker vs 2 workers give identical results |
| Trade-list dedup | `test_trade_list_dedup...`, `test_equivalent_specs_share_trade_list` |
| End to end | discover → freeze → refusals (re-freeze, re-discover, cost change, wrong year, repeat year) → validate → report → postmortem |
| Execution invariants | every family: no overlaps, no session or roll crossing, entries in window, fills inside bars |
| Known answers | `test_reference.py`: engine vs independent pandas (time of day, breakout) |

On real data, run once during the build (both inside 2017–2020):

- `check-causality` on NQ and ES: **NO LOOK-AHEAD DETECTED** (all 20 families).
- Independent pandas reference on real NQ 2017–2018: time-of-day trades
  **514/514 identical to the tick**, breakout signal bars **14,069/14,069**.

## Smoke campaign result (real NQ; means nothing about unseen data)

Config `config/smoke.yaml`: discovery NQ 2017-01-01 → 2018-12-31, four families
(time of day, momentum, rolling breakout, mean deviation), small grids. The
stand-in "unseen" years are **2019 and 2020, both inside the official discovery
period**, so no year from 2021 onward was touched.

| Stage | Count | Coin-flip reference |
|---|---:|---:|
| Tested | 444 | |
| Unique trade lists | 424 | |
| Gross-profitable specs | 216 | |
| Baseline-profitable specs | 124 | |
| **Frozen (unique)** | **123** | 123 |
| 2019 survivors | 71 | 61.5 |
| 2020 survivors | 13 | 30.8 |

Runtime: about 10 seconds end to end. Dashboard:
`results/smoke/reports/index.html`.

What the smoke run showed working: data loading (real NQ, roll-aware), signals,
execution, costs, metrics, Parquet storage, the preservation of *every*
profitable candidate, dedup (identical "15:00 + 60 min" and "15:00 + hold to
16:00" specs collapsed to one), freezing with hashes, neighbourhood robustness,
NQ → ES transfer, sequential validation with a shrinking cohort, failures kept,
the dashboard and candidate pages.

One example from it: the smoke run's best discovery candidate (NQ 15-minute
momentum, PF 1.61, 100% of neighbours profitable) **failed in 2019** and lost
money on ES. That is the funnel doing its job.

**Synthetic run:** `smoke --synthetic`, random walk with no edge. 83 "profitable"
candidates were frozen and 14 survived both stand-in years. That is why the
dashboard shows the coin-flip reference: survivors alone are not evidence.

## Performance

Full NQ 2010–2020 window: 3,476,185 bars, loaded in about 6 s (memory-mapped
afterwards), roughly **45 specs per second on one worker**. The estimated full
discovery (both instruments, 46,164 specs) is about **20 minutes** on this
2-core / 8 GB machine. `workers: auto` picks 1 here because it is bounded by
free memory.

## Real NQ / ES data: FOUND

| | Rows | Span (UTC) | Notes |
|---|---:|---|---|
| NQ | 5,459,797 | 2010-06-07 → 2026-08-10 | continuous front month, unadjusted, contract column present |
| ES | 5,633,953 | 2010-06-07 → 2026-08-14 | same |

Both are referenced read-only from `C:\Users\Administrator\Desktop\Quant\data\`.
Nothing was copied.

## Assumptions you need to confirm

1. **Costs are placeholders**: $4.00 commission per round trip and 1 tick of
   slippage per side, on full-size E-minis. Baseline is $14.00 (NQ) and $29.00
   (ES) per round trip. Set real values (or micro contract sizes) **before**
   discovery.
2. **Discovery really starts 2010-06-07**, because the files start there. The
   period is about 10.5 years, not 11.
3. **Session windows**: entries 09:30–15:30 New York and flat at 16:00 for
   everything except time-of-day, which may enter from 19:00 (Globex) and is still
   flat by 16:00. A 19:00 entry with "hold to 16:00" therefore spans the overnight
   hours of the *same* CME session. Say so if you want time-of-day limited to
   RTH.
4. **Fills**: next-bar-open market entries; time exits at the scheduled bar's
   close; stops at the stop price or a worse gap open; targets never better than
   the limit; same-bar stop plus target counted as the stop.
5. **Normalisation**: thresholds in ATR60 × √N (ATR of the previous 60 one-minute
   bars). Bracket unit is ATR60 × √30. The volatility regime is the prior 5-session
   RTH range ÷ the prior 60-session range (<0.8 low, >1.25 high).
6. **Validation warm-up**: each unseen year may read 30 calendar days of *earlier*
   data for indicators. Warm-up bars are never traded.
7. **"Unseen" means unseen by this system.** 2021–2026 NQ/ES data was looked at
   extensively in your earlier research. QuantLabV2 cannot search those years,
   but the choice of which families to include was made by people who have seen
   them. Keep that in mind when reading a survivor.
8. **Git**: no global identity is configured, so the repo is initialised and
   staged but **not committed**. See NEXT_COMMANDS §0.

## Exact next command

After setting your real costs in `config/costs.yaml` and making the first commit
(NEXT_COMMANDS §0):

```bash
python -m quantlab doctor --tests
```

---

# Update 2026-09-21: trade management as a research dimension

**Objective changed:** look for **any** profitable mechanical intraday strategy,
with no preferred PF, win rate, reward-to-risk or frequency. Nothing about the
qualification rule changed: at least one trade and baseline net P&L > 0. No
2021+ data was read during this update.

## What was built

| Piece | Where | What it does |
|---|---|---|
| Management kernel | `engine/managed.py` | Numba. Initial stop, up to 3 partial legs with R targets (sub-1R allowed), breakeven by R trigger or after a partial fill, 5 trailing types with activation thresholds, runners, time / opposite-signal / session exits, absolute (gap-fill) targets. Tick-rounded stops and targets (away from entry). Walks only bars in a trade. |
| Stop methods | `engine/execution.py`, `management.yaml` | ATR (15-min ATR14) 0.25–3, fixed points, signal bar, confirmed 5-min swing, rolling 15/60-bar extreme, range fraction, family structural level |
| Template library | `engine/management.py` | 150 managed templates plus 9 plain exits. Parametric families (rr, be, stop_time, 4 trailing types, step trail) and curated `PARTIAL_A…K` / `RUNNER_*`, each with an ID and plain-English description |
| Staged discovery | `discovery/enumerate.py`, `runner.py` | Stage A: every entry × plain exits plus core stop/target. Stage B: qualified entries × expanded management. Rule pre-declared, sizes printed before running, both stages disclosed in the freeze manifest |
| Fast path | `discovery/evaluate.py` | Numba summary (trades, WR, PF, gross/net/stress, max DD, trade-list hash) for every spec; full metrics for profitable ones |
| Robustness split | `robustness/parameter_neighborhood.py` | Entry neighbours versus management neighbours (target R, BE, trail, activation, stop distance). `ENTRY_CLIFF` / `MANAGEMENT_CLIFF` flags |
| BE counterfactual | `diagnostics/breakeven.py` | Every BE candidate is re-run without BE; trades stopped at BE are classified "would have lost" or "would have won" |
| Analyses | `reporting/analysis.py` | High-win-rate buckets (60–85%+), breakeven win rate before and after costs, 13 trading-style views, entry-edge vs management-edge per entry, per-management-family results |
| Reports | dashboard + candidate pages + `describe` | Separate ENTRY RULE and MANAGEMENT RULE, stop, initial risk, target R, BE / trail / partial / runner rules, runner P&L split, same-entry management comparison, entry and management heatmaps |

## Conservative intrabar rules (defined and tested)

- Stop and target in the same bar → the stop is assumed first.
- Breakeven trigger reached and the same bar trades back to the entry → assume
  the remainder was **stopped at breakeven**, counted as `be_ambiguous`.
- On the entry bar, only a trade strictly beyond the entry counts as a return,
  because the opening print is the entry and came first.
- Trailing stops are recomputed at the bar close and apply from the next bar.
- Gap through the stop → exit at the open. Gap through a target → fill at the
  target, never better.
- A breakeven exit is a small net **loss** (costs are still paid).

## Search size (current configuration)

| | Count |
|---|---:|
| Entries (instrument × family × params × direction) | **5,732** |
| Managed templates / plain exits | **150 / 9** |
| Stop variants | 19 per instrument (7 ATR, 4 points, signal bar, swing, 2 rolling, 2 range, structural) |
| **Stage A candidates** | **87,888** |
| **Stage B upper bound** (only if every entry qualified) | **2,926,164** |

Stage B was curated so it stays manageable without dropping any family: all
target/BE/partial/runner templates × 6 stop definitions, every trailing template
× 2 reference stops, and every stop definition × 4 R targets. The real Stage B
size is printed after Stage A, and `--yes` is required to run it.

Throughput on the real NQ 2010–2020 window: about **100–670 specs/second on one
worker**, depending on trade count. Stage A takes about 10–20 minutes; the Stage
B worst case takes a few hours.

## Tests: 72, all passing

In addition to the 59 earlier tests:

- `tests/test_management.py` (13 tests): sub-1R target fill and P&L, tick
  rounding, BE hit next bar, **BE same-bar ambiguity** (pessimistic stops at BE;
  optimistic does not), the entry-bar BE rule, stop+target same bar, N-bar trail
  applied only from the next bar, partial and runner P&L accounting, partial then
  BE, short mirror, gap-fill target, the stop-list shorthand, and **exact
  agreement with the reference kernel** on time, fixed-R and opposite-signal
  exits over 3,000 random bars.
- The look-ahead test now runs every family × a spread of management that uses
  **every stop method and every management feature** (targets, BE, all trail
  types, partials, runners, opposite signal, gap fill).
- The pipeline test runs Stage A → refuses to freeze before Stage B → Stage B →
  freeze → validate.

On real data (inside 2020 only): `check-causality` on NQ and ES with the full
management spread reported **NO LOOK-AHEAD DETECTED**.

During the build, a config-parsing bug was found and fixed: a stop given as a
value list (`atr: [0.5, 1.0, 2.0]`) had silently expanded to the full grid. It
is now covered by a test.

## Smoke results (mean nothing; stand-in "unseen" years 2019–2020 are inside discovery)

| | Real NQ | Synthetic, no edge |
|---|---:|---:|
| Stage A / Stage B tested | 762 / 5,892 | 762 / 5,892 |
| Stage B entries qualified | 98 of 118 | – |
| Frozen (unique profitable) | 1,750 | 561 |
| 2019 survivors (coin-flip reference) | 960 (875) | 107 (281) |
| 2020 survivors (coin-flip reference) | 281 (438) | 22 (140) |

Runtime is about 1 minute for the real smoke and 25 seconds for the synthetic
one.

## Exact next command

After setting real costs and committing (NEXT_COMMANDS §0–2):

```bash
python -m quantlab space
```
