# OFFICIAL DISCOVERY REPORT -- main

Discovery 2010-06-07 -> 2020-12-31. Freeze manifest SHA-256 `c6da1c8ad6908f9a4ce94d8ed8e4cf5084bc465b94effd750556627be00f1d6b`. Costs costs_v2_approved_2026-09-21#a27ed5df0c04. Engine v2. **No data after 2020-12-31 was read.**

## 1. Search and qualification counts

Stage B rule: an entry qualifies if ANY of its Stage A variants had gross (before-cost) P&L > 0. Stage B searched the SAME discovery data more deeply for entries chosen by Stage A. It is not an independent experiment; both stages count toward the search.

| quantity | count |
|---|---|
| Specifications tested (total effective search) | 2,659,077 |
|   Stage A specifications | 87,888 |
|   Entries qualifying for Stage B | 5,035 |
|   Stage B specifications | 2,571,189 |
| Entry specifications | 5,732 |
| Specs with at least one trade | 2,623,559 |
| Unique trade behaviours | 2,395,009 |
| Gross-profitable (unique) | 837,989 |
| MODERATE_COST-profitable (unique) | 301,410 |
| BASELINE-profitable specs | 229,858 |
| STRESS-profitable (unique) | 94,783 |
| OFFICIAL unique frozen candidates | 190,475 |
| COST_SENSITIVE_WATCHLIST (separate, not frozen) | 110,935 |

## 2. Official cohort by instrument

| instrument | frozen |
|---|---|
| NQ | 140718 |
| ES | 49757 |

## 3. By direction

| direction | frozen |
|---|---|
| long | 83956 |
| both | 60667 |
| short | 45852 |

## 4. By family

| family | frozen |
|---|---|
| momentum | 63530 |
| mean_deviation | 35099 |
| fvg | 17106 |
| multi_timeframe | 14625 |
| cross_market | 10469 |
| volatility_regime | 7763 |
| compression_expansion | 5478 |
| session_open_distance | 5454 |
| prior_session_levels | 5069 |
| gap | 4092 |
| displacement | 3717 |
| time_of_day | 3439 |
| rolling_breakout | 3246 |
| candles | 2205 |
| opening_range | 2133 |
| price_structure | 2053 |
| overnight_range | 1996 |
| consecutive_bars | 1583 |
| range_position | 1063 |
| failed_breakout | 355 |

## 5. By management family

| mgmt_kind | frozen |
|---|---|
| rr | 36686 |
| trail_atr | 30345 |
| trail_nbar | 25891 |
| be | 25577 |
| trail_r | 21882 |
| partial | 16620 |
| runner | 15578 |
| stop_time | 7305 |
| trail_close_atr | 4291 |
| time | 3873 |
| trail_step | 2003 |
| opposite | 416 |
| gapfill | 8 |

## 6. By initial stop method

| stop_method | frozen |
|---|---|
| swing | 81527 |
| atr | 80990 |
| signal_bar | 10095 |
| points | 6092 |
| none | 4297 |
| range_frac | 3894 |
| rolling | 3036 |
| structural | 544 |

## 7. Profit factor distribution

| range | candidates | share |
|---|---|---|
| 1.0-1.1 | 89700 | 47.1% |
| 1.1-1.2 | 30668 | 16.1% |
| 1.2-1.3 | 16105 | 8.5% |
| 1.3-1.5 | 16603 | 8.7% |
| 1.5-2 | 16246 | 8.5% |
| 2-3 | 9285 | 4.9% |
| 3+ (incl. inf) | 11868 | 6.2% |

## 8. Win-rate distribution

| range | candidates | share |
|---|---|---|
| <30% | 30390 | 16.0% |
| 30-40% | 47328 | 24.8% |
| 40-50% | 58254 | 30.6% |
| 50-60% | 34092 | 17.9% |
| 60-70% | 11857 | 6.2% |
| 70-80% | 3819 | 2.0% |
| 80%+ | 4735 | 2.5% |

## 9. Target-R distribution (final fixed target)

| target | frozen |
|---|---|
| no fixed target | 105217 |
| 2R | 22500 |
| 1R | 22257 |
| 3R | 16394 |
| 4R | 4599 |
| 0.5R | 4591 |
| 0.33R | 3609 |
| 1.5R | 3288 |
| 2.5R | 2365 |
| 5R | 1854 |
| 1.25R | 1687 |
| 0.75R | 1433 |
| 0.25R | 681 |

## 10. Trades-per-year distribution

| range | candidates | share |
|---|---|---|
| <25 (LOW_SAMPLE-prone) | 85164 | 44.7% |
| 25-100 | 48122 | 25.3% |
| 100-500 | 51071 | 26.8% |
| 500-1,000 | 5982 | 3.1% |
| 1,000-2,500 | 136 | 0.1% |
| 2,500+ | 0 | 0.0% |

## 11. Maximum drawdown distribution ($, one contract)

| range | candidates | share |
|---|---|---|
| <$2k | 48599 | 25.5% |
| $2-5k | 33479 | 17.6% |
| $5-10k | 33170 | 17.4% |
| $10-25k | 51507 | 27.0% |
| $25-50k | 21025 | 11.0% |
| $50k+ | 2695 | 1.4% |

## 12. Positive discovery years

| positive_years | frozen |
|---|---|
| 1 | 12965 |
| 2 | 12771 |
| 3 | 22381 |
| 4 | 35645 |
| 5 | 43047 |
| 6 | 33707 |
| 7 | 19275 |
| 8 | 8063 |
| 9 | 2210 |
| 10 | 385 |
| 11 | 26 |

## 13. Entry-parameter robustness

BROAD_PLATEAU >= 75% of neighbours profitable and their median net >= 50% of the candidate's; MODERATE >= 50%; NARROW 25-50%; CLIFF < 25%. Descriptive only.

| entry_robustness | frozen |
|---|---|
| MODERATE | 69027 |
| CLIFF | 42083 |
| BROAD_PLATEAU | 34462 |
| NARROW | 29616 |
| NO_NEIGHBOURS | 15287 |

## 14. Management-parameter robustness

BROAD_PLATEAU >= 75% of neighbours profitable and their median net >= 50% of the candidate's; MODERATE >= 50%; NARROW 25-50%; CLIFF < 25%. Descriptive only.

| management_robustness | frozen |
|---|---|
| BROAD_PLATEAU | 97727 |
| MODERATE | 41529 |
| NO_NEIGHBOURS | 32614 |
| CLIFF | 11967 |
| NARROW | 6638 |

## 15. Threshold counts (descriptive, not gates)

| official frozen candidates with ... | count |
|---|---|
| PF > 1.1 | 100,771 |
| PF > 1.2 | 70,106 |
| PF > 1.3 | 53,998 |
| PF > 1.5 | 37,389 |
| PF > 2.0 | 21,139 |
| WR > 60% | 18,795 |
| WR > 70% | 8,431 |
| WR > 80% | 4,243 |
| 500+ trades/yr | 6,118 |
| 1,000+ trades/yr | 136 |
| 2,500+ trades/yr | 0 |
| 100-500 trades/yr | 51,071 |
| 25-100 trades/yr | 48,122 |
| < 25 trades/yr (flag LOW_SAMPLE) | 85,164 |
| sub-1R target | 10,314 |
| 1.5R+ target | 51,000 |
| 2R+ target | 47,712 |
| 3R+ target | 22,847 |
| 4R target | 6,453 |
| breakeven management | 29,697 |
| trailing management | 93,838 |
| partials | 16,620 |
| runners | 15,578 |
| plain time / opposite exit (no stop) | 4,289 |
| Stage A (simple management) candidates | 6,925 |

