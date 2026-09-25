# RULE CARDS -- FINAL FROZEN COHORT

```
STRATEGY ID:   C39d55eaa5412f438   (FINAL FORWARD CANDIDATE)
CLUSTER:       stronger-subset cluster 0 -- CLEARLY ABOVE NULL (981 members, 22 entry rules)
INSTRUMENT:    NQ, 1 contract
DIRECTION:     Long only

ENTRY:         BUY when the close is at least 1.0 x ATR60 x sqrt(60) ABOVE the average of the previous 60 closes (first bar). Orders are market orders filled at the OPEN of the next one-minute bar.
INITIAL STOP:  Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short).
PROFIT MANAGEMENT: Initial stop only, no target; otherwise exit after the session flat time (16:00 New York). Always flat at the session flat time (16:00 New York).
TRADING HOURS: entries from 09:30 to 15:30 New York, always flat by 16:00
MAX HOLD:      until the session flat time (16:00 New York) at the latest; never overnight
PARAMETERS:    anchor=sma, lookback=60, mode=continuation, window=rth, z=1.0; stop=swing; management=STOP_TIME_eod
COST ASSUMPTION: baseline $14.00 per round trip ($4 commission + 1 tick slippage each side)
HISTORICAL CONTEXT (selection data, NOT independent evidence): discovery 2010-2020 845 trades, PF 1.09; 2021-2026(cutoff) 381 trades, PF 1.70, WR 55.1%, net $193,206, max DD $18,206
               yearly: 2021 PF 2.32 (74 tr); 2022 PF 1.52 (76 tr); 2023 PF 1.65 (68 tr); 2024 PF 1.07 (67 tr); 2025 PF 1.69 (61 tr); 2026 PF 2.92 (35 tr)
ROBUSTNESS:    entry parameters MODERATE; management BROAD_PLATEAU
NULL EVIDENCE: cluster CLEARLY ABOVE NULL (p_size 0.0050, p_entries 0.0100, p_strong 0.0050; 200 null worlds)
FORWARD STATUS: NOT STARTED
```

```
STRATEGY ID:   C175c690afa915a44   (FINAL FORWARD CANDIDATE)
CLUSTER:       stronger-subset cluster 1 -- CLEARLY ABOVE NULL (632 members, 22 entry rules)
INSTRUMENT:    NQ, 1 contract
DIRECTION:     Long and short (one position at a time)

ENTRY:         BUY when the close has risen at least 1.5 x ATR60 x sqrt(30) above the close 30 minutes earlier (first bar this becomes true). SELL SHORT when the close has fallen at least 1.5 x ATR60 x sqrt(30) below the close 30 minutes earlier (first bar this becomes true). Orders are market orders filled at the OPEN of the next one-minute bar.
INITIAL STOP:  Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short).
PROFIT MANAGEMENT: Initial stop = 1R, no target; trailing stop 1.5R below the highest high since entry, recomputed at every bar close, active once the trade has been +1.5R in favour. Always flat at the session flat time (16:00 New York).
TRADING HOURS: entries from 09:30 to 15:30 New York, always flat by 16:00
MAX HOLD:      until the session flat time (16:00 New York) at the latest; never overnight
PARAMETERS:    lookback=30, mode=continuation, window=rth, z=1.5; stop=swing; management=TRAIL_R_1.5_ACT1.5R
COST ASSUMPTION: baseline $14.00 per round trip ($4 commission + 1 tick slippage each side)
HISTORICAL CONTEXT (selection data, NOT independent evidence): discovery 2010-2020 2632 trades, PF 1.03; 2021-2026(cutoff) 1274 trades, PF 1.32, WR 50.9%, net $352,829, max DD $28,987
               yearly: 2021 PF 1.49 (258 tr); 2022 PF 1.28 (231 tr); 2023 PF 1.03 (218 tr); 2024 PF 1.22 (217 tr); 2025 PF 1.49 (221 tr); 2026 PF 1.41 (129 tr)
ROBUSTNESS:    entry parameters BROAD_PLATEAU; management BROAD_PLATEAU
NULL EVIDENCE: cluster CLEARLY ABOVE NULL (p_size 0.0050, p_entries 0.0100, p_strong 0.0050; 200 null worlds)
FORWARD STATUS: NOT STARTED
```

