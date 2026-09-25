# QuantLabV2 -- MASTER RESEARCH RECORD of the official experiment

Archived 2026-09-22 12:38 UTC by `tools/archive_official.py`. Every number below was computed by that script from the official result files in `results/main` (copied or hash-referenced in this archive). Nothing here is a recommendation to trade.

Contents: 1 Objective - 2 Data - 3 Engine - 4 Costs - 5 Strategy universe - 6 Correctness tests - 7 Discovery results - 8 Official freeze - 9 Sequential funnel - 10 Final survivors - 11 Stronger subset - 12 Observations - 13 Data-access audit - 14 Limitations - 15 Open questions - Appendix (files)

## 1. Project objective

QuantLabV2 is a research system built to answer one question honestly: *if we search a very broad space of simple intraday trading rules on the past, do any of them keep making money on years they never saw?* Its motto is **DISCOVERY SHOULD DISCOVER. UNSEEN DATA SHOULD REJECT.**

- **Data:** 1-minute OHLC bars (open, high, low, close; no volume) of the E-mini Nasdaq-100 (NQ) and E-mini S&P 500 (ES) futures, continuous front contract.
- **Discovery philosophy:** the discovery period (2010-06-07 to 2020-12-31) is searched as broadly as practical: 20 entry families, three directions, many stops, targets, breakeven rules, trailing stops, partial exits, runners and time exits. There is no preferred shape (a 30% or 85% win rate, a 0.25R or 5R target are all allowed).
- **Every profitable candidate was preserved.** The only discovery rule was: at least one trade AND net P&L > 0 after BASELINE costs. No profit-factor, win-rate, drawdown, frequency or robustness gate was applied. All such measures are descriptive only.
- **Why not pick the best backtest:** the best of millions of backtests is mostly the luckiest one. Picking it bakes the luck into the result. Freezing *every* profitable candidate, and letting later unseen years do the rejecting, makes the selection objective and lets us measure how discovery performance decays.
- **Sequential unseen testing:** after the freeze, the whole cohort was run unchanged on 2021. Only the 2021-profitable candidates entered 2022, and so on through 2025 and the partial 2026. Each year was opened only after the previous year was finished, and a data-access ledger proves the order.

## 2. Data