## 16. ENTRY EDGE vs EXIT / PAYOFF SHAPING (all entries)

A_SIMPLE_EDGE: the entry is already profitable with simple management (a Stage A variant: plain time / opposite-signal exit, or the core 0.5/1/2R target with a 0.5/1/2 ATR stop); B_MANAGEMENT_RESCUED: no simple variant is profitable, but at least one expanded management (BE, trail, partial, runner, other stop or target) makes it profitable; C_NOT_RESCUED: no tested management makes the entry profitable

| entry_class | entries |
|---|---|
| A_SIMPLE_EDGE | 2064 |
| B_MANAGEMENT_RESCUED | 632 |
| C_NOT_RESCUED | 3036 |

## 16b. How many management methods make a profitable entry work

D_MANY_METHODS: profitable under >= 3 different management families and >= 25% of its tested variants; SEVERAL: profitable under several variants but not broadly; E_SINGLE_SPECIFIC: profitable under only 1-2 specific management configurations; -: no profitable variant

| management_breadth | entries |
|---|---|
| D_MANY_METHODS | 726 |
| E_SINGLE_SPECIFIC | 358 |
| SEVERAL | 1612 |

## 16c. Entry classes by family

| instrument | family | A_SIMPLE_EDGE | B_MANAGEMENT_RESCUED | C_NOT_RESCUED |
|---|---|---|---|---|
| ES | candles | 2 | 0 | 142 |
| ES | compression_expansion | 32 | 1 | 63 |
| ES | consecutive_bars | 5 | 4 | 27 |
| ES | cross_market | 17 | 5 | 170 |
| ES | displacement | 26 | 3 | 67 |
| ES | failed_breakout | 3 | 0 | 27 |
| ES | fvg | 48 | 17 | 151 |
| ES | gap | 8 | 2 | 14 |
| ES | mean_deviation | 199 | 17 | 84 |
| ES | momentum | 242 | 62 | 326 |
| ES | multi_timeframe | 40 | 46 | 202 |
| ES | opening_range | 0 | 6 | 18 |
| ES | overnight_range | 0 | 4 | 32 |
| ES | price_structure | 3 | 2 | 139 |
| ES | prior_session_levels | 6 | 0 | 90 |
| ES | range_position | 12 | 2 | 106 |
| ES | rolling_breakout | 17 | 1 | 162 |
| ES | session_open_distance | 37 | 1 | 22 |
| ES | time_of_day | 19 | 3 | 60 |
| ES | volatility_regime | 34 | 9 | 29 |
| NQ | candles | 47 | 25 | 72 |
| NQ | compression_expansion | 48 | 12 | 36 |
| NQ | consecutive_bars | 14 | 12 | 10 |
| NQ | cross_market | 79 | 30 | 83 |
| NQ | displacement | 41 | 7 | 48 |
| NQ | failed_breakout | 9 | 3 | 18 |
| NQ | fvg | 90 | 33 | 93 |
| NQ | gap | 17 | 2 | 5 |
| NQ | mean_deviation | 220 | 13 | 67 |
| NQ | momentum | 331 | 96 | 203 |
| NQ | multi_timeframe | 101 | 61 | 126 |
| NQ | opening_range | 11 | 8 | 5 |
| NQ | overnight_range | 19 | 5 | 12 |
| NQ | price_structure | 32 | 38 | 74 |
| NQ | prior_session_levels | 40 | 27 | 29 |
| NQ | range_position | 38 | 9 | 73 |
| NQ | rolling_breakout | 54 | 39 | 87 |
| NQ | session_open_distance | 38 | 6 | 16 |
| NQ | time_of_day | 34 | 15 | 33 |
| NQ | volatility_regime | 51 | 6 | 15 |

## 17. High-win-rate buckets

| win_rate_at_least | candidates | with_sub_1R_target | median_target_R | median_stop_pts | median_stop_atr_mult | median_pf | median_trades_per_year | median_net_pnl | median_max_dd | median_win_loss_ratio |
|---|---|---|---|---|---|---|---|---|---|---|
| 60.0% | 20,411 | 7,828 | 0.75 | 11.25 | 1.50 | 1.41 | 1.89 | 1,471 | 936.00 | 0.72 |
| 65.0% | 13,784 | 6,163 | 0.50 | 10.75 | 1.50 | 1.53 | 0.66 | 1,047 | 589.00 | 0.62 |
| 70.0% | 8,554 | 4,216 | 0.50 | 10.75 | 1.50 | 1.62 | 0.47 | 880.67 | 291.50 | 0.51 |
| 75.0% | 6,516 | 2,833 | 0.50 | 10.00 | 1.00 | 1.98 | 0.38 | 664.00 | 0.00 | 0.51 |
| 80.0% | 4,735 | 1,763 | 1.00 | 9.75 | 1.00 | 2.35 | 0.19 | 523.25 | 0.00 | 0.47 |
| 85.0% | 3,681 | 1,179 | 1.00 | 9.75 | 1.00 | 3.62 | 0.19 | 451.00 | 0.00 | 0.50 |

## 18. Fixed stop/target: breakeven win rate before / after costs vs observed

| target_R | candidates | breakeven_before_costs | median_breakeven_after_costs | median_observed_win_rate | median_margin_after_costs | median_pf | median_trades_per_year |
|---|---|---|---|---|---|---|---|
| 0.25 | 681.00 | 80.0% | 84.6% | 76.1% | -7.8% | 1.28 | 1.89 |
| 0.33 | 3,609 | 75.2% | 78.4% | 73.3% | -5.8% | 1.19 | 4.45 |
| 0.50 | 4,591 | 66.7% | 69.7% | 65.4% | -5.0% | 1.18 | 7.57 |
| 0.75 | 1,433 | 57.1% | 61.2% | 57.1% | -4.0% | 1.18 | 6.53 |
| 1.00 | 6,416 | 50.0% | 52.6% | 52.7% | -0.2% | 1.12 | 21.48 |
| 1.25 | 1,687 | 44.4% | 47.9% | 48.6% | 0.5% | 1.11 | 19.02 |
| 1.50 | 1,922 | 40.0% | 43.2% | 45.7% | 2.4% | 1.11 | 24.22 |
| 2.00 | 8,771 | 33.3% | 35.4% | 44.2% | 8.7% | 1.10 | 35.48 |
| 2.50 | 2,365 | 28.6% | 31.1% | 39.2% | 7.8% | 1.11 | 32.08 |
| 3.00 | 2,561 | 25.0% | 27.3% | 37.2% | 9.5% | 1.10 | 35.48 |
| 4.00 | 2,650 | 20.0% | 21.9% | 34.6% | 12.5% | 1.10 | 43.81 |

## 19. Did the extra management help? (same entry + same stop, simpler management)

| mgmt_kind | candidates | improved | median_uplift |
|---|---|---|---|
| be | 25577 | 12797 | $3 |
| partial | 16620 | 11231 | $461 |
| runner | 15578 | 11740 | $1,612 |
| trail_atr | 30345 | 17299 | $696 |
| trail_close_atr | 4291 | 2367 | $495 |
| trail_nbar | 25891 | 11933 | -$300 |
| trail_r | 21882 | 12115 | $462 |
| trail_step | 2003 | 1178 | $831 |

## 20. Breakeven counterfactual across all BE candidates (trades stopped at BE)

| quantity | trades |
|---|---|
| be_moved_trades | 13,229,824 |
| be_stopped_trades | 6,060,323 |
| be_saved_losses | 3,333,742 |
| be_cost_winners | 2,039,362 |
| be_no_difference | 297,583 |