```
STRATEGY ID:   C21fa22c47ad5c1cd   (FINAL FORWARD CANDIDATE)
CLUSTER:       stronger-subset cluster 2 -- CLEARLY ABOVE NULL (496 members, 9 entry rules)
INSTRUMENT:    NQ, 1 contract
DIRECTION:     Long and short (one position at a time)

ENTRY:         BUY when the close has risen at least 3.0 x ATR60 x sqrt(10) above the close 10 minutes earlier (first bar this becomes true). SELL SHORT when the close has fallen at least 3.0 x ATR60 x sqrt(10) below the close 10 minutes earlier (first bar this becomes true). Orders are market orders filled at the OPEN of the next one-minute bar.
INITIAL STOP:  Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short).
PROFIT MANAGEMENT: Initial stop = 1R, single target at +1.5R. Always flat at the session flat time (16:00 New York).
TRADING HOURS: entries from 09:30 to 15:30 New York, always flat by 16:00
MAX HOLD:      until the session flat time (16:00 New York) at the latest; never overnight
PARAMETERS:    lookback=10, mode=continuation, window=rth, z=3.0; stop=swing; management=RR_1.5R
COST ASSUMPTION: baseline $14.00 per round trip ($4 commission + 1 tick slippage each side)
HISTORICAL CONTEXT (selection data, NOT independent evidence): discovery 2010-2020 725 trades, PF 1.08; 2021-2026(cutoff) 289 trades, PF 1.52, WR 51.2%, net $130,704, max DD $18,280
               yearly: 2021 PF 1.12 (71 tr); 2022 PF 1.57 (45 tr); 2023 PF 1.01 (44 tr); 2024 PF 2.22 (43 tr); 2025 PF 1.26 (58 tr); 2026 PF 2.68 (28 tr)
ROBUSTNESS:    entry parameters NARROW; management BROAD_PLATEAU
NULL EVIDENCE: cluster CLEARLY ABOVE NULL (p_size 0.0050, p_entries 0.0846, p_strong 0.0050; 200 null worlds)
FORWARD STATUS: NOT STARTED
```

```
STRATEGY ID:   C7162dcd77274b6f3   (FINAL FORWARD CANDIDATE)
CLUSTER:       stronger-subset cluster 3 -- MIXED (298 members, 3 entry rules)
INSTRUMENT:    NQ (uses ES as information only), 1 contract
DIRECTION:     Long and short (one position at a time)

ENTRY:         BUY when this market's 30-minute move beats the other index future's by more than 1.0 volatility units. SELL SHORT when this market's 30-minute move trails the other index future's by more than 1.0 volatility units. Orders are market orders filled at the OPEN of the next one-minute bar.
INITIAL STOP:  Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short).
PROFIT MANAGEMENT: Initial stop = 1R, single target at +2R. Always flat at the session flat time (16:00 New York).
TRADING HOURS: entries from 09:30 to 15:30 New York, always flat by 16:00
MAX HOLD:      until the session flat time (16:00 New York) at the latest; never overnight
PARAMETERS:    kind=relative, lookback=30, mode=continuation, window=rth, z=1.0; stop=swing; management=RR_2R
COST ASSUMPTION: baseline $14.00 per round trip ($4 commission + 1 tick slippage each side)
HISTORICAL CONTEXT (selection data, NOT independent evidence): discovery 2010-2020 1354 trades, PF 1.02; 2021-2026(cutoff) 594 trades, PF 1.51, WR 44.4%, net $150,929, max DD $23,342
               yearly: 2021 PF 1.20 (225 tr); 2022 PF 1.58 (52 tr); 2023 PF 1.32 (111 tr); 2024 PF 1.32 (99 tr); 2025 PF 2.60 (64 tr); 2026 PF 1.96 (43 tr)
ROBUSTNESS:    entry parameters MODERATE; management BROAD_PLATEAU
NULL EVIDENCE: cluster MIXED (p_size 0.0199, p_entries 0.6418, p_strong 0.0199; 200 null worlds)
FORWARD STATUS: NOT STARTED
```

