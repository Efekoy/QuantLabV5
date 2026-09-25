# QuantLabV2

A clean research system for finding **any** profitable, mechanically definable
**intraday** strategy on **NQ** and **ES** 1-minute bars (2010–2026).

> **DISCOVERY SHOULD DISCOVER. UNSEEN DATA SHOULD REJECT.**

It searches a very broad space on 2010–2020: simple entries combined with many
styles of trade management. Every combination that makes money after costs is
frozen exactly as it is. The later years then decide, one at a time, which of
them keep working.

This is research software. Nothing it produces is a recommendation to trade.

---

## 1. The idea in one page

| Stage | Years | What happens |
|---|---|---|
| **Discovery (Stage A + Stage B)** | 2010-06-07 → 2020-12-31 | Search freely. Every specification is tested and stored. |
| **Freeze** | – | **Every** unique strategy with net P&L > 0 after baseline costs is frozen: exact rules, SHA-256, data fingerprints, code commit, cost file. |
| **2021 → 2022 → 2023 → 2024** | one year each | Only the previous stage's survivors run, unchanged. Net > 0 survives. |
| **Final validation** | 2025 | Only 2024 survivors. |
| **Forward** | 2026 | Only 2025 survivors. |

**The only rule at every stage: at least one trade and baseline net P&L > 0.**
There is no minimum or maximum Sharpe, win rate, profit factor, reward-to-risk,
trade count or frequency. There is no drawdown cap, significance test,
robustness cut-off or prop-firm filter. All of these are **reported**, and none
of them **decides** anything.

### No preferred shape

A candidate with a 75% win rate and a 0.5R average winner is as welcome as one
with a 35% win rate and a 3R winner. PF 1.10 at 2,000 trades/year is as welcome
as PF 2.0 at 80 trades/year. Sub-1R targets, breakeven stops, trailing stops,
partial exits, runners and plain time exits are all searched and all kept when
profitable. The unseen years decide which shapes persist.

### Why every profitable candidate is kept

A search that returns "the best backtest" picks the luckiest result. Here, if 5
strategies are profitable, 5 are frozen; if 20,000 are, 20,000 are frozen. The
main output is the funnel, Discovery → 2021 → … → 2026. Failures are never
deleted: each is kept with the stage where it failed.

### How to read the funnel honestly

Survivors do not prove anything on their own. On random-walk synthetic data
with **no edge at all**, some candidates still survive several "unseen" years
by chance. The dashboard shows a **coin-flip reference** beside every stage: how
many would remain if each year were a coin toss. A cohort far above that line
for several years is interesting. One that follows it down is what luck looks
like.

---

## 2. Data

`config/data_paths.yaml` points, **read-only**, at the existing files (nothing is
copied):

```
NQ: C:/Users/Administrator/Desktop/Quant/data/NQ/nq_continuous_front_1m.parquet
ES: C:/Users/Administrator/Desktop/Quant/data/ES/es_continuous_front_1m.parquet
```

- **Canonical schema:** timestamp (UTC, bar start), open, high, low, close,
  symbol. Volume is never used or fabricated.
- **Timezone:** all session logic runs in America/New_York; DST is handled by
  the timezone database. A CME session runs 18:00 → 17:00 and is named by the
  date it ends.
- **Contract rolls:** the files are unadjusted front-month data with a contract
  column. No return, level, gap or position ever crosses a roll.
- **Integrity:** duplicates, out-of-order rows and bad OHLC raise an error and are
  **never repaired silently**. `python -m quantlab data-check` prints the full
  report.

### The guardrail

Strategy code never receives the full 2010–2026 frame. Each consumer asks for a
**window**, and the loader pushes the date filter into the Parquet read, so later
rows never reach memory. Arrays are read-only.

- Discovery (both stages) can only read sessions up to 2020-12-31.
- An unseen year needs a **permit**, which only `validate --year Y` issues, and
  only for the next year in the sequence. It includes 30 days of *earlier*
  warm-up, which is never traded.
- A 2021 run cannot see 2022. Non-official experiments, such as the smoke test,
  can never read past 2020.

---

## 3. Costs — `config/costs.yaml`