## 21. COST_SENSITIVE_WATCHLIST (NOT frozen, NOT validated)

110,935 unique strategies are profitable at MODERATE cost ($9 NQ / $16.50 ES) but not at BASELINE ($14 / $29).

| family | watchlist |
|---|---|
| momentum | 27198 |
| fvg | 12813 |
| multi_timeframe | 10665 |
| mean_deviation | 9339 |
| cross_market | 7158 |
| rolling_breakout | 5940 |
| price_structure | 4782 |
| candles | 4340 |
| prior_session_levels | 3750 |
| compression_expansion | 3712 |
| range_position | 3170 |
| time_of_day | 3111 |
| displacement | 3055 |
| volatility_regime | 2558 |
| session_open_distance | 2219 |
| overnight_range | 1973 |
| consecutive_bars | 1642 |
| gap | 1350 |
| opening_range | 1312 |
| failed_breakout | 848 |

## 22. Representative candidates (examples of different shapes -- NOT a selection)

### Highest profit factor (>= 100 trades)
`Cbe3434a4a6d6cd1b` -- NQ · momentum · long · entry class A_SIMPLE_EDGE · entry robustness MODERATE · management robustness BROAD_PLATEAU

- **Strategy family:** N-bar momentum (momentum; tier 1; complexity 1)
- **What it tests:** Measures the move over the previous N one-minute bars in volatility units and acts the first bar it exceeds a threshold.
- **Instrument:** NQ
- **Direction:** Long only
- **ENTRY RULE:** BUY when the close has fallen at least 2.0 x ATR60 x sqrt(240) below the close 240 minutes earlier (first bar this becomes true). Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 1 tick beyond the signal bar's low (long) / high (short). Initial stop only, no target; otherwise exit after 60 minutes. Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** lookback=240, mode=reversal, window=rth, z=2.0
- **Management parameters:** stop=signal_bar; management=STOP_TIME_60
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 121 (11.4 per year; 121 long / 0 short)
  - Win rate: 10.7%   Profit factor: 4.52 (before costs 9.55)
  - Net profit: $10,236 (gross $11,930, stressed costs $8,784)   Per year: $969
  - Average trade: $84.60   Avg winner $1,011.00 / avg loser -$26.92
  - Max drawdown: $2,073   Longest losing streak: 31 trades
  - Positive years: 3 of 11   Positive months: 11 of 41
  - Initial risk: 1.71 pts average ($34), median 0.50 pts
  - Target: -   Average winner +9.55R / average loser -1.07R   Average trade -1.426R net
  - Breakeven implied by the realised average winner/loser: 2.6%
  - Warnings (descriptive): PNL_CONCENTRATED,ONE_YEAR_DOMINATED,ONE_MONTH_DOMINATED,UNSTABLE_YEARLY_RESULTS,LONG_LOSS_STREAK

### Highest win rate (>= 100 trades)
`C41111ad4466380a9` -- ES · momentum · both · entry class A_SIMPLE_EDGE · entry robustness NARROW · management robustness BROAD_PLATEAU

- **Strategy family:** N-bar momentum (momentum; tier 1; complexity 2)
- **What it tests:** Measures the move over the previous N one-minute bars in volatility units and acts the first bar it exceeds a threshold.
- **Instrument:** ES
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when the close has risen at least 1.5 x ATR60 x sqrt(240) above the close 240 minutes earlier (first bar this becomes true). SELL SHORT when the close has fallen at least 1.5 x ATR60 x sqrt(240) below the close 240 minutes earlier (first bar this becomes true). Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 2 x ATR(14 fifteen-minute bars) from the entry. Initial stop = 1R, single target at +0.25R. Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 12:00 New York, always flat by 16:00
- **Entry parameters:** lookback=240, mode=continuation, window=rth_am, z=1.5
- **Management parameters:** stop=atr mult=2.0; management=RR_0.25R
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 103 (9.7 per year; 71 long / 32 short)
  - Win rate: 88.3%   Profit factor: 1.72 (before costs 2.49)
  - Net profit: $3,200 (gross $6,188, stressed costs $420)   Per year: $303
  - Average trade: $31.07   Avg winner $84.19 / avg loser -$371.71
  - Max drawdown: $1,441   Longest losing streak: 1 trades
  - Positive years: 8 of 11   Positive months: 48 of 58
  - Initial risk: 8.64 pts average ($432), median 7.25 pts
  - Target: 0.25R   Average winner +0.26R / average loser -0.62R   Average trade +0.075R net
  - Breakeven win rate: 80.0% before costs, 86.4% after costs (at the median risk); observed 88.3%
  - Breakeven implied by the realised average winner/loser: 81.5%
  - Warnings (descriptive): LONG_SIDE_DEPENDENT,ENTRY_CLIFF

### Best 0.25R-target strategy (by net)
`C95160659e2c324d3` -- NQ · prior_session_levels · both · entry class A_SIMPLE_EDGE · entry robustness NO_NEIGHBOURS · management robustness BROAD_PLATEAU

- **Strategy family:** Prior-session levels (prior_session_levels; tier 1; complexity 1)
- **What it tests:** Reactions to the previous session's RTH high, low, close or midpoint.
- **Instrument:** NQ
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when the close crosses ABOVE the previous session's RTH low (first time this session). SELL SHORT when the close crosses BELOW the previous session's RTH low (first time this session). Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short). Initial stop = 1R, single target at +0.25R. Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** event=break, first_only=True, level=low, mode=continuation, window=rth
- **Management parameters:** stop=swing; management=RR_0.25R
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 1,152 (109.0 per year; 384 long / 768 short)
  - Win rate: 74.7%   Profit factor: 1.24 (before costs 1.42)
  - Net profit: $24,027 (gross $40,155, stressed costs $10,203)   Per year: $2,274
  - Average trade: $20.86   Avg winner $144.19 / avg loser -$344.05
  - Max drawdown: $14,163   Longest losing streak: 5 trades
  - Positive years: 4 of 11   Positive months: 65 of 127
  - Initial risk: 29.92 pts average ($598), median 19.50 pts
  - Target: 0.25R   Average winner +0.26R / average loser -0.77R   Average trade -0.080R net
  - Breakeven win rate: 80.0% before costs, 82.9% after costs (at the median risk); observed 74.7%
  - Breakeven implied by the realised average winner/loser: 70.5%
  - Warnings (descriptive): UNSTABLE_YEARLY_RESULTS

### Best 0.5R-target strategy (by net)
`C79c29c82dfcccc25` -- NQ · range_position · both · entry class A_SIMPLE_EDGE · entry robustness MODERATE · management robustness MODERATE

- **Strategy family:** Range position (range_position; tier 1; complexity 1)
- **What it tests:** Where the close sits inside the previous N-bar high-low range (0 = low, 1 = high).
- **Instrument:** NQ
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when the close moves into the top 10% of the previous 120-bar range (or above it). SELL SHORT when the close moves into the bottom 10% of the previous 120-bar range (or below it). Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 40 points from the entry. Initial stop = 1R, single target at +0.5R. Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** edge=0.1, lookback=120, mode=continuation, window=rth
- **Management parameters:** stop=points points=40.0; management=RR_0.5R
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 7,182 (679.6 per year; 3,583 long / 3,599 short)
  - Win rate: 62.3%   Profit factor: 1.07 (before costs 1.14)
  - Net profit: $97,477 (gross $198,025, stressed costs $11,293)   Per year: $9,224
  - Average trade: $13.57   Avg winner $342.92 / avg loser -$529.60
  - Max drawdown: $24,458   Longest losing streak: 9 trades
  - Positive years: 8 of 11   Positive months: 66 of 127
  - Initial risk: 40.00 pts average ($800), median 40.00 pts
  - Target: 0.5R   Average winner +0.45R / average loser -0.64R   Average trade +0.017R net
  - Breakeven win rate: 66.7% before costs, 67.8% after costs (at the median risk); observed 62.3%
  - Breakeven implied by the realised average winner/loser: 60.7%
  - Warnings (descriptive): THIN_EDGE

