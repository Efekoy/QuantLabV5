# V3 DISCOVERY PREREGISTRATION

Written 2026-09-22 18:59:13 (local), before any discovery return was computed. Machine-readable twin: `V3_DISCOVERY_PREREGISTRATION.json` (content_sha256 `7ddb103c6955e65111d34bbb14428c083a3139fdf934d8903fa8f032ed9c0225`).

## Period
sessions 2010-06-07 .. 2018-12-31 (DISCOVERY partition only). NQ traded for every hypothesis except H22 (ES traded, NQ leads); ES/NQ as the other market.

## Normalisation
- **Z(n)**: (c[t]-c[t-n]) / (sigma_tod(n) * sqrt(n)); sigma_tod(n) = mean over the previous 20 sessions of rv(n) at the same session minute; rv(n) = RMS one-minute close change over n bars
- **PE(n)**: |c[t]-c[t-n]| / sum |1-min close changes|; thresholds applied to PE(n)*sqrt(n)
- **D**: mean RTH range of the previous 10 completed sessions
- **ATRh**: ATR(14) of completed 15-minute bars

## Catalog (53 families)

| id | family | rule | ablated conditions | grid |
|---|---|---|---|---|
| H01 | Efficient momentum | Z(n) crosses +/-z; confluence: normalised path efficiency PE(n)*sqrt(n) >= pe. | pe | `{"n": [15, 30, 60], "z": [1.0, 1.5, 2.0], "pe": [null, 1.8, 2.2], "mode": ["continuation"]}` |
| H02 | Momentum acceleration | Recent k-bar impulse Z(k) >= zk; confluence acc: the preceding m-bar move agrees in direction (acc=0) and recent per-minute speed >= acc x prior per-minute speed. | acc | `{"k": [5, 10], "zk": [1.0, 1.5], "m": [20, 30], "acc": [null, 0, 1.5, 2.5], "mode": ["continuation"]}` |
| H03 | Multi-horizon momentum | Directional agreement of Z(5), Z(30), Z(120) (each >= z) for the selected horizons. | h5, h30, h120 | `{"h5": [null, true], "h30": [null, true], "h120": [null, true], "z": [0.5, 1.0], "mode": ["continuation"]}` |
| H04 | HTF trend + short-term impulse | HTF state Z(htf) >= zh (2h or 4h) and/or a k-minute impulse Z(k) >= zi, same direction. | zh, zi | `{"htf": [120, 240], "zh": [null, 0.5, 1.0], "k": [5, 10], "zi": [null, 1.5, 2.0], "mode": ["continuation"]}` |
| H05 | Volatility-shock momentum | Z(n) >= z during a realised-vol shock rv15 / same-time-of-day baseline >= v. | v | `{"n": [15, 30], "z": [1.0, 1.5], "v": [null, 1.5, 2.0, 3.0], "mode": ["continuation"]}` |
| H06 | Compression to expansion | Close breaks the previous N-bar high/low; confluence: the N bars before were compressed (rv_N / time-of-day norm <= cth); optional strength Z(5) >= 1. | cth, strong | `{"N": [30, 60], "cth": [null, 0.6, 0.75], "strong": [null, 1.0], "mode": ["continuation"]}` |
| H07 | Opening-drive continuation | At 09:30+w: RTH move >= m x D; confluence: efficiency since the open >= e. | e | `{"w": [15, 30], "m": [0.15, 0.3], "e": [null, 0.25, 0.4], "mode": ["continuation"]}` |
| H08 | Morning trend continuation | At cutoff (10:30/11:00): return from the open >= m x D; confluences: efficiency >= e, closing location in the range >= cl (in the trend direction). | e, cl | `{"cut": ["10:30", "11:00"], "m": [0.3, 0.5], "e": [null, 0.15], "cl": [null, 0.75], "mode": ["continuation"]}` |
| H09 | Last-hour trend continuation | At 15:00: session return from the open >= m x D; confluences: efficiency, closing location. | e, cl | `{"cut": ["15:00"], "m": [0.4, 0.7], "e": [null, 0.08], "cl": [null, 0.8], "mode": ["continuation"]}` |
| H10 | Impulse + pullback continuation | Impulse Z(L) >= zi, then a controlled pullback of >= retr of the impulse (cancelled beyond 75% or after 60 bars), then resumption: close beyond the previous bar's extreme. retr None = enter at the impulse (parent). | retr | `{"L": [15, 30], "zi": [1.5, 2.0], "retr": [null, 0.25, 0.33, 0.5], "mode": ["continuation"]}` |
| H11 | Failed countertrend move | Trend: Z(120) measured before the counter move >= zt; counter move: 10-minute Z <= -zc; resumption within 30 bars: close above the previous r-bar high. zc None = resumption trigger in trend without a counter move (parent). | zc | `{"zt": [0.75, 1.5], "zc": [null, 1.0, 1.5], "r": [3, 10], "mode": ["continuation"]}` |
| H12 | Breakout + acceptance | Level: previous 120-bar high/low, overnight high/low, previous-day RTH high/low. Acceptance: first close beyond (parent), 2nd / 3rd consecutive close, retest, displacement. | - | `{"level": ["roll120", "on", "pd"], "acc": ["touch", "close2", "close3", "retest", "displace"], "mode": ["continuation"]}` |
| H13 | Rolling-mean overextension | dev(n) = (close - mean of previous n closes)/(sigma_tod(n)*sqrt(n)) >= d; fade. Natural target: the mean. | - | `{"n": [30, 60, 120], "d": [1.25, 1.75, 2.25], "mode": ["reversal"]}` |
| H14 | Deceleration exhaustion | Extended move Z(N) >= z and a new N-bar high, while the last-5-bar per-minute speed <= r x the per-minute speed of the earlier part of the move. r None = no deceleration (parent). | r | `{"N": [30, 60], "z": [1.5, 2.5], "r": [null, 0.5, 0.25], "mode": ["reversal"]}` |
| H15 | Session-extreme rejection | After 10:00, a new RTH session high then, within k bars of the latest new high, a close <= extreme - rj x ATRh and below the high it broke. Fade. | - | `{"k": [5, 15], "rj": [0.25, 0.5, 1.0], "mode": ["reversal"]}` |
| H16 | PDH/PDL failed break | Failed break of the previous day's RTH high/low; fade back into the range. Natural target: prior-range mid. | - | `{"k": [5, 15, 30], "depth": [0.0, 0.25], "mode": ["reversal"]}` |
| H17 | Overnight-extreme failed break | Failed break of the overnight high/low during RTH; fade. Natural target: overnight-range mid. | - | `{"k": [5, 15, 30], "depth": [0.0, 0.25], "mode": ["reversal"]}` |
| H18 | Opening-range failed breakout | Failed break of the w-minute opening range; fade. Natural target: opening-range mid. | - | `{"orw": [15, 30], "k": [5, 15], "depth": [0.0, 0.25], "mode": ["reversal"]}` |
| H19 | Large morning move reversal | RTH high - open >= m x D, then (10:00-13:00) a retracement from the high of >= dr of that move (deterioration). dr None = fade at 11:00 without deterioration (parent). Natural target: RTH open. | dr | `{"m": [0.5, 0.8], "dr": [null, 0.25, 0.4], "mode": ["reversal"]}` |
| H20 | Extreme-move path test | Equally large moves Z(n) >= z split by path efficiency: HIGH (PE >= pe_hi) or LOW (PE <= pe_lo); each tested as continuation AND reversal. | - | `{"n": [30, 60], "z": [2.0, 2.5], "cls": ["high", "low"], "pe_hi": [2.4], "pe_lo": [1.7], "mode": ["continuation", "reversal"]}` |
| H21 | ES leads NQ | The OTHER market's w-minute move >= zE sigma units; confluence lag: this market's move is <= 0.5x the other's (has not yet responded). Trades this market in the other's direction. | lag | `{"w": [2, 5], "zE": [1.5, 2.5], "lag": [null, 0.5], "mode": ["continuation"]}` |
| H22 | NQ leads ES | The OTHER market's w-minute move >= zE sigma units; confluence lag: this market's move is <= 0.5x the other's (has not yet responded). Trades this market in the other's direction. (Traded on ES with NQ as the leader.) | lag | `{"w": [2, 5], "zE": [1.5, 2.5], "lag": [null, 0.5], "mode": ["continuation"]}` |
| H23 | Relative momentum | Z_NQ(n) - Z_ES(n) >= thr (NQ outperforming, vol-adjusted): trade NQ in that direction. | - | `{"n": [15, 30, 60], "thr": [1.0, 1.5], "mode": ["continuation"]}` |
| H24 | Beta-adjusted NQ/ES residual reversion | Residual of NQ's W-minute log return vs beta x ES's (beta from the 390 one-minute returns ending W bars earlier), standardised; |z| >= thr: fade. Natural target: residual = 0 with ES unchanged. | - | `{"W": [15, 30, 60], "thr": [2.5, 3.5], "mode": ["reversal"]}` |
| H25 | Correlation breakdown | 30-minute NQ/ES return correlation <= cth and |30-minute beta residual z| >= rz. Separate hypotheses: continuation (follow NQ's residual) and convergence (fade it). | - | `{"cth": [0.5, 0.65], "rz": [1.0, 2.0], "mode": ["continuation", "reversal"]}` |
| H26 | Mechanical SMT / non-confirmation | One market makes a new extreme (previous N-bar or RTH session high/low) that the other does not. kind nq_only: this market swept, other did not; es_only: the other swept, this did not. Confirmation 'rej': within 10 bars this market closes beyond its previous 3-bar extreme against the sweep. Fade. | confirm | `{"level": ["roll30", "roll60", "session"], "kind": ["nq_only", "es_only"], "confirm": [null, "rej"], "mode": ["reversal"]}` |
| H27 | Cross-market momentum confirmation | NQ Z(n) >= z; confluence: ES Z(n) >= ce in the same direction. | ce | `{"n": [15, 30], "z": [1.0, 1.5], "ce": [null, 0.5, 1.0], "mode": ["continuation"]}` |
| H28 | Cross-market disagreement reversal | NQ 30-minute Z >= z; confluence es: ES 30-minute Z <= 0.5z (not confirming); confluence trig: within 15 bars NQ closes beyond its previous 3-bar extreme against the move. Fade. | es, trig | `{"z": [1.5, 2.0], "es": [null, "nonconf"], "trig": [null, "rej"], "mode": ["reversal"]}` |
| H29 | Relative acceleration | Relative move rel_k = Z_NQ(k) - Z_ES(k) >= thr; confluence acc: rel_k/sqrt(k) >= acc x the relative move over the preceding 20 bars / sqrt(20). Trades NQ absolute continuation. | acc | `{"k": [5, 10], "thr": [1.0, 1.5], "acc": [null, 2.0], "mode": ["continuation"]}` |
| H30 | Path-efficiency continuation | Normalised path efficiency PE(n)*sqrt(n) >= e with at least a modest move Z(n) >= 0.75; continuation. | - | `{"n": [15, 30, 60], "e": [1.5, 1.8], "mode": ["continuation"]}` |
| H31 | Low-efficiency reversal | Large move Z(n) >= z achieved with normalised path efficiency PE(n)*sqrt(n) <= e (noisy path); fade. | - | `{"n": [30, 60], "z": [1.25, 1.75], "e": [1.2, 1.45], "mode": ["reversal"]}` |
| H32 | Speed shock | |k-minute move| >= s x its same-time-of-day mean |k-minute move|; direction = sign of the move; continuation and reversal tested separately. | - | `{"k": [2, 5], "s": [3.0, 5.0], "mode": ["continuation", "reversal"]}` |
| H33 | Acceleration (three windows) | Three consecutive w-minute moves in the same direction with strictly increasing size, total move Z(3w) >= z; continuation. | - | `{"w": [3, 5, 10], "z": [0.75, 1.25], "mode": ["continuation"]}` |
| H34 | Deceleration | Three consecutive w-minute moves in the same direction with strictly decreasing size (still progressing), total Z(3w) >= z; fade. | - | `{"w": [5, 10], "z": [1.0, 1.5], "mode": ["reversal"]}` |
| H35 | Pullback quality | As H10 (30-minute impulse, 33% pullback, resumption) with the pullback classified FAST (depth reached <= 5 bars after the extreme) or SLOW (>= 15 bars). qual None = any (parent). | qual | `{"L": [30], "zi": [1.5, 2.0], "retr": [0.33], "qual": [null, "fast", "slow"], "mode": ["continuation"]}` |
| H36 | Time since session high/low | stale: the RTH high was set >= Tm minutes ago and the close is still in the top 20% of the RTH range (failed to extend). fresh: a new RTH high after >= Tm minutes without one. Each tested as continuation and reversal (mirror for lows). After 10:30. | - | `{"Tm": [60, 120], "kind": ["stale", "fresh"], "mode": ["continuation", "reversal"]}` |
| H37 | Realised-volatility shock | rv15 / same-time-of-day norm >= v (onset); confluence hist: rv15 / rv390 >= 1.5 (also high vs recent history). Direction = sign of the 15-minute move. Continuation and reversal. | hist | `{"v": [2.0, 3.0], "hist": [null, 1.5], "mode": ["continuation", "reversal"]}` |
| H38 | Volatility-of-volatility shock | rv15 now / rv15 of the previous 15 bars >= q (jump) or <= 1/q (collapse); direction = sign of the 15-minute move; continuation and reversal. | - | `{"q": [2.0, 3.0], "kind": ["jump", "collapse"], "mode": ["continuation", "reversal"]}` |
| H39 | Intraday compression breakout | A 5-minute move Z(5) >= z5 (volatility expansion); confluence: the 30 bars before were compressed (rv30 / time-of-day norm, measured at t-1, <= cth). Trade the expansion direction. | cth | `{"cth": [null, 0.6, 0.75], "z5": [1.0, 1.5], "mode": ["continuation"]}` |
| H40 | Daily compression -> intraday expansion | Confluence dc: mean RTH range of the previous 3 sessions <= dc x that of the previous 20. Trigger: first close of the session beyond the 30-minute opening range (or2) or beyond the previous-day RTH high/low (pd). Continuation. | dc | `{"dc": [null, 0.65, 0.8], "trig": ["or30", "pd"], "mode": ["continuation"]}` |
| H41 | Variance-ratio trending regime + momentum | Momentum Z(15) >= z; confluence: variance ratio VR(5) over the last L bars >= vr (persistent). | vr | `{"z": [1.0, 1.5], "vr": [null, 1.2, 1.4], "L": [120, 240], "mode": ["continuation"]}` |
| H42 | Variance-ratio mean-reverting regime + reversion | Overextension dev(30) >= d; confluence: VR(5) over the last L bars <= vr (anti-persistent). Fade; natural target: the mean. | vr | `{"d": [1.0, 1.5], "vr": [null, 0.8, 0.65], "L": [120, 240], "mode": ["reversal"]}` |
| H43 | Positive autocorrelation regime + momentum | Momentum Z(15) >= z; confluence: lag-1 autocorrelation of the last 24 five-minute returns >= a. | a | `{"z": [1.0, 1.5], "a": [null, 0.1, 0.25], "mode": ["continuation"]}` |
| H44 | Negative autocorrelation regime + mean reversion | Overextension dev(30) >= d; confluence: 5-minute return autocorrelation (last 24) <= -a. Fade; natural target: the mean. | a | `{"d": [1.0, 1.5], "a": [null, 0.1, 0.25], "mode": ["reversal"]}` |
| H45 | Early trend-day classification | At the cutoff count five transparent criteria: |return from open| >= 0.2D, RTH range >= 0.45D, efficiency >= 0.2, close location in the direction >= 0.75, 30-minute realised vol >= its time-of-day norm. Trend day if >= k are met; trade the open-to-cutoff direction. | - | `{"cut": ["10:00", "10:30"], "k": [3, 4, 5], "mode": ["continuation"]}` |
| H46 | Early range-day classification + fade | At the cutoff count three criteria: efficiency since open <= 0.1, >= 4 crossings of the RTH open, |return| <= 0.12D. Range day if >= strict are met (None = no classification, parent). Then until 15:00 fade the first bar that trades beyond the cutoff's RTH high (low) and closes back inside. Natural target: mid of the cutoff range. | strict | `{"cut": ["10:30", "11:00"], "strict": [null, 2, 3], "mode": ["reversal"]}` |
| H47 | Large overnight move + same-direction open | Gap (RTH open - previous RTH close) >= g x D; confluence open: at 09:30+w the close is >= 0.05D beyond the RTH open in the gap direction. Continuation, entered at 09:30+w. | open | `{"g": [0.25, 0.5], "w": [5, 15], "open": [null, "same"], "mode": ["continuation"]}` |
| H48 | Large overnight move + opening rejection | Gap >= g x D, then at 09:30+w the close is >= o x D back against the gap from the RTH open. Fade the gap. Natural target: the previous RTH close (gap fill). | - | `{"g": [0.25, 0.5], "w": [15, 30], "o": [0.05, 0.1], "mode": ["reversal"]}` |
| H49 | Morning range -> afternoon continuation / reversal | At 12:00 the morning RTH range >= r x D; kind eff: efficiency since the open >= 0.13; ineff: <= 0.035 (discovery quartiles). Direction = sign of the morning move. Each kind as continuation and reversal. | - | `{"r": [0.7, 0.95], "kind": ["eff", "ineff"], "mode": ["continuation", "reversal"]}` |
| H50 | Trend morning -> lunch consolidation -> PM continuation | A: at 11:30 the close is >= m x D from the RTH open with efficiency >= 0.1. B (cons): the 11:30-13:30 range <= cons x the 09:30-11:30 range. C (trig=brk): after 13:30 the first close beyond the 11:30-13:30 range in the morning direction; trig None: enter at 13:30. | cons, trig | `{"m": [0.4, 0.6], "cons": [null, 0.35, 0.5], "trig": [null, "brk"], "mode": ["continuation"]}` |
| X1 | Turn-of-month long | Executor hypothesis X1: month-start institutional inflows. On the first N sessions of a calendar month, buy at 09:31 (signal at the 09:30 bar's close). Long only. | - | `{"N": [1, 3], "mode": ["continuation"]}` |
| X2 | First half-hour predicts last half-hour | Executor hypothesis X2 (intraday time-series momentum; late-day hedging/rebalancing flow): the return to 10:00 (from the previous RTH close, base=pcl, or from the RTH open, base=open) >= thr x D sets the direction; enter at 15:30, exit by 16:00. thr 0 = sign only. | - | `{"base": ["pcl", "open"], "thr": [0.0, 0.25], "mode": ["continuation"]}` |
| X3 | Correlation-regime momentum | Executor hypothesis X3: momentum Z(30) >= z is market-wide (and should persist) when NQ/ES one-minute correlation over the last 390 bars is high (>= 0.9), idiosyncratic when low (<= 0.75). | reg | `{"z": [1.5, 2.0], "reg": [null, "high", "low"], "mode": ["continuation"]}` |

## Executor-added hypotheses (recorded before any discovery result)

### X1
- hypothesis: Month-start institutional inflows (pension / payroll contributions) lift equity-index futures during the first sessions of a calendar month.
- rule: On the first N RTH sessions of a calendar month (sessions counted by session end date), buy at 09:31 (signal = close of the 09:30 bar); long only; exits per the management library.
- mechanism: calendar-driven flow; not a price-pattern; independent of every H01-H50 signal
- parameters: `{"N": [1, 3]}`

### X2
- hypothesis: Intraday time-series momentum: the return to 10:00 predicts the last half hour (late-day hedging / rebalancing flows that trade with the day's direction).
- rule: At 15:30 enter in the direction of the 10:00 close relative to the previous RTH close (base=pcl) or the RTH open (base=open) when |return| > thr x D; flat by 16:00.
- mechanism: documented intraday momentum (first half-hour -> last half-hour); differs from H09, which classifies the whole session at 15:00
- parameters: `{"base": ["pcl", "open"], "thr": [0.0, 0.25]}`

### X3
- hypothesis: Momentum persists when the move is market-wide (high NQ/ES correlation) and fades when it is idiosyncratic (low correlation).
- rule: 30-minute momentum Z(30) >= z, optionally only when the 390-bar NQ/ES one-minute return correlation is >= 0.9 (high) or <= 0.75 (low).
- mechanism: breadth of participation: index-wide flow vs. sector rotation
- parameters: `{"z": [1.5, 2.0], "reg": [null, "high", "low"]}`

## Management
- **stageA_continuation**: ATR1 x {1R,1.5R,2R,3R,4R, no target->EOD, 60-min time exit}; ATR1.5 and STRUCT x {1R,2R,EOD}
- **stageA_reversal**: ATR1 x {0.5R,0.75R,1R,1.5R,2R,3R,EOD,60-min, NATURAL if defined}; ATR1.5 and STRUCT x {0.75R,1.5R,NATURAL or EOD}
- **stageA_lead_lag_extra**: ATR1 x time exits {2,5,10} minutes (H21/H22)
- **stageB**: ATR1 only: BE {0.5,1,1.5}R x {2R | none} (continuation) or x {1.5R | 3R} (reversal); ATR trails {1.5,2,3}; confirmed-swing trail; partials 50%@1R+2R, 50%@1R+3R, 50%@1R+2ATR trail, 25%@1R+runner, (reversal) 50%@0.5R+1.5R; 50%@1R->BE->3R; BE@1R+2ATR trail
- **stageB_qualification**: an entry qualifies if ANY Stage-A management variant has BASELINE net > 0
- **controls**: Stage-A single-exit variants (no BE / no partial / no trail) are the controls of Stage B

## Search-space size
`{"signal_configs": 511, "entries": 1529, "stageA_specs": 20693, "stageB_max_specs": 24464, "max_total_specs": 45157, "families": 53}`

## Discovery labels
- **PRIMARY**: trades >= 30, BASELINE net > 0 and per-trade t-statistic >= 1.0 (mean net trade at least one standard error above zero). The only candidates ELIGIBLE for the final cohort.
- **WEAK_POSITIVE**: trades >= 30, BASELINE net > 0, t < 1.0. Frozen and tracked (diagnostic).
- **LOW_SAMPLE**: 0 < trades < 30 and BASELINE net > 0. Frozen and tracked (diagnostic).
- **MODERATE_ONLY**: MODERATE net > 0 but BASELINE net <= 0 (cost-sensitive). Frozen and tracked (diagnostic).
- **GROSS_ONLY**: GROSS > 0 but MODERATE net <= 0. Recorded in results only.
- **flag STRESS_NEGATIVE**: BASELINE net > 0 but STRESS net <= 0.
- **flag REGIME_CONDITIONAL**: PRIMARY with >= 1 confluence condition present while its parent without that condition (all else equal) has BASELINE net <= 0.

**Discovery freeze candidate set:** PRIMARY + WEAK_POSITIVE + LOW_SAMPLE + MODERATE_ONLY (every such spec is run unchanged in confirmation; only PRIMARY is eligible for the final cohort)

## Robustness
- **parameter**: share of grid neighbours (same family, instrument, direction, management and every non-numeric / None-status parameter; one step apart in exactly one numeric parameter) with BASELINE net > 0
- **management**: share of the entry's Stage-A management variants with BASELINE net > 0

## Ablation
for every spec with a confluence condition present, compare with the identical spec where that one condition is None: trades removed (n, %), change in PF, WR, avg net trade, expectancy (R), max DD, cost sensitivity (stress/baseline), parameter robustness, and sub-period repetition (sign of the avg-trade improvement in 2010-12, 2013-15, 2016-18)

## Sub-periods
{'P1': [2010, 2012], 'P2': [2013, 2015], 'P3': [2016, 2018]}

## Hashes
```
{
 "search_space_yaml": "a4834eb6ced4702927a0b86f903747e5644ee28a22f354625a9824ff2db590d2",
 "search_space_json": "421e68a99f26b5795fa9f6bcf49666c10b6a4d3de8fc9168ddc79fba7cd6c2de",
 "feature_calibration": "5fd14831edc5eeb2b366e5b4ab99e9318722fe4ee792574b1f4b7cee6a61f683",
 "behaviour_code_sha256": "a05d4436e1e81e4e1905ab84aa24570a006bf461abf852b2e12e5c73084927c7",
 "strategy_registry_sha256": "950a256470df4cdfdfeb98625be522f43d4a4b7ca948beae9fb7077a9f60e4c9",
 "config": {
  "research": "f7392ef3e19a82fe071e16ec9ac9552e81270b4bc4b02f4a5618534a0a70caa8",
  "costs": "a27ed5df0c04611fce85e81a2380963f9d63d955a88081a4c12b6e543c98624a",
  "sessions": "fffc52681f6b3e5a2222f073aaaaa73a0ccfecdcc555c7ba7a2907b5447c5460",
  "partitions": "1161208105e16d4d782b2014c5282a9f3b64a5969f867756722323b9f42831a9",
  "search_space": "49243942ec9edf81a346603bf7779e51c0cc0eaf6ba1394f19d65e5dc8478b2d",
  "management": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"
 },
 "research_code": {
  "_calib_features.py": "de8253996f8f31d658d001ea4ed1f5cffe605fa9d5a3a1b64805be21c3c55a18",
  "count_space.py": "78543836947fa47f3a5612ff60c9e1db17b879b202ef10e8a403b275eb76a369",
  "s0_verify_engine.py": "0dea96d61f6e1b9f8980318550e88012f983259e3a1f172cd76d3437a97c20db",
  "s1_discovery.py": "03ed3f41a51e8bfafd3474ef41dd6edc7e7eac95fd6f4c019bf82018ad1a68f6",
  "s1a_prereg_discovery.py": "9c374979a76770a3f2ac9ea7df4c8e9b94fe38dd9adde77ae226844b049c0f5a",
  "s2_discovery_analysis.py": "1c0b2738c29a369b387d551fbf08cfc11ce54ad6008eed9e47ac33a77c1c10a0",
  "v3lib.py": "27fa05b74df51f1cdb00ead6758656ccc449328237a6dfc57fa22b148792c086"
 }
}
```