```
STRATEGY ID:   C3dc5dc6a88e523c7   (FINAL FORWARD CANDIDATE)
CLUSTER:       stronger-subset cluster 4 -- MIXED (271 members, 2 entry rules)
INSTRUMENT:    NQ, 1 contract
DIRECTION:     Long only

ENTRY:         BUY when the close has risen at least 1.0 x ATR60 x sqrt(240) above the close 240 minutes earlier (first bar this becomes true). Orders are market orders filled at the OPEN of the next one-minute bar.
INITIAL STOP:  Initial stop 1 tick beyond the last confirmed 5-minute swing low (long) / high (short).
PROFIT MANAGEMENT: Initial stop = 1R, single target at +2R. Always flat at the session flat time (16:00 New York).
TRADING HOURS: entries from 09:30 to 12:00 New York, always flat by 16:00
MAX HOLD:      until the session flat time (16:00 New York) at the latest; never overnight
PARAMETERS:    lookback=240, mode=continuation, window=rth_am, z=1.0; stop=swing; management=RR_2R
COST ASSUMPTION: baseline $14.00 per round trip ($4 commission + 1 tick slippage each side)
HISTORICAL CONTEXT (selection data, NOT independent evidence): discovery 2010-2020 542 trades, PF 1.33; 2021-2026(cutoff) 293 trades, PF 1.38, WR 57.0%, net $74,243, max DD $15,870
               yearly: 2021 PF 1.39 (62 tr); 2022 PF 1.48 (47 tr); 2023 PF 1.31 (49 tr); 2024 PF 1.49 (47 tr); 2025 PF 1.24 (47 tr); 2026 PF 1.39 (41 tr)
ROBUSTNESS:    entry parameters MODERATE; management BROAD_PLATEAU
NULL EVIDENCE: cluster MIXED (p_size 0.0249, p_entries 0.9353, p_strong 0.0249; 200 null worlds)
FORWARD STATUS: NOT STARTED
```

```
STRATEGY ID:   C1cf9dd8f45bc741e   (FINAL FORWARD CANDIDATE)
CLUSTER:       stronger-subset cluster 14 -- MIXED (62 members, 12 entry rules)
INSTRUMENT:    NQ, 1 contract
DIRECTION:     Long and short (one position at a time)

ENTRY:         BUY when the close has risen at least 2.0 x ATR60 x sqrt(15) above the close 15 minutes earlier (first bar this becomes true). SELL SHORT when the close has fallen at least 2.0 x ATR60 x sqrt(15) below the close 15 minutes earlier (first bar this becomes true). Orders are market orders filled at the OPEN of the next one-minute bar.
INITIAL STOP:  Initial stop 1 x ATR(14 fifteen-minute bars) from the entry.
PROFIT MANAGEMENT: Initial stop = 1R, no target; trailing stop 3 ATR below the highest high since entry (above the lowest low for shorts), recomputed at every bar close, active from the start. Always flat at the session flat time (16:00 New York).
TRADING HOURS: entries from 09:30 to 15:30 New York, always flat by 16:00
MAX HOLD:      until the session flat time (16:00 New York) at the latest; never overnight
PARAMETERS:    lookback=15, mode=continuation, window=rth, z=2.0; stop=atr mult=1.0; management=TRAIL_ATR_3_ACT0R
COST ASSUMPTION: baseline $14.00 per round trip ($4 commission + 1 tick slippage each side)
HISTORICAL CONTEXT (selection data, NOT independent evidence): discovery 2010-2020 2527 trades, PF 1.07; 2021-2026(cutoff) 1063 trades, PF 1.37, WR 28.5%, net $177,538, max DD $15,277
               yearly: 2021 PF 1.31 (215 tr); 2022 PF 1.26 (177 tr); 2023 PF 1.41 (169 tr); 2024 PF 1.48 (181 tr); 2025 PF 1.30 (203 tr); 2026 PF 1.54 (118 tr)
ROBUSTNESS:    entry parameters BROAD_PLATEAU; management MODERATE
NULL EVIDENCE: cluster MIXED (p_size 0.3881, p_entries 0.0249, p_strong 0.3881; 200 null worlds)
FORWARD STATUS: NOT STARTED
```