Round trip = commission × c_mult + 2 × slippage ticks × tick value × s_mult.
Approved for the first official campaign (`costs_v2_approved_2026-09-21`):

| Scenario | Formula | NQ ($5 tick) | ES ($12.50 tick) | Role |
|---|---|---:|---:|---|
| Gross | 0 | $0 | $0 | diagnostic |
| **MODERATE_COST** | $4 + 0.5 tick/side | $9.00 | $16.50 | diagnostic → `COST_SENSITIVE_WATCHLIST` |
| **BASELINE** | $4 + 1 tick/side | **$14.00** | **$29.00** | **OFFICIAL qualification** |
| Stress | $6 (1.5×) + 2 ticks/side | $26.00 | $56.00 | diagnostic |

A candidate enters the official cohort only if **baseline** net P&L > 0.
Strategies profitable at MODERATE cost but not at baseline are preserved in a
separate `results/main/watchlist/COST_SENSITIVE_WATCHLIST.parquet`. They are
never mixed with the frozen cohort and never validated automatically.

**Partials and runners** are fractions of one normalised unit. Commission is one
round trip for the unit. Slippage is charged on the full unit at entry, and each
exit leg pays its own proportional exit slippage. Together that is exactly one
round trip per trade, not one per leg (`CostModel.trade_cost`, tested). Reports
show the first-leg P&L, the runner P&L, the total P&L and the total execution
cost. After the freeze, costs may not change.

---

## 4. Execution rules (conservative, never relaxed)

**Entries and exits**
- A signal is decided at the **close** of a bar. The earliest fill is the
  **next bar's open**, in the same session and contract.
- Rolling levels exclude the current bar. Higher-timeframe bars exist only after
  they have closed.
- Stops are rounded **away** from the entry to the tick grid, and so are targets.
  Both are the conservative direction.
- **R = the initial risk** = |entry − initial stop| after rounding.
- Time exits fill at the close of the last bar of the holding period. Every
  position is closed at the last bar before 16:00, or earlier at a session or
  contract end.

**Profit targets need a 1-tick trade-through (engine v2).** A resting target
(fixed, sub-1R, partial, runner, gap-fill) counts as filled only when a bar
trades at least **1 tick beyond** it. A touch is not a fill, because a real limit
order may not be reached in the queue. It then fills at the target price, never
better. Time, session and opposite-signal exits are market exits and are
unaffected.

**Inside one 1-minute bar (only OHLC is known, not the path)**

| Situation | Baseline ("pessimistic") | Recorded as |
|---|---|---|
| Bar opens beyond the stop | exit everything at the **open** (worse) | stop |
| Bar opens beyond a target | fill at the **target**, never better | target |
| Stop touched **and** a target traded through | the **stop** is assumed first | `ambiguous_bars` |
| Breakeven trigger reached **and** the bar also trades back to the entry | assume the trigger came first and the remainder was **stopped at breakeven** | `be_ambiguous_trades` |
| Breakeven trigger on the entry bar itself | the opening print *is* the entry and came first, so only a trade strictly beyond the entry counts as a return | – |
| Trailing stop | recomputed at each bar **close** from data up to that bar, applied from the **next** bar, only ever tightens (an executable "update once per minute" rule with no intrabar ambiguity) | trailing_stop |

`ambiguity_policy: optimistic` exists only for sensitivity checks. The baseline
is pessimistic and is tested (`tests/test_management.py`).

**A breakeven exit is a small net LOSS:** the price P&L is zero but costs are
still paid. It counts as a loss in win rate and profit factor.

---

## 5. What is searched

A candidate is

```
ENTRY (instrument, family, entry parameters, direction, window)
  + INITIAL STOP METHOD
  + MANAGEMENT TEMPLATE (targets, breakeven, trailing, partials, runner, time)
```

### 5a. Entry families (the "zoo", 20 families)

