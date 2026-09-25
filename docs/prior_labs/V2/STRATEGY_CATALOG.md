# QuantLabV2 — Catalog of Everything Already Tested

Purpose: a complete list of the strategy ideas already tested in QuantLabV2, with results, so a
new round of research can propose ideas that are genuinely NEW rather than re-testing these.

---

## 0. Instructions for the AI reading this

You are helping design the NEXT research round. Please:

1. **Do not re-propose anything in sections 3–4** unless you change it in a way that makes it a
   different behaviour. Changing a parameter value, a lookback or an exit is NOT a new idea.
2. Propose ideas as **behaviours with a reason** ("why should this make money, who is on the other
   side?"), not as parameter grids.
3. For each idea give: an exact rule definition with no look-ahead, the market mechanism behind it,
   which tested family it is closest to and why it is different, and what data it needs.
4. Use the results (section 5) and the gaps (section 6): build on the families that beat the null
   and avoid variations of the families that were null-like.
5. Respect the constraints in section 1 unless you explicitly propose extending them. Say so if
   you do, for example "needs volume data".

---

## 1. Test setup and constraints

- **Instruments:** E-mini Nasdaq-100 (NQ) and E-mini S&P 500 (ES) futures, continuous front contract.
- **Data:** 1-minute OHLC bars only. **No volume, no order book, no tick data**, no options, no news,
  no economic calendar, no other markets.
- **History:** 2010-06-07 to 2026-08-14. Discovery (the search) used 2010–2020; 2021–2026 were tested
  one year at a time.
- **Intraday only:** entries only during a family's window; always flat by 16:00 New York; no position
  held overnight or across a contract roll. One position at a time per strategy.
- **Execution:** the signal is known at the bar close and fills at the NEXT bar's open (market order).
  A target fills only if price trades 1 tick beyond it. Stops fill at the stop price, or at the open if
  price gaps through. When a bar touches both the stop and the target, the stop is assumed to fill first.
- **Costs:** BASELINE decided pass/fail. NQ $14 per round trip ($4 commission + 1 tick slippage each
  side). ES $29. Stress test: NQ $26, ES $56.
- **Trading windows:** `rth` 09:30–15:30, `rth_am`, `rth_pm`, `globex` 18:00–15:30 (New York time).
- **Directions:** every entry was tested three ways: long only, short only, and `both` (long and short).
- **Modes:** almost every family was tested in both `continuation` (trade WITH the signal) and
  `reversal` (FADE the signal) mode. Both sides of each idea have therefore been covered.
- **Volatility unit:** many thresholds are "z" moves measured as `z × ATR60 × sqrt(n)`, where ATR60 is
  the 60-bar 1-minute ATR and n is the lookback in minutes.

**Scale:** 20 entry families → 1,938 signal configurations → 5,732 entry specifications per
instrument. Crossed with the exit/management library → **2,659,077 strategy specifications** tested.

---

## 2. How results are labelled in this catalog

**Frozen:** profitable (after BASELINE costs) in discovery, 2010–2020.

**Final survivors:** also profitable in EVERY year from 2021 to 2025 and in 2026 up to August 14.

**Null verdict:** each family's survivor count compared with 200 simulated markets that have
realistic volatility but no directional edge. The p-value is family-wise across all families.

| Verdict | Meaning |
|---|---|
| **EDGE** | Clearly above the simulated markets (p ≤ 0.04). |
| **WEAK** | Above the null median, but not significant after the family-wise correction. |
| **NULL** | Indistinguishable from chance. |

---

## 3. Entry families tested (20)

Each family below gives its definition, the parameter grid tested, and its result.
Results are shown as: frozen → final survivors, then the null-world median, then the verdict.

### A. Time of day
- **Definition:** enter at a fixed New York clock time every session and hold for a fixed time.
  No indicator.
- **Grid:** entry time every 30 minutes from 19:00 to 15:00 (41 times); `globex` window; long or
  short; time exits only.
- **Result:** 3,439 → 114; null median 14; **NULL** (p = 0.49).

### B. N-bar momentum
- **Definition:** the close moved at least `z × ATR60 × sqrt(n)` over the last n minutes (first bar
  this becomes true).
- **Grid:** lookback 5/10/15/30/60/120/240; z 0.5/1/1.5/2/3; continuation/reversal; `rth`, `rth_am`,
  `rth_pm`; exits: time, opposite signal, plus the full management library.
- **Result:** 63,530 → 3,860; null median 356; **EDGE** (p = 0.015). 4 of the 6 final forward
  strategies come from here.

### C. Consecutive bars
- **Definition:** a bar completes a run of exactly N higher (or lower) closes.
- **Grid:** N 2/3/4/5/6/8; continuation/reversal; `rth`.
- **Result:** 1,583 → 91; null median 2; **WEAK** (p = 0.10).

### D. Displacement
- **Definition:** a single 1-minute bar whose body or range is at least k × the previous ATR60,
  optionally also requiring a strong close.
- **Grid:** body/range; k 2/3/4/5; close strength none/strong; continuation/reversal.
- **Result:** 3,717 → 93; null median 7; **NULL** (p = 0.60).

### E. Rolling breakout
- **Definition:** a bar closes (or trades) beyond the high/low of the previous N bars (first such bar).
- **Grid:** N 15/30/60/120/240; trigger close/touch; continuation/reversal; `rth`, `rth_am`, `rth_pm`.
- **Result:** 3,246 → 59; null median 2; **NULL** (p = 0.79).

### F. Failed breakout
- **Definition:** a bar trades beyond the previous N-bar extreme but closes back inside the range.
- **Grid:** N 15/30/60/120/240; reversal/continuation.
- **Result:** 355 → 24; null median 0; **NULL/WEAK** (p = 0.35). It had the best average number of
  years survived, but the sample is tiny.

### G. Mean deviation
- **Definition:** the close is at least `z × ATR60 × sqrt(n)` away from the SMA of the previous n
  closes, or from the midpoint of the previous n-bar range.
- **Grid:** anchor sma/midpoint; n 15/30/60/120/240; z 0.5/1/1.5/2/3; reversal/continuation; exits
  time/opposite plus the library.
- **Result:** 35,099 → 2,583; null median 129; **EDGE** (p = 0.005).
- **Note:** the surviving versions are mostly CONTINUATION, meaning "stretched above the mean → buy".
  That is really momentum, not mean reversion.

### H. Range position
- **Definition:** the close moves into the top or bottom `edge` fraction of the previous N-bar range.
- **Grid:** N 15/30/60/120/240; edge 0.1/0.2/0.25/0.33.
- **Result:** 1,063 → 109; null median 0; **WEAK** (p = 0.09).

### I. Session-open distance
- **Definition:** the close is at least `z × ATR60 × sqrt(minutes elapsed)` away from the Globex open
  (18:00) or the RTH open (09:30).
- **Grid:** anchor globex/rth open; z 0.5/1/1.5/2/3.
- **Result:** 5,454 → 306; null median 15; **EDGE** (p = 0.04).

### J. Prior-session levels
- **Definition:** the close crosses (`break`), or probes and is rejected at (`touch`), the previous
  session's RTH high, low, close or midpoint.
- **Grid:** 4 levels × break/touch × first touch only (yes/no).
- **Result:** 5,069 → 162; null median 20; **NULL** (p = 0.48).

### K. Overnight range
- **Definition:** a break of, or rejection at, the overnight (18:00–09:30) high, low or midpoint
  during RTH.
- **Grid:** 3 levels × break/touch.
- **Result:** 1,996 → 22; null median 5; **NULL** (p = 0.93).

### L. Opening range
- **Definition:** the first close beyond the high/low of the first k minutes of RTH.
- **Grid:** k 5/15/30/60.
- **Result:** 2,133 → 75; null median 3; **WEAK** (p = 0.08).

### M. RTH gap
- **Definition:** the 09:30 open vs the prior RTH close, measured against the average RTH range of the
  last 10 sessions. The decision is made at 09:31.
- **Grid:** threshold 0.1/0.2/0.3/0.5; continuation/reversal; gap-fill targets (full/half).
- **Result:** 4,092 → 13; null median 10; **NULL** (p = 1.0).

### N. Candle patterns
- **Definition:** a candle pattern on a 1-, 5- or 15-minute bar:
  - `body_X`: body at least X of the range
  - `close_X`: close location at least X
  - `wick_X`: rejection wick at least X
  - `outside`: outside bar
  - `inside_break`: break of an inside bar
- **Grid:** timeframe 1/5/15; the 8 patterns (body 0.6/0.8, close 0.8/0.9, wick 0.5/0.66, outside,
  inside break).
- **Result:** 2,205 → 126; null median 3; **WEAK** (p = 0.055).

### O. Compression / expansion
- **Definition:** ratio = ATR(n) / ATR(10n).
  - `compression_breakout`: the ratio was below 0.7 (or 0.5) and the bar closes beyond the n-bar
    high/low.
  - `expansion_move`: the ratio is above 1.5 (or 2.0) and the n-bar move gives the direction.
- **Grid:** n 10/20/30/60; state; strength 1/2.
- **Result:** 5,478 → 155; null median 8; **WEAK** (p = 0.11).

### P. Volatility regime (context filter)
- **Definition:** a basic momentum or mean-deviation setup, taken only in a low, mid or high
  volatility regime. Regime = RTH range of the last 5 sessions / the last 60 (cut-offs 0.8 and 1.25).
- **Grid:** setup mom15_z1, mom60_z1, dev60_z1.5 or dev120_z2; regime low/mid/high.
- **Result:** 7,763 → 253; null median 24; **NULL/WEAK** (p = 0.15).

### Q. Price structure (swings)
- **Definition:** a swing high/low is confirmed after `swing` bars on each side. Events:
  - `swing_break`: the close crosses the latest swing high/low
  - `pullback`: the first retest of a broken swing level that holds
  - `trend_state`: two rising (or falling) swing highs AND lows
- **Grid:** timeframe 1/5; swing 2/3/5/10; 3 events.
- **Result:** 2,053 → 46; null median 3; **NULL** (p = 0.64).

### R. Multi-timeframe
- **Definition:** the direction of the 15/30/60-minute timeframe (completed bars only) plus a 1-minute
  momentum trigger, either WITH the higher-timeframe trend or a PULLBACK against it.
- **Grid:** higher timeframe 15/30/60; its lookback 1/3; with_trend/pullback; trigger lookback 5/15;
  z 1/2.
- **Result:** 14,625 → 529; null median 63; **NULL/WEAK** (p = 0.19).

### S. Fair-value gap (FVG)
- **Definition:** a 3-candle imbalance, where low[j] > high[j-2] (bullish) or the mirror (bearish),
  on 1-, 5- or 15-minute bars. Events:
  - `create`: the gap forms
  - `touch`: price trades back into the zone
  - `reject`: touches the zone and closes back out of it
  - `invert`: closes through the zone
- **Grid:** timeframe 1/5/15; minimum gap size 0/0.25/0.5 × ATR; 4 events.
- **Result:** 17,106 → 1,235; null median 61; **EDGE** on count (p = 0.01), but its members are
  low-quality: a large, low-PF, high-frequency, long-biased cluster.

### T. NQ/ES cross-market
- **Definition:** four signals from the two markets together:
  - `relative`: this market's z-move minus the other market's crosses ±z
  - `lead`: the OTHER market's z-move crosses ±z
  - `nonconfirm`: the other market breaks its n-bar high/low but this market doesn't
  - `confirm`: both markets break on the same bar
- **Grid:** 4 kinds; lookback 5/15/30/60; z 0.5/1/1.5.
- **Result:** 10,469 → 1,607; null median 46; **EDGE** (p = 0.005).

---

## 4. Exit and trade-management library tested

Every entry was crossed with these exits. Management turned out to matter little: the same entry
with or without breakeven or trailing passed 2021 at nearly the same rate, and partials and runners
did slightly worse.

- **Initial stops:**
  - ATR × 0.25/0.5/0.75/1/1.5/2/3 (ATR14 of 15-minute bars)
  - fixed points: NQ 5/10/20/40, ES 2/4/8/16
  - beyond the signal bar
  - beyond the last 5-minute swing
  - rolling 15/60-bar extreme
  - a fraction of the range (0.5/1.0)
  - "structural"
- **Fixed targets:** 0.25, 0.33, 0.5, 0.75, 1, 1.25, 1.5, 2, 2.5, 3, 4 R.
- **Breakeven:** move the stop to entry at +0.25/0.5/0.75/1/1.5/2 R, combined with a target of
  1/2/3 R or none.
- **Trailing stops:**
  - ATR distance 0.5–3, activating at 0–2 R
  - close-based ATR trail
  - N-bar extreme trail, N = 2/3/5/8/10/15/20
  - R-distance trail, 0.5–2 R
  - R-step trail, steps of 0.5/1 R
- **Partial exits:** 11 templates, for example 50% at 1R and 50% at 2R; 33/33/34 at 0.5/1/2 R;
  75% at 0.5R and 25% at 2R; partials followed by breakeven or an ATR trail.
- **Runners:** 50% at 1R, then the rest runs to 2/3/4/5R, 120 minutes, the opposite signal, a 2-ATR
  trail, a 10-bar trail or the session close.
- **Time exits:** after 5/15/30/60/120 minutes or at the end of the day. Stop + time exits at
  60/120 minutes or end of day.
- **Other exits:** opposite signal (maximum hold 240 minutes); gap-fill targets (full/half).

---

## 5. What we learned (use this to aim the new ideas)

1. **The ideas that beat the null all react to a volatility-scaled price move on the SAME day:**
   momentum, mean deviation used as continuation, distance from the session open, and NQ/ES
   cross-market signals. These are the only families with clear evidence.
2. **Fixed price levels and chart patterns did not beat the null:**
   - gaps
   - overnight range
   - prior-session levels
   - rolling breakouts
   - swing structure
   - displacement bars
   - time of day
   - multi-timeframe filters
   - volatility-regime filters
3. **Cross-market information (NQ vs ES) was among the strongest families.** Relative strength and
   lead–lag between related markets look promising.
4. **Higher-frequency rules (250+ trades a year) showed the most evidence**, but their margins are
   thin (median PF about 1.09) and very sensitive to costs and slippage.
5. **The best-looking backtests failed most often.** Discovery PF ≥ 3 or win rate ≥ 80% survived at
   chance rates. Modest, frequent, robust rules did better.
6. **The edge weakened in 2025–2026:** survival rates in those years fell within the null range.
   Ideas that adapt to regime, or explain WHY the edge exists, are more valuable.
7. **The selected forward strategies** were 4 momentum, 1 mean deviation (continuation, long) and 1
   cross-market, all on NQ, all entering 09:30–15:30 and flat by 16:00.

---

## 6. Gaps — ideas NOT yet tested

A starting list, not a limit. Items marked *(new data)* need data beyond 1-minute OHLC for NQ/ES.

- **Holding periods:** overnight and multi-day holds; close-to-open and open-to-close effects;
  weekend holds.
- **Calendar effects:**
  - day of week, turn of month, month-end or quarter-end rebalancing
  - option expiration (OPEX) week, triple witching
  - holidays and days before/after holidays
  - FOMC, CPI or NFP days *(needs an event calendar)*
- **Intraday seasonality:** conditioned on context rather than a fixed clock time, for example the
  last-hour drift after a trend day, or lunch-hour reversal only after a large morning move.
- **Day types:** trend day vs range day classification early in the session, then trading the
  expected continuation.
- **Cross-market extensions:**
  - NQ/ES spread mean reversion (pairs)
  - lead–lag with bonds (ZN), the dollar (DX), VIX, RTY or YM *(new data)*
  - correlation-breakdown signals
- **Volatility as the signal (not as a filter):**
  - realized-volatility shocks
  - volatility-of-volatility
  - range expansion after compression, measured on daily bars
  - variance-ratio (trending vs mean-reverting) switches
- **Path shape:**
  - speed or acceleration of a move
  - efficiency ratio (net move / total path)
  - drawdown from the intraday high
  - time since the session high/low
- **Statistical and ML approaches:**
  - regression or classifier on simple features (with a strict walk-forward)
  - regime-switching models
  - Hurst / autocorrelation-regime switching
- **Order-flow and volume** *(needs volume or tick data):* VWAP deviation, volume spikes, delta,
  absorption, liquidity at levels.
- **Different execution:** limit-order entries (pullback fills) instead of market orders;
  scaling in; volatility-scaled position sizing.
- **Portfolio level:** combining uncorrelated rules; risk parity across the survivors; time-series
  momentum on daily bars.
- **Other markets:** RTY, YM, CL, GC, ZN, 6E, European indexes — both to replicate the momentum and
  cross-market findings and to find new ones *(new data)*.

---

## 7. Paste-ready prompt

> I'm attaching a catalog of ~2.66M intraday strategy specifications (20 entry families × a large
> exit library) that I already tested on 1-minute NQ and ES futures, with the results of each family
> against a no-edge null. Propose 15–25 NEW strategy ideas to test next. Do not repeat or lightly
> re-parameterize anything in the catalog. For each idea give:
>
> 1. a name and a one-line hypothesis
> 2. the market mechanism (why it should work and who is on the other side)
> 3. an exact, look-ahead-free rule definition
> 4. the closest existing family and why this is different
> 5. the data required
> 6. a small parameter grid (at most 3 parameters, a few values each)
> 7. how it could fail
>
> Prioritize ideas that build on what beat the null (volatility-scaled same-day momentum,
> continuation, cross-market) or that fill the gaps in section 6. Mark which ideas need data beyond
> 1-minute OHLC.