### Best 0.75R-target strategy (by net)
`Cc82fe5230c41fca7` -- NQ · fvg · long · entry class A_SIMPLE_EDGE · entry robustness MODERATE · management robustness BROAD_PLATEAU

- **Strategy family:** Three-candle fair-value gap (fvg; tier 1; complexity 1)
- **What it tests:** Creation of, and first return into, a mechanically defined three-candle price gap.
- **Instrument:** NQ
- **Direction:** Long only
- **ENTRY RULE:** BUY when price first trades back down into the most recent bullish 5-minute FVG of at least 0.25 x ATR60 x sqrt(5). Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short). Initial stop = 1R, single target at +0.75R. Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** event=touch, min_gap=0.25, mode=continuation, timeframe=5, window=rth
- **Management parameters:** stop=swing; management=RR_0.75R
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 5,557 (525.8 per year; 5,557 long / 0 short)
  - Win rate: 57.2%   Profit factor: 1.07 (before costs 1.18)
  - Net profit: $53,127 (gross $130,925, stressed costs -$13,557)   Per year: $5,027
  - Average trade: $9.56   Avg winner $251.51 / avg loser -$313.64
  - Max drawdown: $21,053   Longest losing streak: 8 trades
  - Positive years: 4 of 11   Positive months: 67 of 127
  - Initial risk: 19.99 pts average ($400), median 13.00 pts
  - Target: 0.75R   Average winner +0.69R / average loser -0.82R   Average trade -0.042R net
  - Breakeven win rate: 57.1% before costs, 60.2% after costs (at the median risk); observed 57.2%
  - Breakeven implied by the realised average winner/loser: 55.5%
  - Warnings (descriptive): PNL_CONCENTRATED,ONE_YEAR_DOMINATED,COST_SENSITIVE,THIN_EDGE,UNSTABLE_YEARLY_RESULTS

### Best 1R-target strategy (by net)
`Cb100c0740d5d21c0` -- NQ · range_position · both · entry class A_SIMPLE_EDGE · entry robustness BROAD_PLATEAU · management robustness CLIFF

- **Strategy family:** Range position (range_position; tier 1; complexity 1)
- **What it tests:** Where the close sits inside the previous N-bar high-low range (0 = low, 1 = high).
- **Instrument:** NQ
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when the close moves into the top 20% of the previous 30-bar range (or above it). SELL SHORT when the close moves into the bottom 20% of the previous 30-bar range (or below it). Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 40 points from the entry. Initial stop = 1R, single target at +1R. Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** edge=0.2, lookback=30, mode=continuation, window=rth
- **Management parameters:** stop=points points=40.0; management=RR_1R
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 5,833 (551.9 per year; 2,921 long / 2,912 short)
  - Win rate: 52.1%   Profit factor: 1.07 (before costs 1.13)
  - Net profit: $120,283 (gross $201,945, stressed costs $50,287)   Per year: $11,382
  - Average trade: $20.62   Avg winner $577.41 / avg loser -$584.99
  - Max drawdown: $20,638   Longest losing streak: 9 trades
  - Positive years: 9 of 11   Positive months: 69 of 127
  - Initial risk: 40.00 pts average ($800), median 40.00 pts
  - Target: 1R   Average winner +0.74R / average loser -0.71R   Average trade +0.026R net
  - Breakeven win rate: 50.0% before costs, 50.9% after costs (at the median risk); observed 52.1%
  - Breakeven implied by the realised average winner/loser: 50.3%
  - Warnings (descriptive): MANAGEMENT_CLIFF

### Interesting 2R+ strategy (by net)
`Cb90dfc8c7cf0f5db` -- NQ · range_position · both · entry class A_SIMPLE_EDGE · entry robustness BROAD_PLATEAU · management robustness MODERATE

- **Strategy family:** Range position (range_position; tier 1; complexity 1)
- **What it tests:** Where the close sits inside the previous N-bar high-low range (0 = low, 1 = high).
- **Instrument:** NQ
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when the close moves into the top 20% of the previous 60-bar range (or above it). SELL SHORT when the close moves into the bottom 20% of the previous 60-bar range (or below it). Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 40 points from the entry. Initial stop = 1R, single target at +2R. Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** edge=0.2, lookback=60, mode=continuation, window=rth
- **Management parameters:** stop=points points=40.0; management=RR_2R
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 4,322 (409.0 per year; 2,165 long / 2,157 short)
  - Win rate: 45.6%   Profit factor: 1.09 (before costs 1.14)
  - Net profit: $121,702 (gross $182,210, stressed costs $69,838)   Per year: $11,516
  - Average trade: $28.16   Avg winner $737.62 / avg loser -$565.52
  - Max drawdown: $26,827   Longest losing streak: 10 trades
  - Positive years: 6 of 11   Positive months: 66 of 127
  - Initial risk: 40.00 pts average ($800), median 40.00 pts
  - Target: 2R   Average winner +0.94R / average loser -0.69R   Average trade +0.035R net
  - Breakeven win rate: 33.3% before costs, 33.9% after costs (at the median risk); observed 45.6%
  - Breakeven implied by the realised average winner/loser: 43.4%

### Interesting 3R+ strategy (by net)
`Cd204fb526f04852e` -- NQ · time_of_day · long · entry class A_SIMPLE_EDGE · entry robustness MODERATE · management robustness BROAD_PLATEAU

- **Strategy family:** Time of day (time_of_day; tier 1; complexity 2)
- **What it tests:** Open a position at a fixed New York clock time every session and hold for a fixed time.
- **Instrument:** NQ
- **Direction:** Long only
- **ENTRY RULE:** BUY at the open of the 19:00 New York bar, every session. Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 2 x ATR(14 fifteen-minute bars) from the entry. Initial stop = 1R; move the stop to breakeven after +0.5R; target +3R. Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 18:00 to 15:30 New York, always flat by 16:00
- **Entry parameters:** entry_time=19:00, window=globex
- **Management parameters:** stop=atr mult=2.0; management=BE_0.5R_T3R
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 2,203 (208.5 per year; 2,203 long / 0 short)
  - Win rate: 16.6%   Profit factor: 1.45 (before costs 1.61)
  - Net profit: $133,003 (gross $163,845, stressed costs $106,567)   Per year: $12,585
  - Average trade: $60.37   Avg winner $1,174.71 / avg loser -$160.92
  - Max drawdown: $24,385   Longest losing streak: 33 trades
  - Positive years: 10 of 11   Positive months: 83 of 127
  - Initial risk: 20.01 pts average ($400), median 12.50 pts
  - Target: 3R   Average winner +2.76R / average loser -0.34R   Average trade +0.110R net
  - Breakeven implied by the realised average winner/loser: 12.0%
  - Breakeven rule +0.5R: moved to BE 1,571 trades, stopped at BE 1,207; of those, without BE 822 would have LOST and 379 would have WON (same-bar BE ambiguity: 20 trades)
  - Warnings (descriptive): LONG_LOSS_STREAK

### Highest-frequency profitable strategy
`C29a5f132ad01e545` -- NQ · fvg · both · entry class B_MANAGEMENT_RESCUED · entry robustness MODERATE · management robustness MODERATE