| | Family | What it tests |
|---|---|---|
| A | `time_of_day` | Enter at a clock time (19:00 … 15:00), hold. Also the engine's sanity check. |
| B | `momentum` | N-bar move beyond ±z volatility units (RTH, AM or PM). |
| C | `consecutive_bars` | The bar completing N higher / lower closes. |
| D | `displacement` | A bar with body or range ≥ k × the previous ATR60. |
| E | `rolling_breakout` | Close (or trade) beyond the previous N-bar high/low; the level ends at t-1. |
| F | `failed_breakout` | Pokes through the N-bar high/low, closes back inside. |
| G | `mean_deviation` | Close stretched from the N-bar average or midpoint. |
| H | `range_position` | Close into the top or bottom x% of the prior N-bar range. |
| I | `session_open_distance` | Distance from the Globex or RTH open. |
| J | `prior_session_levels` | Break of, or rejection at, the prior RTH high/low/close/mid. |
| K | `overnight_range` | Break of, or rejection at, the overnight high/low/mid. |
| L | `opening_range` | First close beyond the 5/15/30/60-minute range. |
| M | `gap` | RTH gap: continuation, or a fade with gap-fill targets. |
| N | `candles` | Body, close location, wicks, outside, inside-break (1/5/15 min). |
| O | `compression_expansion` | Breakout from compression; move during expansion. |
| P | `volatility_regime` (tier 2) | Setup only in low, mid or high volatility regimes. |
| Q | `price_structure` | Swing breaks, pullbacks, HH/HL states. |
| R | `multi_timeframe` (tier 2) | Higher-timeframe direction plus a 1-minute trigger. |
| S | `fvg` | Three-candle fair-value gap: create / touch / reject / invert. |
| T | `cross_market` | NQ↔ES relative strength, lead-lag, (non-)confirmation. |

Every family defines an up-type and a down-type event. `continuation` trades
with the event and `reversal` against it; long-only, short-only and both are
separate candidates. Exact definitions are in each family file's docstring.

### 5b. Initial stop methods (`config/management.yaml → stop_methods`)

| Method | Definition |
|---|---|
| `atr` | 0.25 / 0.5 / 0.75 / 1 / 1.5 / 2 / 3 × **ATR(14) of completed 15-minute bars** |
| `points` | fixed points (NQ 5/10/20/40, ES 2/4/8/16). Not scale-free. |
| `signal_bar` | 1 tick beyond the signal bar's low (long) / high (short) |
| `swing` | 1 tick beyond the last **confirmed** 5-minute swing (3 bars each side) |
| `rolling` | 1 tick beyond the lowest low / highest high of the last 15 or 60 bars |
| `range_frac` | 0.5 or 1.0 × the previous 60-bar range |
| `structural` | the family's own level: the broken level (breakout), the other side of the opening range, the prior-day or overnight level, the prior close (gap), the last swing (structure). Reversal trades use the signal bar's extreme. |

Where a stop would be on the wrong side of the entry, that trade is not taken.

### 5c. Management templates (`config/management.yaml → templates`)

| Family | Grid | Example ID |
|---|---|---|
| `time` (no stop) | hold 5/15/30/60/120 min or to 16:00 | `TIME_60` |
| `opposite` (no stop) | exit on the opposite signal, ≤ 240 min | `OPPOSITE_240` |
| `gapfill` (no stop) | target the prior close / half-way | `GAPFILL_FULL` |
| `stop_time` | stop only, time exit 60/120/eod | `STOP_TIME_eod` |
| `rr` | single target **0.25, 0.33, 0.5, 0.75, 1, 1.25, 1.5, 2, 2.5, 3, 4 R** | `RR_0.5R` |
| `be` | move to BE after +0.25/0.5/0.75/1/1.5/2R; target 1/2/3R or none | `BE_0.5R_T2R` |
| `trail_atr` | trail 0.5–3 ATR below the highest high; start 0/0.5/1/1.5/2R | `TRAIL_ATR_1_ACT0.5R` |
| `trail_close_atr` | trail below the highest close | `TRAIL_CLOSE_ATR_1_ACT0R` |
| `trail_nbar` | N-bar low (2/3/5/8/10/15/20); start 0–2R | `TRAIL_NBAR_5_ACT1R` |
| `trail_r` | 0.5–2R below the highest high; start 0–2R | `TRAIL_R_1_ACT1R` |
| `trail_step` | step trail in 0.5R / 1R steps | `TRAIL_STEP_1R` |
| `partial` (curated) | `PARTIAL_A`…`PARTIAL_K` | 50% @ 1R, rest @ 2R, … |
| `runner` (curated) | 50% at +1R, runner to 2/3/4/5R, time, opposite, 2 ATR trail, 10-bar trail, session close | `RUNNER_3R` |