- **NQ**: `C:/Users/Administrator/Desktop/Quant/data/NQ/nq_continuous_front_1m.parquet` (Parquet, timestamp column `ts_event`, UTC, bar stamped at its START, contract column `symbol`). Opened read-only, never copied or modified.
- **ES**: `C:/Users/Administrator/Desktop/Quant/data/ES/es_continuous_front_1m.parquet` (Parquet, timestamp column `ts_event`, UTC, bar stamped at its START, contract column `symbol`). Opened read-only, never copied or modified.
- Whole-file SHA-256 fingerprints: NQ `63b8f16dd1da0a35f2fdfdc9039686ffc8db0ada84333bfc7cd85f8f28d013e7`, ES `4a5dcac73b45f8097164e1242447fb490e6b2d52b4012cbe1ee3890f2d76edb2` (identical in the freeze and every stage manifest).
- First available bar (both): 2010-06-07 18:00:00-04:00.
- **Last real-market bar used:** ES 2026-08-14 16:59:00-04:00; **NQ 2026-08-10 19:59:00-04:00** -- the NQ file ends four days before the ES file, so the NQ 2026 period is shorter (the NQ file's last session, 2026-08-11, is incomplete: it holds only the evening from 18:00 to 19:59 NY). The overall highest real timestamp read by the official experiment is **2026-08-14 16:59:00-04:00**.
- **Bar frequency:** 1 minute. **Timezone:** all session logic in America/New_York (DST via the tz database). A CME session runs 18:00 to 17:00 and is labelled by the date it ends on.
- **Contract rolls:** each bar carries its outright contract; a change of contract starts a new segment. No return, gap, level, indicator window or position ever spans two segments.

| Period | Sessions | Warm-up read | Last bar read |
|---|---|---|---|
| Discovery | 2010-06-07 .. 2020-12-31 | none (starts at file start) | 2020-12-31 16:59:00-05:00 |
| 2021 | 2021-01-01 .. 2021-12-31 | warm-up from 2020-12-02 | NQ 2021-12-31 16:59:00-05:00; ES 2021-12-31 16:59:00-05:00 |
| 2022 | 2022-01-01 .. 2022-12-31 | warm-up from 2021-12-02 | NQ 2022-12-30 16:59:00-05:00; ES 2022-12-30 16:59:00-05:00 |
| 2023 | 2023-01-01 .. 2023-12-31 | warm-up from 2022-12-02 | NQ 2023-12-29 16:59:00-05:00; ES 2023-12-29 16:59:00-05:00 |
| 2024 | 2024-01-01 .. 2024-12-31 | warm-up from 2023-12-02 | NQ 2024-12-31 16:59:00-05:00; ES 2024-12-31 16:59:00-05:00 |
| 2025 | 2025-01-01 .. 2025-12-31 | warm-up from 2024-12-02 | NQ 2025-12-31 16:59:00-05:00; ES 2025-12-31 16:59:00-05:00 |
| 2026 (partial) | 2026-01-01 .. 2026-12-31 | warm-up from 2025-12-02 | NQ 2026-08-10 19:59:00-04:00; ES 2026-08-14 16:59:00-04:00 |

The warm-up is 30 calendar days of EARLIER data so indicators have history; no trade is scored in it.

## 3. Engine and execution assumptions

- **Next-bar execution:** a signal is known only when its bar closes; the order fills at the OPEN of the next 1-minute bar. Never on the signal bar.
- **1-tick target trade-through:** a profit target fills only if a later bar trades at least one tick BEYOND it (a touch is not a fill). It then fills at the target price.
- **Stops** fill at the stop price, or at the open if the market gaps through it (never better). Stop and target prices are rounded to the tick AWAY from the entry (conservative).
- **Stop-first rule:** if one bar reaches both the stop and a target, the order inside the minute is unknowable, so the stop is assumed to fill first (official `ambiguity_policy: pessimistic`).
- **Breakeven:** once price reaches +X R, the stop moves to the entry price from the NEXT bar. If the trigger bar itself also returns to the entry, the trade is assumed to exit at breakeven. On the entry bar, only a trade strictly beyond the entry counts as a return.
- **Trailing stops** (ATR distance, close-based ATR, N-bar extreme, R distance, R steps) are recomputed at each bar close and apply from the next bar; they only ever tighten. Activation thresholds (e.g. from +1R) are part of the template.
- **Partial exits** split the position into legs (e.g. 50% at 1R, 50% at 2R); after the first leg the remaining stop may move to breakeven if the template says so. Cost = one normalised round trip per trade, with exit slippage charged in proportion to each leg.
- **Runners** take a first partial profit and let the remainder run to a far target, a trailing stop, the opposite signal, a time limit or the session end.
- **Session exits:** every position is flat at the close of the last bar before 16:00 New York. No position crosses a session. Entries only inside the family's window (rth 09:30-15:30, rth_am, rth_pm, or globex 18:00-15:30).
- **Contract rolls:** no position is opened across or held over a roll boundary.
- **One position at a time** per candidate; in `both` mode conflicting long/short signals take no trade.
- **Intrabar ambiguity** is always resolved pessimistically (stop before target, BE before target, gap-through fills at the open).
- Engine version **2**; target trade-through 1 tick; ambiguity policy pessimistic.

## 4. Cost assumptions

Round trip = commission x commission_mult + 2 x slippage ticks/side x tick value x slippage_mult + extra.

| Instrument | View | Commission RT | Slippage | Tick value | Total RT |
|---|---|---|---|---|---|
| NQ | GROSS | $0.00 | 0 tick/side = $0.00 | $5.00 (point $20) | $0.00 |
| NQ | MODERATE_COST | $4.00 | 0.5 tick/side = $5.00 | $5.00 (point $20) | $9.00 |
| NQ | BASELINE | $4.00 | 1 tick/side = $10.00 | $5.00 (point $20) | $14.00 |
| NQ | STRESS | $6.00 | 2 tick/side = $20.00 | $5.00 (point $20) | $26.00 |
| ES | GROSS | $0.00 | 0 tick/side = $0.00 | $12.50 (point $50) | $0.00 |
| ES | MODERATE_COST | $4.00 | 0.5 tick/side = $12.50 | $12.50 (point $50) | $16.50 |
| ES | BASELINE | $4.00 | 1 tick/side = $25.00 | $12.50 (point $50) | $29.00 |
| ES | STRESS | $6.00 | 2 tick/side = $50.00 | $12.50 (point $50) | $56.00 |

**BASELINE determined official profitability** at every stage (`{'metric': 'baseline_net_pnl', 'condition': '> 0'}`). GROSS, MODERATE_COST and STRESS are diagnostics. Cost version `costs_v2_approved_2026-09-21#a27ed5df0c04`.

## 5. Strategy universe

| Family | Grid | Grid points | Directions | No-stop exits |
|---|---|---|---|---|
| time_of_day | entry_time=['19:00', '19:30', '20:00', '20:30', '21:00', '21:30', '22:00', '22:30', '23:00', '23:30', '00:00', '00:30', '01:00', '01:30', '02:00', '02:30', '03:00', '03:30', '04:00', '04:30', '05:00', '05:30', '06:00', '06:30', '07:00', '07:30', '08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00']; window=['globex'] | 41 | long,short | time |
| momentum | lookback=[5, 10, 15, 30, 60, 120, 240]; z=[0.5, 1.0, 1.5, 2.0, 3.0]; mode=['continuation', 'reversal']; window=['rth', 'rth_am', 'rth_pm'] | 210 | long,short,both | time,opposite |
| consecutive_bars | n=[2, 3, 4, 5, 6, 8]; mode=['continuation', 'reversal']; window=['rth'] | 12 | long,short,both | time |
| displacement | measure=['body', 'range']; k=[2.0, 3.0, 4.0, 5.0]; close_strength=['none', 'strong']; mode=['continuation', 'reversal']; window=['rth'] | 32 | long,short,both | time |
| rolling_breakout | lookback=[15, 30, 60, 120, 240]; trigger=['close', 'touch']; mode=['continuation', 'reversal']; window=['rth', 'rth_am', 'rth_pm'] | 60 | long,short,both | time |
| failed_breakout | lookback=[15, 30, 60, 120, 240]; mode=['reversal', 'continuation']; window=['rth'] | 10 | long,short,both | time |
| mean_deviation | anchor=['sma', 'midpoint']; lookback=[15, 30, 60, 120, 240]; z=[0.5, 1.0, 1.5, 2.0, 3.0]; mode=['reversal', 'continuation']; window=['rth'] | 100 | long,short,both | time,opposite |
| range_position | lookback=[15, 30, 60, 120, 240]; edge=[0.1, 0.2, 0.25, 0.33]; mode=['continuation', 'reversal']; window=['rth'] | 40 | long,short,both | time |
| session_open_distance | anchor=['globex_open', 'rth_open']; z=[0.5, 1.0, 1.5, 2.0, 3.0]; mode=['continuation', 'reversal']; window=['rth'] | 20 | long,short,both | time |
| prior_session_levels | level=['high', 'low', 'close', 'midpoint']; event=['break', 'touch']; first_only=[True, False]; mode=['continuation', 'reversal']; window=['rth'] | 32 | long,short,both | time |
| overnight_range | level=['high', 'low', 'midpoint']; event=['break', 'touch']; mode=['continuation', 'reversal']; window=['rth'] | 12 | long,short,both | time |
| opening_range | minutes=[5, 15, 30, 60]; mode=['continuation', 'reversal']; window=['rth'] | 8 | long,short,both | time |
| gap | threshold=[0.1, 0.2, 0.3, 0.5]; mode=['continuation', 'reversal']; window=['rth'] | 8 | long,short,both | time,gapfill |
| candles | timeframe=[1, 5, 15]; pattern=['body_0.6', 'body_0.8', 'close_0.8', 'close_0.9', 'wick_0.5', 'wick_0.66', 'outside', 'inside_break']; mode=['continuation', 'reversal']; window=['rth'] | 48 | long,short,both | time |
| compression_expansion | lookback=[10, 20, 30, 60]; state=['compression_breakout', 'expansion_move']; strength=[1, 2]; mode=['continuation', 'reversal']; window=['rth'] | 32 | long,short,both | time |
| volatility_regime | setup=['mom15_z1', 'mom60_z1', 'dev60_z1.5', 'dev120_z2']; regime=['low', 'mid', 'high']; mode=['continuation', 'reversal']; window=['rth'] | 24 | long,short,both | time |
| price_structure | timeframe=[1, 5]; swing=[2, 3, 5, 10]; event=['swing_break', 'pullback', 'trend_state']; mode=['continuation', 'reversal']; window=['rth'] | 48 | long,short,both | time |
| multi_timeframe | htf=[15, 30, 60]; htf_lookback=[1, 3]; trigger=['with_trend', 'pullback']; ltf_lookback=[5, 15]; z=[1.0, 2.0]; mode=['continuation', 'reversal']; window=['rth'] | 96 | long,short,both | time |
| fvg | timeframe=[1, 5, 15]; min_gap=[0.0, 0.25, 0.5]; event=['create', 'touch', 'reject', 'invert']; mode=['continuation', 'reversal']; window=['rth'] | 72 | long,short,both | time |
| cross_market | kind=['relative', 'lead', 'nonconfirm', 'confirm']; lookback=[5, 15, 30, 60]; z=[0.5, 1.0, 1.5]; mode=['continuation', 'reversal']; window=['rth'] | 96 | long,short,both | time |

- Directions: ['long', 'short', 'both'] (time_of_day: long/short only). Every grid point x direction is one ENTRY specification; **5,732 entry specifications** (1,938 distinct signal configurations), per instrument as printed by `python -m quantlab space`.
- **Initial stop methods:** atr {'mult': [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]}; points {'NQ': [5, 10, 20, 40], 'ES': [2, 4, 8, 16]}; signal_bar {}; swing {}; rolling {'bars': [15, 60]}; range_frac {'frac': [0.5, 1.0]}; structural {}. ATR = ATR(14) of completed 15-minute bars at the signal bar.
- **Target R values** (rr template): [0.25, 0.33, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0]
- **Breakeven rules** (be template): be_R [0.25, 0.5, 0.75, 1.0, 1.5, 2.0] x target [1.0, 2.0, 3.0, 'none']
- **Trailing rules:** trail_atr {'dist': [0.5, 0.75, 1.0, 1.5, 2.0, 3.0], 'act_R': [0.0, 0.5, 1.0, 1.5, 2.0]}; trail_close_atr {'dist': [1.0, 2.0], 'act_R': [0.0, 1.0]}; trail_nbar {'bars': [2, 3, 5, 8, 10, 15, 20], 'act_R': [0.0, 0.5, 1.0, 1.5, 2.0]}; trail_r {'dist_R': [0.5, 0.75, 1.0, 1.5, 2.0], 'act_R': [0.0, 0.5, 1.0, 1.5, 2.0]}; trail_step {'step_R': [0.5, 1.0]}
- **Partial templates:** PARTIAL_A, PARTIAL_B, PARTIAL_C, PARTIAL_D, PARTIAL_E, PARTIAL_F, PARTIAL_G, PARTIAL_H, PARTIAL_I, PARTIAL_J, PARTIAL_K (curated library in `engine/management.py`).
- **Runner templates:** RUNNER_2R, RUNNER_3R, RUNNER_4R, RUNNER_5R, RUNNER_TIME120, RUNNER_OPPOSITE, RUNNER_ATR2, RUNNER_NBAR10, RUNNER_EOD.
- **Time exits:** time [5, 15, 30, 60, 120, 'eod'] minutes; stop_time [60, 120, 'eod']; **opposite-signal exits:** max hold [240] min; gap-fill targets ['full', 'half'].
- **Management-template count:** 150 templates that use an initial stop + 9 without a stop (time / opposite / gap fill).
- **Stage A** (all 5,732 entries): each entry x its no-stop family exits, and x ATR stops {0.5, 1, 2} x fixed targets {0.5R, 1R, 2R}. **87,888 specifications.**
- **Stage B qualification rule** (fixed before Stage A ran): an entry qualifies if ANY of its Stage A variants had GROSS (before-cost) P&L > 0. **5,035 of 5,732 entries qualified.**
- **Stage B** (qualified entries only): targets/BE/time/partials/runners x the main stops; every trailing variant x two reference stops (ATR 1.0, swing); every stop definition x a small R sweep. **2,571,189 specifications.**
- **Total search: 2,659,077 specifications** on 2010-06-07..2020-12-31 only. Stage B searched the same data more deeply; both stages count toward the search.

## 6. Correctness tests

- **82 tests, 82 passed, 0 failed** (run before 2021 was opened, and again at the end; recorded in `PRE_VALIDATION_STATE.md` and `FINAL_INTEGRITY_CHECK.md`). Files: test_lookahead (20), test_management (23), test_engine_timing (9), test_split_guard (7), test_pipeline (6), test_costs_metrics (5), test_sessions_dst (4), test_cross_market (3), test_resample (3), test_reference (2).
- Failure modes covered: lookahead / future mutation never changes past signals; next-bar entry; higher-timeframe bars available only after they close; cross-market bars lagged and never forward-filled; 1-tick target trade-through (touch is not a fill, short side, gap exactly at target, partial touched stays open); stop/target same-bar ambiguity; gap-through stops; breakeven (next-bar move, same-bar ambiguity, entry-bar rule); trailing from next bar only; partial and runner accounting and exact partial-cost arithmetic; session flat and no session crossing; DST (RTH open 09:30 winter and summer, Sunday evening belongs to Monday); contract rolls; costs, profit factor, drawdown, streaks; split guards (discovery view physically excludes 2021, unseen years need a permit, non-official experiments cannot read them, validation refuses out-of-order years, arrays read-only); deterministic candidate IDs and trade-list deduplication; parallel workers identical to serial; managed kernel agrees with an independent reference kernel; full pipeline refusals (freeze immutable, discovery closed after freeze, cost change refused).
- **Freeze reproducibility check:** Deterministic sample: 601 candidates (first of every instrument x family x management family, plus every 952-th by ID) out of 190,475. Mismatches: 0 -> PASS Fields compared: trades, trade_list_id (hash of every trade's entry bar, exit bar, side and P&L), gross P&L, net P&L, PF, WR, max DD, long/short counts.
- **Independent stage checks** (`tools/check_stage.py`, after every year): cohort equals the previous survivors exactly, no duplicates, survival flag equals (trades > 0 and net > 0), per-candidate trade counts and net P&L reconcile with the stored trade files, every trade lies inside its year, and the ledger shows no later bar. All six PASSED (logs archived).
- **Data-boundary checks:** pre-2021 audit (cache views, results folders, logs, source-code reader audit, highest timestamp), per-year access audits, final ledger audit -- all PASSED (section 13).

## 7. Discovery results

| Quantity | Count |
|---|---|
| Stage A specifications | 87,888 |
| Stage B specifications | 2,571,189 |
| Total specifications tested | 2,659,077 |
| Entry specifications | 5,732 |
| Specifications with >= 1 trade | 2,623,559 |
| Unique trade behaviours (distinct trade lists) | 2,395,009 |
| Gross-profitable specs / unique | 905,124 / 837,989 |
| MODERATE_COST-profitable specs / unique | 347,069 / 301,410 |
| BASELINE-profitable specifications | 229,858 |
| STRESS-profitable specs / unique | 127,127 / 94,783 |
| **Unique official frozen candidates** | 190,475 |
| Distinct entry rules among frozen | 2,657 |
| COST_SENSITIVE_WATCHLIST (moderate- but not baseline-profitable; NOT frozen, NOT validated) | 110,935 |

**Instrument** (frozen cohort)

| Instrument | count | share |
|---|---|---|
| NQ | 140,718 | 73.9% |
| ES | 49,757 | 26.1% |

**Direction** (frozen cohort)

| Direction | count | share |
|---|---|---|
| long | 83,956 | 44.1% |
| both | 60,667 | 31.9% |
| short | 45,852 | 24.1% |

**Entry family** (frozen cohort)

| Entry family | count | share |
|---|---|---|
| momentum | 63,530 | 33.4% |
| mean_deviation | 35,099 | 18.4% |
| fvg | 17,106 | 9.0% |
| multi_timeframe | 14,625 | 7.7% |
| cross_market | 10,469 | 5.5% |
| volatility_regime | 7,763 | 4.1% |
| compression_expansion | 5,478 | 2.9% |
| session_open_distance | 5,454 | 2.9% |
| prior_session_levels | 5,069 | 2.7% |
| gap | 4,092 | 2.1% |
| displacement | 3,717 | 2.0% |
| time_of_day | 3,439 | 1.8% |
| rolling_breakout | 3,246 | 1.7% |
| candles | 2,205 | 1.2% |
| opening_range | 2,133 | 1.1% |
| price_structure | 2,053 | 1.1% |
| overnight_range | 1,996 | 1.0% |
| consecutive_bars | 1,583 | 0.8% |
| range_position | 1,063 | 0.6% |
| failed_breakout | 355 | 0.2% |

**Management type** (frozen cohort)

| Management type | count | share |
|---|---|---|
| rr | 36,686 | 19.3% |
| trail_atr | 30,345 | 15.9% |
| trail_nbar | 25,891 | 13.6% |
| be | 25,577 | 13.4% |
| trail_r | 21,882 | 11.5% |
| partial | 16,620 | 8.7% |
| runner | 15,578 | 8.2% |
| stop_time | 7,305 | 3.8% |
| trail_close_atr | 4,291 | 2.3% |
| time | 3,873 | 2.0% |
| trail_step | 2,003 | 1.1% |
| opposite | 416 | 0.2% |
| gapfill | 8 | 0.0% |

**Initial stop** (frozen cohort)

| Initial stop | count | share |
|---|---|---|
| swing | 81,527 | 42.8% |
| atr | 80,990 | 42.5% |
| signal_bar | 10,095 | 5.3% |
| points | 6,092 | 3.2% |
| none | 4,297 | 2.3% |
| range_frac | 3,894 | 2.0% |
| rolling | 3,036 | 1.6% |
| structural | 544 | 0.3% |

**Entry-parameter robustness** (frozen cohort)

| Entry-parameter robustness | count | share |
|---|---|---|
| MODERATE | 69,027 | 36.2% |
| CLIFF | 42,083 | 22.1% |
| BROAD_PLATEAU | 34,462 | 18.1% |
| NARROW | 29,616 | 15.5% |
| NO_NEIGHBOURS | 15,287 | 8.0% |

**Management-parameter robustness** (frozen cohort)

| Management-parameter robustness | count | share |
|---|---|---|
| BROAD_PLATEAU | 97,727 | 51.3% |
| MODERATE | 41,529 | 21.8% |
| NO_NEIGHBOURS | 32,614 | 17.1% |
| CLIFF | 11,967 | 6.3% |
| NARROW | 6,638 | 3.5% |

**PF distribution** (discovery, frozen cohort)

| PF | count | share |
|---|---|---|
| 1.0-1.1 | 89,700 | 47.1% |
| 1.1-1.2 | 30,668 | 16.1% |
| 1.3-1.5 | 16,603 | 8.7% |
| 1.5-2 | 16,246 | 8.5% |
| 1.2-1.3 | 16,105 | 8.5% |
| 3+ (incl. no losers) | 11,868 | 6.2% |
| 2-3 | 9,285 | 4.9% |

**Win rate distribution** (discovery, frozen cohort)

| Win rate | count | share |
|---|---|---|
| 40-50% | 58,254 | 30.6% |
| 30-40% | 47,328 | 24.8% |
| 50-60% | 34,092 | 17.9% |
| <30% | 30,390 | 16.0% |
| 60-70% | 11,857 | 6.2% |
| 80%+ | 4,735 | 2.5% |
| 70-80% | 3,819 | 2.0% |

**Trades per year distribution** (discovery, frozen cohort)

| Trades per year | count | share |
|---|---|---|
| <10 | 64,785 | 34.0% |
| 100-250 | 32,800 | 17.2% |
| 50-100 | 24,911 | 13.1% |
| 25-50 | 23,211 | 12.2% |
| 10-25 | 20,379 | 10.7% |
| 250-500 | 18,271 | 9.6% |
| 500+ | 6,118 | 3.2% |

**Target-R distribution** (final fixed target; blank = no fixed R target)

| target | count | share |
|---|---|---|
| no fixed target | 105,217 | 55.2% |
| 2R | 22,500 | 11.8% |
| 1R | 22,257 | 11.7% |
| 3R | 16,394 | 8.6% |
| 4R | 4,599 | 2.4% |
| 0.5R | 4,591 | 2.4% |
| 0.33R | 3,609 | 1.9% |
| 1.5R | 3,288 | 1.7% |
| 2.5R | 2,365 | 1.2% |
| 5R | 1,854 | 1.0% |
| 1.25R | 1,687 | 0.9% |
| 0.75R | 1,433 | 0.8% |
| 0.25R | 681 | 0.4% |

Robustness labels: BROAD_PLATEAU >= 75% of parameter neighbours profitable and their median net >= 50% of the candidate's; MODERATE >= 50%; NARROW 25-50%; CLIFF < 25%. Entry robustness varies entry parameters with management fixed; management robustness the reverse. Descriptive only.

## 8. Official freeze

- **190,475 unique candidates** (every unique trade list with trades > 0 and baseline net P&L > 0; identical trade lists collapsed to one, aliases kept in aliases.parquet).
- Name: **OFFICIAL_DISCOVERY_FREEZE**; frozen at **2026-09-22T00:55:52.120022+00:00**.
- Manifest: `results/main/frozen/FREEZE_MANIFEST.json` (copy in `official/frozen/`).
- **Manifest SHA-256: `c6da1c8ad6908f9a4ce94d8ed8e4cf5084bc465b94effd750556627be00f1d6b`**
- Behaviour-code hash (data/, features/, engine/, strategies/, config.py): `b5b7fc4b9ed13c88ae911c0c34455718bd1ade4d24af269d4c55bf205afbfccf`; registry hash `a00e25d5b3e80cf5bab04aa0ac812465a83bb4a4c4ed8b8b10dbf01f128fc01b`. Git: no commit (no identity configured; none invented) -- the source/config hashes stand in for a commit.
- Code change acknowledged at freeze: discovery ran with code hash `555e5683d5af55ba...`; before the freeze the append-only data-access ledger was added to the loader (logging only). Recorded: "added append-only data-access ledger to loader (logging only); doctor/data-check now footer-only/guarded; no trade logic changed". The reproducibility check (601 candidates, 0 mismatches) confirms no trade changed.
- Execution engine version **2**; cost config hash `a27ed5df0c04611fce85e81a2380963f9d63d955a88081a4c12b6e543c98624a`; search-space hash `a3355bceaec56e1e4917d53ae0961a08682d95542076795297f988050ccfa025`; management hash `4a7ac3cd72bb510ff2b461f396440465d2bbcf9665d3ec5629c02e6d56c9d342`; sessions hash `8035db7d5ae87ef61d879c06f9b08efd19612e89fff9845e30bd74048d17e6e6`; research config hash `83a8ca70936cc42cb94c6bbd35a6766371d9af88c6ec95aae91ecbb700ef866d`.
- Stage A results hash `3b3af9252e02a8e8d8fab435c42d0fc3ddf39dc442e34c7a3d8342af7e0f8825` (248 shards); Stage B results hash `e1fbeb67103f127a0842041b78c080e45863f402c7cd92e646af4b9e52e13e62` (1904 shards).
- **After this point no candidate rule could change.** Candidate IDs are hashes of the full specification (entry, management, execution assumptions, cost version, sessions); the frozen files are read-only and hash-checked; validation refuses to run if the cost, code or freeze hashes differ. The final integrity check re-hashed all 190,475 specifications with 0 mismatches.

## 9. Sequential unseen funnel

| Stage | Entering | Profitable | Failed | Survival % | Cumulative % |
|---|---|---|---|---|---|
| Discovery freeze (2010-06-07..2020-12-31) | - | 190,475 | - | - | 100.000% |
| 2021 | 190,475 | 104,342 | 86,133 | 54.78% | 54.780% |
| 2022 | 104,342 | 63,361 | 40,981 | 60.72% | 33.265% |
| 2023 | 63,361 | 42,828 | 20,533 | 67.59% | 22.485% |
| 2024 | 42,828 | 29,748 | 13,080 | 69.46% | 15.618% |
| 2025 (final validation) | 29,748 | 16,553 | 13,195 | 55.64% | 8.690% |
| 2026 (FINAL FORWARD - PARTIAL YEAR) | 16,553 | 11,462 | 5,091 | 69.24% | 6.018% |

Rule at every stage: trades > 0 AND BASELINE net P&L > 0. Nothing else. Failures are preserved, not deleted. 2026 = FINAL FORWARD - PARTIAL YEAR (ES through 2026-08-14 16:59 NY; NQ through 2026-08-10 19:59 NY). A 50%-per-stage coin flip would leave 190,475 x 0.5^6 = 2,976 -- a reference line only, since the candidates are not independent.

## 10. Final survivors

- **Final survivors: 11,462** (profitable in 2021, 2022, 2023, 2024, 2025 and the partial 2026). Recomputed from the six stage result files; equals the final report.
- **Distinct entry rules: 567** (of 2,657 among the frozen cohort).
- NQ 10,876 (94.9%); ES 586.
- Long-only 5,577; short-only 1,227; both 4,658.
- Cumulative OOS PF (2021..2026 only; finite values): min 1.028, p5 1.086, p25 1.181, median 1.321, p75 1.517, p95 2.249, max 16.195; 4 survivors had no losing OOS trade (PF infinite).
- Cumulative OOS trades per survivor: min 7, p5 71, p25 282, median 574, p75 1,270, p95 2,631, max 5,717; total 9,975,435 (summed across overlapping candidates).
- Cumulative OOS net P&L per survivor ($, one contract): min 392, p5 20,881, p25 63,960, median 104,150, p75 153,220, p95 268,088, max 513,525. Summed over all survivors $1,340,752,280 -- NOT an achievable portfolio figure: survivors overlap heavily.
- OOS net P&L from long trades $946,139,848 (70.6%); from short trades $394,612,432 (29.4%) (sum over survivors, baseline net).
- Short-only survivors: 1,227 from 70 entry rules; median cumulative OOS PF 1.545.

**Family composition of final survivors**

| family | count | share |
|---|---|---|
| momentum | 3,860 | 33.7% |
| mean_deviation | 2,583 | 22.5% |
| cross_market | 1,607 | 14.0% |
| fvg | 1,235 | 10.8% |
| multi_timeframe | 529 | 4.6% |
| session_open_distance | 306 | 2.7% |
| volatility_regime | 253 | 2.2% |
| prior_session_levels | 162 | 1.4% |
| compression_expansion | 155 | 1.4% |
| candles | 126 | 1.1% |
| time_of_day | 114 | 1.0% |
| range_position | 109 | 1.0% |
| displacement | 93 | 0.8% |
| consecutive_bars | 91 | 0.8% |
| opening_range | 75 | 0.7% |
| rolling_breakout | 59 | 0.5% |
| price_structure | 46 | 0.4% |
| failed_breakout | 24 | 0.2% |
| overnight_range | 22 | 0.2% |
| gap | 13 | 0.1% |

**Management composition of final survivors**

| management type | count | share |
|---|---|---|
| trail_atr | 2,230 | 19.5% |
| trail_r | 1,854 | 16.2% |
| be | 1,820 | 15.9% |
| rr | 1,525 | 13.3% |
| trail_nbar | 1,436 | 12.5% |
| runner | 861 | 7.5% |
| partial | 607 | 5.3% |
| stop_time | 505 | 4.4% |
| trail_close_atr | 238 | 2.1% |
| time | 199 | 1.7% |
| trail_step | 143 | 1.2% |
| opposite | 44 | 0.4% |

## 11. Stronger survivor subset

Final survivors with **at least 200 OOS trades AND cumulative OOS PF >= 1.3: 4,362 candidates from 138 distinct entry rules** (NQ 4,296, ES 66; long 1,988, short 383, both 1,991). These thresholds were chosen AFTER the funnel as a descriptive view; they are not an official gate.

## 12. Important observations (descriptive)

- **Discovery PF did not predict next-period PF** (rank correlation by stage: 2021 -0.01, 2022 -0.04, 2023 +0.07, 2024 +0.11, 2025 -0.19, 2026 +0.32).
- **The strongest discovery candidates generalised worst.** Share surviving every stage by discovery PF: <1.10 7.97%, 1.10-1.25 7.35%, 1.25-1.50 4.49%, 1.50-2.00 1.66%, 2.00-3.00 0.62%, >=3.00 0.05%.
- **NQ dominates:** 94.9% of final survivors trade NQ (NQ was 73.9% of the frozen cohort).
- **Long exposure benefited from a rising NQ market:** first-year pass rate long 62.0% vs short 39.9%; 71% of survivors' OOS net came from long trades.
- **Short-only survivors also exist:** 1,227 (median OOS PF 1.55), which market drift alone does not explain -- but whether this is unusual needs a no-edge reference (section 15).
- **Costs became a smaller hurdle:** costs are fixed dollars while NQ point ranges grew with the price level. Median net P&L per trade of each stage's entrants: 2021 14.37 (discovery) -> 27.32; 2022 12.20 (discovery) -> 52.86; 2023 10.91 (discovery) -> 49.30; 2024 10.46 (discovery) -> 50.87; 2025 10.68 (discovery) -> 21.92; 2026 9.28 (discovery) -> 121.44.
- **The headline count greatly exceeds the number of independent ideas:** 11,462 survivors share 567 entry rules, many of which are themselves near-duplicates (neighbouring parameters of one family).

## 13. Data-access audit

- Highest real timestamp accessible before 2021 (all discovery-phase ledger entries): **2020-12-31 16:59:00-05:00**.
- First 2021 access: **2026-09-22 09:33:32.820047+00:00** UTC
- First 2022 access: **2026-09-22 09:55:06.037031+00:00** UTC
- First 2023 access: **2026-09-22 10:01:27.850208+00:00** UTC
- First 2024 access: **2026-09-22 10:05:23.099270+00:00** UTC
- First 2025 access: **2026-09-22 10:08:06.052585+00:00** UTC
- First 2026 access: **2026-09-22 10:10:01.212275+00:00** UTC
- Final real-market timestamp: ES **2026-08-14 16:59:00-04:00**, NQ **2026-08-10 19:59:00-04:00**.

| stage | phase | first_access_utc | entries | max_bar_read_in_stage_ny | max_bar_accessed_before_this_stage_ny |
|---|---|---|---|---|---|
| discovery | discovery | 2026-09-22 00:32:38.080132+00:00 | 191 | 2020-12-31 16:59:00-05:00 | - |
| 2021 | unseen:official | 2026-09-22 09:33:32.820047+00:00 | 8 | 2021-12-31 16:59:00-05:00 | 2020-12-31 16:59:00-05:00 |
| 2022 | unseen:official | 2026-09-22 09:55:06.037031+00:00 | 8 | 2022-12-30 16:59:00-05:00 | 2021-12-31 16:59:00-05:00 |
| 2023 | unseen:official | 2026-09-22 10:01:27.850208+00:00 | 8 | 2023-12-29 16:59:00-05:00 | 2022-12-30 16:59:00-05:00 |
| 2024 | unseen:official | 2026-09-22 10:05:23.099270+00:00 | 8 | 2024-12-31 16:59:00-05:00 | 2023-12-29 16:59:00-05:00 |
| 2025 | unseen:official | 2026-09-22 10:08:06.052585+00:00 | 8 | 2025-12-31 16:59:00-05:00 | 2024-12-31 16:59:00-05:00 |
| 2026 | unseen:official | 2026-09-22 10:10:01.212275+00:00 | 6 | 2026-08-14 16:59:00-04:00 | 2025-12-31 16:59:00-05:00 |

- Stage-order violations (a year read before it was officially opened): 0
- Entries from commands outside the approved research commands: 0
- RESULT: PASS -- every data-access boundary was respected
- Per-year ACCESS_AUDIT.md files confirm after each year that the following year was still unopened.
- Disclosures (outside QuantLabV2 code, see PRE_2021_DATA_ACCESS_AUDIT.md): the files' schema and first/last timestamps were inspected during setup; `doctor` once read the timestamp column (now footer-only); the 2021-2026 data had been used extensively in the older `Quant` project, so the designers are not blind to those years even though QuantLabV2's code was.

## 14. Limitations

- Strategies are highly dependent: variants share entries, stops and market exposure, so they succeed and fail together.
- The survivor count (11,462) is not an independent-strategy count; distinct entry rules number 567, and those are clustered further.
- Many management variants share one entry; a single good (or lucky) entry produces dozens of survivors.
- 2021-2026 was mostly a rising NQ market; long-biased rules had a tailwind.
- Costs are fixed in dollars; as NQ's point volatility grew, the cost hurdle shrank relative to moves.
- 2026 is partial (ES to Aug 14, NQ to Aug 10) and is not a full year.
- **The experiment has no no-edge null distribution yet**: we do not know how many of the frozen cohort would survive the same funnel on markets with no exploitable direction.
- Execution is simulated on 1-minute bars (next-bar open fills, pessimistic ambiguity, fixed slippage); real fills, queue position, outages and liquidity shocks are not modelled.
- The 2021-2026 period was not unseen by the researchers (see disclosures); only by the code.
- Historical unseen survival does not guarantee future profitability.

## 15. Open questions

- **Most important: How unusual is the real 2021 to 2026 survivor funnel relative to the same frozen cohort on no-edge surrogate markets?**
- How many genuinely distinct behaviours (by P&L correlation) the survivors represent.
- Whether the short-only survivors and the >=200-trade / PF>=1.3 subset exceed what a no-edge world produces.

**The next experiment is the NULL FUNNEL**: the exact 190,475 frozen candidates run through the same 2021-2026 sequential funnel on many surrogate markets that keep realistic volatility, calendar and NQ/ES structure but destroy directional predictability. Results go to `results/null_funnel/` and never modify this archive or `results/main`.

## Appendix: files in this archive

- `official/` copies of the freeze manifest, audits, ledger, stage manifests, access audits, reports, final tables and logs; `config/` all configuration; `source_snapshot/` all source and tests as run; `tools/` the check scripts; `VERIFIED_FACTS.json` the machine-readable numbers used above.
- Large official files are referenced by path and SHA-256 in `ARCHIVE_MANIFEST.json` instead of copied.
- `ARCHIVE_SHA256.txt` = SHA-256 of `ARCHIVE_MANIFEST.json`.