- **Strategy family:** Three-candle fair-value gap (fvg; tier 1; complexity 2)
- **What it tests:** Creation of, and first return into, a mechanically defined three-candle price gap.
- **Instrument:** NQ
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when price first trades back down into the most recent bullish 1-minute FVG. SELL SHORT when price first trades back up into the most recent bearish 1-minute FVG. Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 1 x ATR(14 fifteen-minute bars) from the entry. Initial stop = 1R, no target; trailing stop 2R below the highest high since entry, recomputed at every bar close, active from the start. Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** event=touch, min_gap=0.0, mode=continuation, timeframe=1, window=rth
- **Management parameters:** stop=atr mult=1.0; management=TRAIL_R_2_ACT0R
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 15,983 (1,512.4 per year; 8,058 long / 7,925 short)
  - Win rate: 31.9%   Profit factor: 1.01 (before costs 1.14)
  - Net profit: $10,108 (gross $233,870, stressed costs -$181,688)   Per year: $956
  - Average trade: $0.63   Avg winner $367.53 / avg loser -$171.10
  - Max drawdown: $75,247   Longest losing streak: 21 trades
  - Positive years: 4 of 11   Positive months: 52 of 127
  - Initial risk: 9.44 pts average ($189), median 6.25 pts
  - Target: -   Average winner +2.01R / average loser -0.85R   Average trade -0.063R net
  - Breakeven implied by the realised average winner/loser: 31.8%
  - Warnings (descriptive): HIGH_DRAWDOWN,PNL_CONCENTRATED,ONE_YEAR_DOMINATED,ONE_MONTH_DOMINATED,LONG_SIDE_DEPENDENT,COST_SENSITIVE,THIN_EDGE,UNSTABLE_YEARLY_RESULTS,LONG_LOSS_STREAK

### Profitable lower-frequency strategy (25-100 trades/yr, by net)
`C0d75271ed2c07270` -- NQ · consecutive_bars · both · entry class A_SIMPLE_EDGE · entry robustness MODERATE · management robustness CLIFF

- **Strategy family:** Consecutive directional bars (consecutive_bars; tier 1; complexity 1)
- **What it tests:** Acts on the bar that completes a run of exactly N higher (or lower) closes.
- **Instrument:** NQ
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when a bar completes a run of 8 consecutive lower closes. SELL SHORT when a bar completes a run of 8 consecutive higher closes. Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** No stop, no target. Hold until the session flat time (16:00 New York). Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** mode=reversal, n=8, window=rth
- **Management parameters:** stop=none; management=TIME_eod
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 1,004 (95.0 per year; 484 long / 520 short)
  - Win rate: 48.3%   Profit factor: 1.25 (before costs 1.30)
  - Net profit: $76,244 (gross $90,300, stressed costs $64,196)   Per year: $7,215
  - Average trade: $75.94   Avg winner $788.63 / avg loser -$590.06
  - Max drawdown: $16,853   Longest losing streak: 10 trades
  - Positive years: 5 of 11   Positive months: 61 of 127
  - Breakeven implied by the realised average winner/loser: 42.8%
  - Warnings (descriptive): MANAGEMENT_CLIFF,UNSTABLE_YEARLY_RESULTS

### Largest discovery net P&L
`C76caff7585ad0adf` -- NQ · range_position · both · entry class A_SIMPLE_EDGE · entry robustness BROAD_PLATEAU · management robustness MODERATE

- **Strategy family:** Range position (range_position; tier 1; complexity 1)
- **What it tests:** Where the close sits inside the previous N-bar high-low range (0 = low, 1 = high).
- **Instrument:** NQ
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when the close moves into the top 33% of the previous 30-bar range (or above it). SELL SHORT when the close moves into the bottom 33% of the previous 30-bar range (or below it). Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** No stop, no target. Hold until the session flat time (16:00 New York). Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** edge=0.33, lookback=30, mode=continuation, window=rth
- **Management parameters:** stop=none; management=TIME_eod
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 2,710 (256.4 per year; 1,373 long / 1,337 short)
  - Win rate: 50.9%   Profit factor: 1.20 (before costs 1.25)
  - Net profit: $162,955 (gross $200,895, stressed costs $130,435)   Per year: $15,420
  - Average trade: $60.13   Avg winner $705.93 / avg loser -$609.95
  - Max drawdown: $22,670   Longest losing streak: 11 trades
  - Positive years: 9 of 11   Positive months: 69 of 127
  - Breakeven implied by the realised average winner/loser: 46.4%

### Low drawdown relative to profit (>= 100 trades, above-median net)
`C060d3c8c87c84fec` -- NQ · gap · long · entry class A_SIMPLE_EDGE · entry robustness BROAD_PLATEAU · management robustness BROAD_PLATEAU

- **Strategy family:** Opening gap (gap; tier 1; complexity 2)
- **What it tests:** Trade the RTH opening gap either as continuation or as a fade toward the prior close.
- **Instrument:** NQ
- **Direction:** Long only
- **ENTRY RULE:** BUY when the RTH open is below the prior RTH close by more than 0.5 x the 10-session average RTH range (decided at the close of the 09:30 bar). Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 1 x ATR(14 fifteen-minute bars) from the entry. Initial stop = 1R, no target; trailing stop 0.5R below the highest high since entry, recomputed at every bar close, active from the start. Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** mode=reversal, threshold=0.5, window=rth
- **Management parameters:** stop=atr mult=1.0; management=TRAIL_R_0.5_ACT0R
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 297 (28.1 per year; 297 long / 0 short)
  - Win rate: 51.9%   Profit factor: 3.02 (before costs 4.04)
  - Net profit: $19,722 (gross $23,880, stressed costs $16,158)   Per year: $1,866
  - Average trade: $66.40   Avg winner $191.58 / avg loser -$68.41
  - Max drawdown: $1,024   Longest losing streak: 12 trades
  - Positive years: 9 of 11   Positive months: 71 of 114
  - Initial risk: 9.39 pts average ($188), median 6.00 pts
  - Target: -   Average winner +0.92R / average loser -0.40R   Average trade +0.157R net
  - Breakeven implied by the realised average winner/loser: 26.3%

### Broad plateau in BOTH entry and management (by net)
`Ce3b50b15539d3e22` -- NQ · time_of_day · long · entry class A_SIMPLE_EDGE · entry robustness BROAD_PLATEAU · management robustness BROAD_PLATEAU

- **Strategy family:** Time of day (time_of_day; tier 1; complexity 2)
- **What it tests:** Open a position at a fixed New York clock time every session and hold for a fixed time.
- **Instrument:** NQ
- **Direction:** Long only
- **ENTRY RULE:** BUY at the open of the 19:00 New York bar, every session. Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 2 x ATR(14 fifteen-minute bars) from the entry. Initial stop = 1R; move the stop to breakeven after +2R; no target (held to the flat time). Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 18:00 to 15:30 New York, always flat by 16:00
- **Entry parameters:** entry_time=19:00, window=globex
- **Management parameters:** stop=atr mult=2.0; management=BE_2R_Tnone
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 2,203 (208.5 per year; 2,203 long / 0 short)
  - Win rate: 26.6%   Profit factor: 1.26 (before costs 1.34)
  - Net profit: $143,733 (gross $174,575, stressed costs $117,297)   Per year: $13,601
  - Average trade: $65.24   Avg winner $1,169.75 / avg loser -$335.96
  - Max drawdown: $17,464   Longest losing streak: 17 trades
  - Positive years: 9 of 11   Positive months: 78 of 127
  - Initial risk: 20.01 pts average ($400), median 12.50 pts
  - Target: -   Average winner +3.01R / average loser -0.80R   Average trade +0.156R net
  - Breakeven implied by the realised average winner/loser: 22.3%
  - Breakeven rule +2R: moved to BE 797 trades, stopped at BE 306; of those, without BE 206 would have LOST and 99 would have WON (same-bar BE ambiguity: 0 trades)
  - Warnings (descriptive): LONG_LOSS_STREAK