The curated partials and runners, each with an ID and plain-English
description, are defined in `src/quantlab/engine/management.py`:

| ID | Rule |
|---|---|
| PARTIAL_A | 50% at +1R, 50% at +2R |
| PARTIAL_B | 50% at +0.5R, 50% at +1.5R |
| PARTIAL_C | 50% at +1R, then stop to breakeven, rest at +3R |
| PARTIAL_D | 50% at +1R, rest trails 1 ATR |
| PARTIAL_E | 33% at +0.5R, 33% at +1R, 34% at +2R |
| PARTIAL_F | 25% at +1R, 25% at +2R, rest trails 1 ATR |
| PARTIAL_G | 50% at +0.5R, then breakeven, rest at +2R |
| PARTIAL_H | 75% at +0.5R, 25% at +2R |
| PARTIAL_I | 66% at +1R, 34% at +3R |
| PARTIAL_J | 50% at +0.25R, 50% at +1R |
| PARTIAL_K | 50% at +1R, breakeven, rest trails a 5-bar low |
| RUNNER_2R / 3R / 4R / 5R | 50% at +1R, runner to 2/3/4/5R |
| RUNNER_TIME120 / OPPOSITE / ATR2 / NBAR10 / EOD | 50% at +1R, runner exits on time / opposite signal / 2-ATR trail / 10-bar trail / session close |

Stops, targets, BE, trails and partials are **not** Cartesian-multiplied against
each other. Combinations come only from these curated, interpretable templates.

### 5d. Staged discovery (both stages on 2010–2020 only, both before the freeze)

| | What | Size (current config) |
|---|---|---|
| **Stage A** | every entry × plain exits (time / opposite / gap fill) + a core grid (stop 0.5/1/2 ATR × target 0.5/1/2R) | **87,888** candidates (5,732 entries) |
| **Stage B rule** | an entry qualifies if **any** of its Stage A variants made money **before costs** (fixed in `management.yaml` before Stage A runs) | – |
| **Stage B** | qualifying entries × (a) every target/BE/stop-time/partial/runner template × 6 stop definitions, (b) every trailing template × 2 reference stops, (c) every stop definition × 4 R targets | at most **2,926,164** if every entry qualified; the real number is printed after Stage A |

Stage B is **not** an independent experiment. It searches the same discovery
data more deeply, so both stages count toward the search. The freeze manifest
records the Stage A count, the rule, the number of qualifying entries, the
Stage B count and the total.

`python -m quantlab space` prints entries, template counts and both stage sizes
before anything runs.

---

## 6. Metrics

Every candidate reports trades, trades/year, **win rate**, **profit factor**
(net, gross and stressed), gross, net and stressed P&L, average trade, average
winner and loser, win/loss ratio, expectancy (points, $, and R when a stop
exists), max drawdown ($ and points), longest losing streak, hold times,
long/short split, MAE/MFE, exposure, positive months and years.

For managed candidates it also reports **stop method, initial risk** (average
and median points, $), **target R**, average winner and loser in R, **breakeven
rule** with counts moved and stopped at breakeven, the **trailing rule**, the
**partial structure** with first-leg and runner P&L, and same-bar ambiguity
counts.

**Breakeven win rates**
- Theoretical, before costs, for a fixed stop and target: `1 / (1 + target_R)`.
  That gives 0.25R → 80%, 0.5R → 66.7%, 0.75R → 57.1%, 1R → 50%, 2R → 33.3% and
  3R → 25%.
- After costs, at the candidate's median risk: `(1 + cost/risk) / (1 + target_R)`.
- Implied by the realised average winner and loser:
  `|avg loser| / (avg winner + |avg loser|)`.

PF is never capped (`inf` with no losers). R is reported only when a stop
defines the risk.

### Warning flags (descriptive only; they never reject)