### Parameter CLIFF but very profitable
`C8608ad2cef5c55b5` -- NQ · candles · both · entry class A_SIMPLE_EDGE · entry robustness CLIFF · management robustness CLIFF

- **Strategy family:** Candle structure (candles; tier 1; complexity 1)
- **What it tests:** Simple, mechanically defined candle shapes on 1, 5 or 15-minute bars.
- **Instrument:** NQ
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when a completed 15-minute bar closes UP with its body at least 0.6 of its range. SELL SHORT when a completed 15-minute bar closes DOWN with its body at least 0.6 of its range. Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 1 x ATR(14 fifteen-minute bars) from the entry. Initial stop only, no target; otherwise exit after the session flat time (16:00 New York). Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** mode=continuation, pattern=body_0.6, timeframe=15, window=rth
- **Management parameters:** stop=atr mult=1.0; management=STOP_TIME_eod
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 7,096 (671.5 per year; 3,671 long / 3,425 short)
  - Win rate: 26.7%   Profit factor: 1.08 (before costs 1.19)
  - Net profit: $86,056 (gross $185,400, stressed costs $904)   Per year: $8,143
  - Average trade: $12.13   Avg winner $608.60 / avg loser -$205.04
  - Max drawdown: $25,953   Longest losing streak: 22 trades
  - Positive years: 4 of 11   Positive months: 64 of 127
  - Initial risk: 10.26 pts average ($205), median 6.75 pts
  - Target: -   Average winner +3.04R / average loser -0.97R   Average trade -0.011R net
  - Breakeven implied by the realised average winner/loser: 25.2%
  - Warnings (descriptive): PNL_CONCENTRATED,THIN_EDGE,PARAMETER_CLIFF,ENTRY_CLIFF,MANAGEMENT_CLIFF,UNSTABLE_YEARLY_RESULTS,LONG_LOSS_STREAK

### Breakeven-improved (largest uplift vs the same target without BE)
`Cd0510e6ec7a64c8e` -- NQ · consecutive_bars · both · entry class B_MANAGEMENT_RESCUED · entry robustness CLIFF · management robustness CLIFF

- **Strategy family:** Consecutive directional bars (consecutive_bars; tier 1; complexity 2)
- **What it tests:** Acts on the bar that completes a run of exactly N higher (or lower) closes.
- **Instrument:** NQ
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when a bar completes a run of 3 consecutive higher closes. SELL SHORT when a bar completes a run of 3 consecutive lower closes. Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 2 x ATR(14 fifteen-minute bars) from the entry. Initial stop = 1R; move the stop to breakeven after +0.75R; no target (held to the flat time). Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** mode=continuation, n=3, window=rth
- **Management parameters:** stop=atr mult=2.0; management=BE_0.75R_Tnone
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 8,795 (832.2 per year; 4,503 long / 4,292 short)
  - Win rate: 21.6%   Profit factor: 1.02 (before costs 1.12)
  - Net profit: $18,960 (gross $142,090, stressed costs -$86,580)   Per year: $1,794
  - Average trade: $2.16   Avg winner $661.10 / avg loser -$179.79
  - Max drawdown: $86,065   Longest losing streak: 20 trades
  - Positive years: 3 of 11   Positive months: 51 of 127
  - Initial risk: 17.40 pts average ($348), median 11.25 pts
  - Target: -   Average winner +1.94R / average loser -0.51R   Average trade -0.046R net
  - Breakeven implied by the realised average winner/loser: 21.4%
  - Breakeven rule +0.75R: moved to BE 4,693 trades, stopped at BE 3,082; of those, without BE 1,460 would have LOST and 640 would have WON (same-bar BE ambiguity: 227 trades)
  - Warnings (descriptive): HIGH_DRAWDOWN,PNL_CONCENTRATED,ONE_YEAR_DOMINATED,LONG_SIDE_DEPENDENT,COST_SENSITIVE,THIN_EDGE,PARAMETER_CLIFF,ENTRY_CLIFF,MANAGEMENT_CLIFF,UNSTABLE_YEARLY_RESULTS,LONG_LOSS_STREAK

### Trailing-stop-improved (largest uplift vs stop + hold to close)
`C410be26d2ba29c8a` -- NQ · fvg · both · entry class A_SIMPLE_EDGE · entry robustness MODERATE · management robustness MODERATE

- **Strategy family:** Three-candle fair-value gap (fvg; tier 1; complexity 2)
- **What it tests:** Creation of, and first return into, a mechanically defined three-candle price gap.
- **Instrument:** NQ
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when price first trades back down into the most recent bullish 5-minute FVG. SELL SHORT when price first trades back up into the most recent bearish 5-minute FVG. Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short). Initial stop = 1R, no target; trailing stop 1R below the highest high since entry, recomputed at every bar close, active from the start. Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** event=touch, min_gap=0.0, mode=continuation, timeframe=5, window=rth
- **Management parameters:** stop=swing; management=TRAIL_R_1_ACT0R
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 8,280 (783.5 per year; 4,188 long / 4,092 short)
  - Win rate: 38.7%   Profit factor: 1.11 (before costs 1.23)
  - Net profit: $126,100 (gross $242,020, stressed costs $26,740)   Per year: $11,932
  - Average trade: $15.23   Avg winner $387.91 / avg loser -$220.13
  - Max drawdown: $44,988   Longest losing streak: 14 trades
  - Positive years: 4 of 11   Positive months: 67 of 127
  - Initial risk: 20.72 pts average ($414), median 13.25 pts
  - Target: -   Average winner +0.97R / average loser -0.55R   Average trade -0.041R net
  - Breakeven implied by the realised average winner/loser: 36.2%
  - Warnings (descriptive): PNL_CONCENTRATED,UNSTABLE_YEARLY_RESULTS

### Partial-exit-improved (largest uplift vs a single target)
`C59daaf6b52312ab6` -- NQ · fvg · both · entry class A_SIMPLE_EDGE · entry robustness MODERATE · management robustness NO_NEIGHBOURS

- **Strategy family:** Three-candle fair-value gap (fvg; tier 1; complexity 2)
- **What it tests:** Creation of, and first return into, a mechanically defined three-candle price gap.
- **Instrument:** NQ
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when a bullish 5-minute FVG of at least 0.25 x ATR60 x sqrt(5) completes. SELL SHORT when a bearish 5-minute FVG of at least 0.25 x ATR60 x sqrt(5) completes. Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 1 x ATR(14 fifteen-minute bars) from the entry. Take 66% at +1R, the last 34% at +3R. Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** event=create, min_gap=0.25, mode=continuation, timeframe=5, window=rth
- **Management parameters:** stop=atr mult=1.0; management=PARTIAL_I
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 9,588 (907.3 per year; 4,811 long / 4,777 short)
  - Win rate: 51.6%   Profit factor: 1.01 (before costs 1.15)
  - Net profit: $5,396 (gross $139,628, stressed costs -$109,660)   Per year: $511
  - Average trade: $0.56   Avg winner $203.40 / avg loser -$215.29
  - Max drawdown: $53,115   Longest losing streak: 11 trades
  - Positive years: 4 of 11   Positive months: 51 of 127
  - Initial risk: 10.47 pts average ($209), median 7.00 pts
  - Target: 3R   Average winner +1.03R / average loser -0.97R   Average trade -0.054R net
  - Breakeven implied by the realised average winner/loser: 51.4%
  - Partial structure 66%@1R / 34%@3R: first leg gross $64,574, remainder/runner gross $75,053, combined gross $139,628
  - Warnings (descriptive): HIGH_DRAWDOWN,PNL_CONCENTRATED,ONE_YEAR_DOMINATED,ONE_MONTH_DOMINATED,LONG_SIDE_DEPENDENT,COST_SENSITIVE,THIN_EDGE,UNSTABLE_YEARLY_RESULTS