`LOW_SAMPLE`, `HIGH_DRAWDOWN`, `PNL_CONCENTRATED`, `ONE_YEAR_DOMINATED`,
`ONE_MONTH_DOMINATED`, `LONG_SIDE_DEPENDENT`, `SHORT_SIDE_DEPENDENT`,
`COST_SENSITIVE`, `THIN_EDGE`, `PARAMETER_CLIFF`, **`ENTRY_CLIFF`**,
**`MANAGEMENT_CLIFF`**, `RECENT_DECAY`, `UNSTABLE_YEARLY_RESULTS`,
`LONG_LOSS_STREAK`, `VERY_HIGH_TURNOVER`, `AMBIGUOUS_FILLS`.

---

## 7. Robustness (discovery data only)

Neighbours are the same strategy with one ordered parameter moved one grid step.
They are split in two:

- **Entry robustness**: lookback, threshold, entry time, …
- **Management robustness**: target R, BE trigger, trail distance and activation,
  hold, stop distance.

Each dimension is labelled **BROAD_PLATEAU** (≥ 75% of neighbours profitable and
their median net ≥ 50% of the candidate's), **MODERATE** (≥ 50%), **NARROW**
(25–50%) or **CLIFF** (< 25%). The labels are separate for ENTRY robustness and
MANAGEMENT robustness.

Reported for each: count, % profitable, median/worst/best neighbour PF and net,
change from the centre, dispersion, a **cliff score** and a **plateau score**.
Candidate pages show separate entry-parameter and management-parameter heatmaps.
A narrow candidate is **flagged, never rejected**. A better neighbour in a later
year never replaces the frozen original.

## 8. Entry edge vs management edge

Every entry gets a class:
- **A_SIMPLE_EDGE**: already profitable with simple (Stage A) management.
- **B_MANAGEMENT_RESCUED**: profitable only with expanded management.
- **C_NOT_RESCUED**: nothing tested makes it profitable.

Every profitable entry also gets a breadth label: **D_MANY_METHODS** (≥ 3
management families and ≥ 25% of variants profitable), **SEVERAL**, or
**E_SINGLE_SPECIFIC** (only 1–2 configurations). Together these separate a
MARKET ENTRY EDGE from EXIT / PAYOFF SHAPING.

**Management uplift:** each BE, trailing, partial or runner candidate is compared
with the same entry and stop under simpler management. For BE the reference is
the same target without BE; for trails it is stop plus hold to the close; for
partials and runners it is a single target at the first partial level.

For every entry, the system records how every management variant did on the
**exact same entries**:
- `management_comparison_by_entry.csv` gives each entry `ENTRY_EDGE_ALONE`
  (profitable with a plain time or opposite-signal exit) or `NEEDS_MANAGEMENT`
  (profitable only with some stop/target/BE/trail/partial structure).
- Each candidate page shows the reference managements side by side for its
  entries (time exit, 0.5R / 1R / 2R, BE at +0.5R, runner to 3R, ATR trail,
  PARTIAL_C). The full list of every variant is in `entries/<entry>.csv`.
- **Breakeven counterfactual:** every breakeven candidate is re-run without the
  breakeven rule, and each trade stopped at breakeven is matched to the same
  entry without it. The comparison is recorded as "would have lost" versus "would
  have won". Breakeven is measured, not assumed to help.

## 9. Duplicates, similarity, transfer

Trade lists are hashed on times, sides and P&L. Specs with identical trades are
**one** candidate, with the rest kept as aliases. Candidate pages list the most
similar candidates by daily P&L correlation and entry overlap. At freeze time,
every candidate is also run unchanged on the other index (discovery years) for
information. Fixed-point stops are skipped because they are not scale-free.

## 10. Freeze and sequential validation

- `freeze`: requires Stage A and Stage B to be complete. It writes
  `candidates.parquet` (spec, hash, all metrics, robustness, BE counterfactual,
  transfer, warnings), `aliases.parquet`, `yearly_discovery.parquet`,
  `FREEZE_MANIFEST.json` and its `.sha256`, makes them read-only, and refuses to
  run twice.
- `validate --year Y`: verifies the hashes and refuses changed costs, sessions or
  code. It refuses any year out of order or already opened, runs the eligible
  cohort unchanged, and keeps every failure.
- `postmortem --year Y`: **not official**; only for years already opened.

## 11. Reports (`results/<experiment>/reports/`)

- **Dashboard (`index.html`)**
  - discovery overview with the full stage disclosure
  - counts by family, instrument and direction
  - funnel with the coin-flip reference
  - **high-win-rate buckets** (60/65/70/75/80/85%+ with median target R, stop,
    PF, trades/yr, net, DD and W/L)
  - **breakeven tables**
  - **trading-style views**: highest PF, highest WR, highest net, lowest
    DD/profit, highest average trade, highest expectancy in R, most positive
    years, broadest plateau, lower-frequency, high-frequency, high-WR,
    asymmetric-R and sub-1R. Each view states its sort key, and none is declared
    best.
  - **entry vs management edge** and how each management family fared
  - the sortable, filterable candidate table with every entry and management
    column. There is no composite score.
- **Candidate pages** show the ENTRY RULE and MANAGEMENT RULE in plain English
  and every metric above, plus:
  - year-by-year results across all opened stages, equity and drawdown curves,
    rolling 12-month figures
  - cost sensitivity
  - same-entry management comparison
  - entry and management robustness with heatmaps
  - breakeven counterfactual and runner split
  - similar candidates, transfer, and the exact frozen spec
- `python -m quantlab describe <ID>` prints the same content as text.

---

## 12. Commands

```bash
python -m quantlab doctor --tests         # dependencies, data, configs, git, test suite
python -m quantlab status                 # phase, stages, next allowed action
python -m quantlab space                  # entries, templates, Stage A and Stage B sizes
python -m quantlab smoke                  # full pipeline on NQ 2017-2020 (never touches 2021+)
python -m quantlab smoke --synthetic      # same on generated no-edge data
python -m quantlab discover --stage A --yes
python -m quantlab discover --stage B     # prints the qualified count and size; add --yes to run
python -m quantlab freeze
python -m quantlab discovery-report      # DISCOVERY_REPORT.md / .html
python -m quantlab validate --year 2021   # then 2022 ... 2026, in order
python -m quantlab report                 # dashboard + 300 candidate pages (--details all)
python -m quantlab describe <ID>
python -m quantlab report --candidate <ID>
python -m quantlab check-causality --instrument NQ    # look-ahead test on real discovery data
python -m pytest
```

## 13. Performance

A Numba kernel walks only the bars where a trade is open. A cheap Numba summary
is computed for every spec, and full metrics only for profitable ones. Signals,
features and stop arrays are shared by every spec that uses them, and bars are
memory-mapped. On this 2-core / 8 GB machine a single worker runs roughly
**100–670 specs/second** on the full NQ 2010–2020 window, depending on trade
count. Stage A (~88k) takes roughly 10–20 minutes. The Stage B worst case
(~2.9M) takes a few hours; the real size is known and shown before it runs.

## 14. Layout

```
config/            research.yaml, management.yaml, search_space.yaml, costs.yaml, sessions.yaml,
                   data_paths.yaml, smoke.yaml (+ *_smoke.yaml)
src/quantlab/
  data/            guarded loader, sessions/DST, causal resampling, split guard, validation
  features/        causal Numba indicators, feature cache (incl. 15-min ATR, confirmed swings)
  engine/          managed.py (management kernel), management.py (stops + template library),
                   execution.py, costs.py, metrics.py, backtest.py (reference kernel for tests)
  strategies/      families A-T, registry, spec + deterministic IDs
  discovery/       staged enumeration, resumable parallel runner, evaluator, dedup, SQL results
  freeze/          immutable freeze + verification
  validation/      sequential stages, funnel, status, postmortem
  robustness/      entry and management neighbourhoods, heatmaps
  diagnostics/     look-ahead detector, execution invariants, flags, BE counterfactual,
                   cost sensitivity, similarity, transfer
  reporting/       dashboard, analyses, candidate pages, describe
tests/             the tests for the tester
results/<experiment>/  discovery/ frozen/ stages/<year>/ robustness/ postmortem/ reports/
```