### Runner-improved (largest uplift vs a single target)
`C4a05b59d983b0f71` -- NQ · fvg · both · entry class A_SIMPLE_EDGE · entry robustness MODERATE · management robustness NO_NEIGHBOURS

- **Strategy family:** Three-candle fair-value gap (fvg; tier 1; complexity 2)
- **What it tests:** Creation of, and first return into, a mechanically defined three-candle price gap.
- **Instrument:** NQ
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when a bullish 5-minute FVG of at least 0.25 x ATR60 x sqrt(5) completes. SELL SHORT when a bearish 5-minute FVG of at least 0.25 x ATR60 x sqrt(5) completes. Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 1 x ATR(14 fifteen-minute bars) from the entry. Take 50% at +1R; the 50% runner exits at +4R. Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** event=create, min_gap=0.25, mode=continuation, timeframe=5, window=rth
- **Management parameters:** stop=atr mult=1.0; management=RUNNER_4R
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 8,752 (828.2 per year; 4,399 long / 4,353 short)
  - Win rate: 32.6%   Profit factor: 1.04 (before costs 1.19)
  - Net profit: $38,952 (gross $161,480, stressed costs -$66,072)   Per year: $3,686
  - Average trade: $4.45   Avg winner $337.92 / avg loser -$156.66
  - Max drawdown: $31,530   Longest losing streak: 20 trades
  - Positive years: 4 of 11   Positive months: 60 of 127
  - Initial risk: 10.37 pts average ($207), median 7.00 pts
  - Target: 4R   Average winner +1.68R / average loser -0.70R   Average trade -0.039R net
  - Breakeven implied by the realised average winner/loser: 31.7%
  - Partial structure 50%@1R / 50%@4R: first leg gross $47,042, remainder/runner gross $114,438, combined gross $161,480
  - Warnings (descriptive): PNL_CONCENTRATED,ONE_YEAR_DOMINATED,LONG_SIDE_DEPENDENT,COST_SENSITIVE,THIN_EDGE,UNSTABLE_YEARLY_RESULTS,LONG_LOSS_STREAK

### Simple Tier-1 strategy (complexity 1, by net) (same candidate as above)
`C76caff7585ad0adf` -- NQ · range_position · both · entry class A_SIMPLE_EDGE · entry robustness BROAD_PLATEAU · management robustness MODERATE

- **Strategy family:** Range position (range_position; tier 1; complexity 1)
- **What it tests:** Where the close sits inside the previous N-bar high-low range (0 = low, 1 = high).
- **Instrument:** NQ
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when the close moves into the top 33% of the previous 30-bar range (or above it). SELL SHORT when the close moves into the bottom 33% of the previous 30-bar range (or below it). Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** No stop, no target. Hold until the session flat time (16:00 New York). Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** edge=0.33, lookback=30, mode=continuation, window=rth
- **Management parameters:** stop=none; management=TIME_eod
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 2,710 (256.4 per year; 1,373 long / 1,337 short)
  - Win rate: 50.9%   Profit factor: 1.20 (before costs 1.25)
  - Net profit: $162,955 (gross $200,895, stressed costs $130,435)   Per year: $15,420
  - Average trade: $60.13   Avg winner $705.93 / avg loser -$609.95
  - Max drawdown: $22,670   Longest losing streak: 11 trades
  - Positive years: 9 of 11   Positive months: 69 of 127
  - Breakeven implied by the realised average winner/loser: 46.4%

### Tier-2 strategy (by net)
`C921a68c1e0ac0127` -- NQ · multi_timeframe · both · entry class A_SIMPLE_EDGE · entry robustness MODERATE · management robustness CLIFF

- **Strategy family:** Higher-timeframe direction + 1-minute trigger (multi_timeframe; tier 2; complexity 2)
- **What it tests:** Take a 1-minute momentum trigger only when the higher timeframe points one way.
- **Instrument:** NQ
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when the last completed 15-minute close is below the 15-minute close 3 bar(s) before it and the 15-minute move crosses above +1.0 x ATR60 x sqrt(15) (a rally in a down-trend). SELL SHORT when the last completed 15-minute close is above the 15-minute close 3 bar(s) before it and the 15-minute move crosses below -1.0 x ATR60 x sqrt(15) (a dip in an up-trend). Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 40 points from the entry. Initial stop = 1R, single target at +2R. Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** htf=15, htf_lookback=3, ltf_lookback=15, mode=reversal, trigger=pullback, window=rth, z=1.0
- **Management parameters:** stop=points points=40.0; management=RR_2R
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 3,230 (305.6 per year; 1,664 long / 1,566 short)
  - Win rate: 47.6%   Profit factor: 1.10 (before costs 1.17)
  - Net profit: $82,955 (gross $128,175, stressed costs $44,195)   Per year: $7,850
  - Average trade: $25.68   Avg winner $571.63 / avg loser -$469.34
  - Max drawdown: $36,658   Longest losing streak: 10 trades
  - Positive years: 7 of 11   Positive months: 70 of 127
  - Initial risk: 40.00 pts average ($800), median 40.00 pts
  - Target: 2R   Average winner +0.73R / average loser -0.57R   Average trade +0.032R net
  - Breakeven win rate: 33.3% before costs, 33.9% after costs (at the median risk); observed 47.6%
  - Breakeven implied by the realised average winner/loser: 45.1%
  - Warnings (descriptive): MANAGEMENT_CLIFF

### NQ candidate (by net) (same candidate as above)
`C76caff7585ad0adf` -- NQ · range_position · both · entry class A_SIMPLE_EDGE · entry robustness BROAD_PLATEAU · management robustness MODERATE

- **Strategy family:** Range position (range_position; tier 1; complexity 1)
- **What it tests:** Where the close sits inside the previous N-bar high-low range (0 = low, 1 = high).
- **Instrument:** NQ
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when the close moves into the top 33% of the previous 30-bar range (or above it). SELL SHORT when the close moves into the bottom 33% of the previous 30-bar range (or below it). Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** No stop, no target. Hold until the session flat time (16:00 New York). Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** edge=0.33, lookback=30, mode=continuation, window=rth
- **Management parameters:** stop=none; management=TIME_eod
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 2,710 (256.4 per year; 1,373 long / 1,337 short)
  - Win rate: 50.9%   Profit factor: 1.20 (before costs 1.25)
  - Net profit: $162,955 (gross $200,895, stressed costs $130,435)   Per year: $15,420
  - Average trade: $60.13   Avg winner $705.93 / avg loser -$609.95
  - Max drawdown: $22,670   Longest losing streak: 11 trades
  - Positive years: 9 of 11   Positive months: 69 of 127
  - Breakeven implied by the realised average winner/loser: 46.4%

### ES candidate (by net)
`C3796048e40101924` -- ES · time_of_day · long · entry class A_SIMPLE_EDGE · entry robustness BROAD_PLATEAU · management robustness CLIFF

- **Strategy family:** Time of day (time_of_day; tier 1; complexity 1)
- **What it tests:** Open a position at a fixed New York clock time every session and hold for a fixed time.
- **Instrument:** ES
- **Direction:** Long only
- **ENTRY RULE:** BUY at the open of the 19:30 New York bar, every session. Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** No stop, no target. Hold until the session flat time (16:00 New York). Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 18:00 to 15:30 New York, always flat by 16:00
- **Entry parameters:** entry_time=19:30, window=globex
- **Management parameters:** stop=none; management=TIME_eod
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 2,612 (247.2 per year; 2,612 long / 0 short)
  - Win rate: 53.6%   Profit factor: 1.10 (before costs 1.20)
  - Net profit: $89,177 (gross $164,925, stressed costs $18,653)   Per year: $8,438
  - Average trade: $34.14   Avg winner $684.10 / avg loser -$717.79
  - Max drawdown: $40,482   Longest losing streak: 9 trades
  - Positive years: 10 of 11   Positive months: 79 of 127
  - Breakeven implied by the realised average winner/loser: 51.2%
  - Warnings (descriptive): PNL_CONCENTRATED,MANAGEMENT_CLIFF

### Entry that ONLY works with sophisticated management (class B, by net)
`C64d04297f322a6c2` -- NQ · momentum · both · entry class B_MANAGEMENT_RESCUED · entry robustness BROAD_PLATEAU · management robustness MODERATE

- **Strategy family:** N-bar momentum (momentum; tier 1; complexity 3)
- **What it tests:** Measures the move over the previous N one-minute bars in volatility units and acts the first bar it exceeds a threshold.
- **Instrument:** NQ
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when the close has fallen at least 0.5 x ATR60 x sqrt(5) below the close 5 minutes earlier (first bar this becomes true). SELL SHORT when the close has risen at least 0.5 x ATR60 x sqrt(5) above the close 5 minutes earlier (first bar this becomes true). Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short). Initial stop = 1R, no target; trailing stop 2 ATR below the highest close since entry, recomputed at every bar close, active once the trade has been +1R in favour. Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 12:00 to 15:30 New York, always flat by 16:00
- **Entry parameters:** lookback=5, mode=reversal, window=rth_pm, z=0.5
- **Management parameters:** stop=swing; management=TRAIL_CLOSE_ATR_2_ACT1R
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 5,456 (516.3 per year; 2,755 long / 2,701 short)
  - Win rate: 35.4%   Profit factor: 1.12 (before costs 1.25)
  - Net profit: $87,226 (gross $163,610, stressed costs $21,754)   Per year: $8,254
  - Average trade: $15.99   Avg winner $411.75 / avg loser -$201.34
  - Max drawdown: $24,579   Longest losing streak: 17 trades
  - Positive years: 4 of 11   Positive months: 55 of 127
  - Initial risk: 16.61 pts average ($332), median 9.75 pts
  - Target: -   Average winner +1.46R / average loser -0.80R   Average trade -0.212R net
  - Breakeven implied by the realised average winner/loser: 32.8%
  - Warnings (descriptive): PNL_CONCENTRATED,ONE_YEAR_DOMINATED,UNSTABLE_YEARLY_RESULTS,LONG_LOSS_STREAK

### Entry that works under MANY management methods (class D, by net)
`C38d442210c771367` -- NQ · time_of_day · long · entry class A_SIMPLE_EDGE · entry robustness BROAD_PLATEAU · management robustness MODERATE

- **Strategy family:** Time of day (time_of_day; tier 1; complexity 1)
- **What it tests:** Open a position at a fixed New York clock time every session and hold for a fixed time.
- **Instrument:** NQ
- **Direction:** Long only
- **ENTRY RULE:** BUY at the open of the 19:00 New York bar, every session. Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** No stop, no target. Hold until the session flat time (16:00 New York). Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 18:00 to 15:30 New York, always flat by 16:00
- **Entry parameters:** entry_time=19:00, window=globex
- **Management parameters:** stop=none; management=TIME_eod
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 2,238 (211.8 per year; 2,238 long / 0 short)
  - Win rate: 55.6%   Profit factor: 1.17 (before costs 1.21)
  - Net profit: $160,633 (gross $191,965, stressed costs $133,777)   Per year: $15,200
  - Average trade: $71.78   Avg winner $883.06 / avg loser -$945.39
  - Max drawdown: $39,182   Longest losing streak: 8 trades
  - Positive years: 9 of 11   Positive months: 81 of 127
  - Breakeven implied by the realised average winner/loser: 51.7%
  - Warnings (descriptive): PNL_CONCENTRATED

### Most positive discovery years (then net)
`Cbf42c052aae5d5be` -- NQ · momentum · long · entry class A_SIMPLE_EDGE · entry robustness MODERATE · management robustness BROAD_PLATEAU

- **Strategy family:** N-bar momentum (momentum; tier 1; complexity 2)
- **What it tests:** Measures the move over the previous N one-minute bars in volatility units and acts the first bar it exceeds a threshold.
- **Instrument:** NQ
- **Direction:** Long only
- **ENTRY RULE:** BUY when the close has risen at least 1.5 x ATR60 x sqrt(30) above the close 30 minutes earlier (first bar this becomes true). Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** Initial stop 20 points from the entry. Initial stop = 1R, single target at +2R. Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 12:00 New York, always flat by 16:00
- **Entry parameters:** lookback=30, mode=continuation, window=rth_am, z=1.5
- **Management parameters:** stop=points points=20.0; management=RR_2R
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 903 (85.4 per year; 903 long / 0 short)
  - Win rate: 49.2%   Profit factor: 1.18 (before costs 1.28)
  - Net profit: $28,088 (gross $40,730, stressed costs $17,252)   Per year: $2,658
  - Average trade: $31.11   Avg winner $409.63 / avg loser -$335.05
  - Max drawdown: $7,203   Longest losing streak: 9 trades
  - Positive years: 11 of 11   Positive months: 77 of 127
  - Initial risk: 20.00 pts average ($400), median 20.00 pts
  - Target: 2R   Average winner +1.06R / average loser -0.80R   Average trade +0.078R net
  - Breakeven win rate: 33.3% before costs, 34.5% after costs (at the median risk); observed 49.2%
  - Breakeven implied by the realised average winner/loser: 45.0%

### Plain time exit, no stop (by net) (same candidate as above)
`C76caff7585ad0adf` -- NQ · range_position · both · entry class A_SIMPLE_EDGE · entry robustness BROAD_PLATEAU · management robustness MODERATE

- **Strategy family:** Range position (range_position; tier 1; complexity 1)
- **What it tests:** Where the close sits inside the previous N-bar high-low range (0 = low, 1 = high).
- **Instrument:** NQ
- **Direction:** Long and short (one position at a time)
- **ENTRY RULE:** BUY when the close moves into the top 33% of the previous 30-bar range (or above it). SELL SHORT when the close moves into the bottom 33% of the previous 30-bar range (or below it). Orders are market orders filled at the OPEN of the next one-minute bar.
- **MANAGEMENT RULE:** No stop, no target. Hold until the session flat time (16:00 New York). Always flat at the session flat time (16:00 New York).
- **Trading hours:** entries from 09:30 to 15:30 New York, always flat by 16:00
- **Entry parameters:** edge=0.33, lookback=30, mode=continuation, window=rth
- **Management parameters:** stop=none; management=TIME_eod
- **Costs:** costs_v2_approved_2026-09-21#a27ed5df0c04

  - Trades: 2,710 (256.4 per year; 1,373 long / 1,337 short)
  - Win rate: 50.9%   Profit factor: 1.20 (before costs 1.25)
  - Net profit: $162,955 (gross $200,895, stressed costs $130,435)   Per year: $15,420
  - Average trade: $60.13   Avg winner $705.93 / avg loser -$609.95
  - Max drawdown: $22,670   Longest losing streak: 11 trades
  - Positive years: 9 of 11   Positive months: 69 of 127
  - Breakeven implied by the realised average winner/loser: 46.4%
