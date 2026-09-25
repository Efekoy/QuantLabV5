# FINAL COHORT REPORT

```
ELIGIBLE CLUSTERS:            6 (verified: 3 CLEARLY ABOVE NULL + 3 MIXED)
FINAL SELECTED STRATEGIES:    6
CLUSTERS REPRESENTED:         6 of 6
MAX PAIRWISE OOS CORRELATION: 0.497 (cap 0.500); median 0.249
INSTRUMENTS:                  NQ 6 (one uses ES as information)
FAMILIES:                     momentum 4, mean_deviation 1, cross_market 1
DIRECTIONS:                   both 4, long 2
MANAGEMENT TYPES:             rr 3, stop_time 1, trail_r 1, trail_atr 1
FORWARD START:                2026-08-17 session (opens 2026-08-16 18:00 America/New_York)
FORWARD DATA ACCESSED:        NO
```

## Important: historical data is now SELECTION data

These strategies are NOT independently validated by any historical period any more. Their selection used discovery (2010-2020), 2021, 2022, 2023, 2024, 2025, partial 2026, the 200-world null comparison and the cluster analysis. All historical data through the cutoff (ES 2026-08-14 16:59 NY; NQ 2026-08-10 19:59 NY) is therefore selection data for this cohort. **The clean evidence for these strategies starts only with the 2026-08-17 session.**

They are FINAL FORWARD CANDIDATES in a FINAL FROZEN COHORT -- not proven, not guaranteed, not live-ready. The evidence so far is population-level: the survivor population and a few behaviour clusters beat no-edge surrogate markets. The forward period tests whether these representatives stay profitable.

## Cohort

Manifest `FINAL_FORWARD_COHORT.json` -- SHA-256 **`4e27bc928f39c93d504bcf289ac1ab75a7cdfae5df348d2bdf9c8e4ee7a3c113`** (also in FINAL_FORWARD_COHORT_SHA256.txt). Frozen 2026-09-22T17:15:50.502814+00:00.

These are FINAL FORWARD CANDIDATES. They are NOT proven, NOT guaranteed and NOT live-ready. All data through the cutoff was used to select them. Clean evidence starts with the 2026-08-17 session (2026-08-16 18:00 America/New_York).

| # | candidate | cluster | evidence | instrument | family | direction | management | OOS trades | OOS PF | OOS WR | OOS max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `C39d55eaa5412f438` | 0 | CLEARLY ABOVE NULL | NQ | mean_deviation | long | stop_time | 381 | 1.70 | 55.1% | $18,206 |
| 2 | `C175c690afa915a44` | 1 | CLEARLY ABOVE NULL | NQ | momentum | both | trail_r | 1,274 | 1.32 | 50.9% | $28,987 |
| 3 | `C21fa22c47ad5c1cd` | 2 | CLEARLY ABOVE NULL | NQ | momentum | both | rr | 289 | 1.52 | 51.2% | $18,280 |
| 4 | `C7162dcd77274b6f3` | 3 | MIXED | NQ | cross_market | both | rr | 594 | 1.51 | 44.4% | $23,342 |
| 5 | `C3dc5dc6a88e523c7` | 4 | MIXED | NQ | momentum | long | rr | 293 | 1.38 | 57.0% | $15,870 |
| 6 | `C1cf9dd8f45bc741e` | 14 | MIXED | NQ | momentum | both | trail_atr | 1,063 | 1.37 | 28.5% | $15,277 |

## Rule cards

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

## Pairwise daily OOS P&L correlation (2021-01-01 .. cutoff)

| | C39d55eaa | C175c690a | C21fa22c4 | C7162dcd7 | C3dc5dc6a | C1cf9dd8f |
|---|---|---|---|---|---|---|
| C39d55eaa | 1.000 | 0.497 | 0.494 | 0.207 | 0.386 | 0.260 |
| C175c690a | 0.497 | 1.000 | 0.467 | 0.249 | 0.214 | 0.483 |
| C21fa22c4 | 0.494 | 0.467 | 1.000 | 0.243 | 0.156 | 0.350 |
| C7162dcd7 | 0.207 | 0.249 | 0.243 | 1.000 | 0.220 | 0.189 |
| C3dc5dc6a | 0.386 | 0.214 | 0.156 | 0.220 | 1.000 | 0.169 |
| C1cf9dd8f | 0.260 | 0.483 | 0.350 | 0.189 | 0.169 | 1.000 |

## Hashes

```
{
 "selection_rule_sha256": "c74000f922a197c025123915ecba1f556077c6fa704cf903bd999784484b3209",
 "selection_rule_sha256_recorded_before_selection": "c74000f922a197c025123915ecba1f556077c6fa704cf903bd999784484b3209",
 "clustering_preregistration_sha256": "cf2d08497692b4f7bb230c026261b47c1ad95f4845fa5e011d5d8b1a9096a62c",
 "cluster_evidence_preregistration_sha256": "008982cc703992afdc6f3109193fe3abd15ee6422856b38f2b8bf0b28176b57d",
 "official_discovery_freeze_manifest_sha256": "c6da1c8ad6908f9a4ce94d8ed8e4cf5084bc465b94effd750556627be00f1d6b",
 "archive_manifest_sha256": "cfe9dc59ccd12762e46a32a889fbc119bcd69aa9adaf26b1acbe588ef371c5cb",
 "selection_result_sha256": "372e317f615a6bcfd142ec62d14167c742a2a472abff120586a6bae6d2cf4669",
 "reproduction_check_sha256": "32238889a12321dbbde235e1b84ee2a77547dd7c6776b9bbc2c1363eceedbb8c",
 "cluster_summary_strong_sha256": "bf4dec2817714dd09c74d0c32e4e2e9dd80569d51b415c5e90f61b6527ec5549",
 "edge_real_labels_sha256": "24011e05214c7a0cfcac21b860d6c98eea5e31fffc53da4d1f344d578ba71b56",
 "edge_daily_pnl_sha256": "76e4ad5e30e75905068d3e6543950862ac65a3f72fec13514d05ed0ed1fb0e20",
 "costs_yaml_sha256": "c6a9052c49bf55b29fe58a34d4b1da36cf1b6df0e63da08e995c4fcebbed21e9",
 "sessions_yaml_sha256": "f5522947f5bff662c71ad68ee18b8499714bc95da2b19e8a2f008ef3bd14699f",
 "research_yaml_sha256": "6f71b79391b6536e2a6698672fbe6d161e385eb0e68625c69136efe926833750",
 "search_space_yaml_sha256": "a1eb2e4adec54330dbddd3ba93bd2caa37c72a2c17fbdb468f8696178ad65173",
 "management_yaml_sha256": "8f1e0e4347562dac87a525f8fe1265a3a7dc6a68a45ece7b5732065a48553934",
 "behaviour_code_hash": "b5b7fc4b9ed13c88ae911c0c34455718bd1ade4d24af269d4c55bf205afbfccf",
 "behaviour_code_hash_at_official_freeze": "b5b7fc4b9ed13c88ae911c0c34455718bd1ade4d24af269d4c55bf205afbfccf",
 "data_fingerprints": {
  "ES": "4a5dcac73b45f8097164e1242447fb490e6b2d52b4012cbe1ee3890f2d76edb2",
  "NQ": "63b8f16dd1da0a35f2fdfdc9039686ffc8db0ada84333bfc7cd85f8f28d013e7"
 }
}
```

## Yearly history (context only; selection data)

| candidate | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|
| `C39d55eaa5412f438` | PF 2.32, 74 tr | PF 1.52, 76 tr | PF 1.65, 68 tr | PF 1.07, 67 tr | PF 1.69, 61 tr | PF 2.92, 35 tr |
| `C175c690afa915a44` | PF 1.49, 258 tr | PF 1.28, 231 tr | PF 1.03, 218 tr | PF 1.22, 217 tr | PF 1.49, 221 tr | PF 1.41, 129 tr |
| `C21fa22c47ad5c1cd` | PF 1.12, 71 tr | PF 1.57, 45 tr | PF 1.01, 44 tr | PF 2.22, 43 tr | PF 1.26, 58 tr | PF 2.68, 28 tr |
| `C7162dcd77274b6f3` | PF 1.20, 225 tr | PF 1.58, 52 tr | PF 1.32, 111 tr | PF 1.32, 99 tr | PF 2.60, 64 tr | PF 1.96, 43 tr |
| `C3dc5dc6a88e523c7` | PF 1.39, 62 tr | PF 1.48, 47 tr | PF 1.31, 49 tr | PF 1.49, 47 tr | PF 1.24, 47 tr | PF 1.39, 41 tr |
| `C1cf9dd8f45bc741e` | PF 1.31, 215 tr | PF 1.26, 177 tr | PF 1.41, 169 tr | PF 1.48, 181 tr | PF 1.30, 203 tr | PF 1.54, 118 tr |

## Selection audit

See `SELECTION_AUDIT.md`. Reproduction: `selection/REPRODUCTION_CHECK.md` (PASS).

## Forward tracking

Protocol: `forward/FORWARD_PROTOCOL.md` (hashed in the manifest). Runner: `python -m quantlab.cohort.forward --authorized` (refuses without explicit authorisation). Nothing has run.

## Integrity

# FINAL COHORT -- INTEGRITY CHECK (START, 2026-09-22T17:11 UTC)

| check | result | detail |
|---|---|---|
| Archive manifest hash unchanged | PASS | cfe9dc59ccd12762e46a32a889fbc119bcd69aa9adaf26b1acbe588ef371c5cb |
| All 192 archived files match | PASS | 0 |
| results/main identical to the archive | PASS | [] |
| Frozen cohort / stage results unchanged | PASS | [] |
| Official discovery freeze unchanged | PASS | c6da1c8ad6908f9a4ce94d8ed8e4cf5084bc465b94effd750556627be00f1d6b |
| All null worlds unchanged (200) | PASS | [] |
| Null-funnel tree identical to the edge-stage snapshot | PASS | [] |
| CLUSTERING_PREREGISTRATION.md unchanged since hashed | PASS | cf2d08497692b4f7bb230c026261b47c1ad95f4845fa5e011d5d8b1a9096a62c |
| CLUSTER_EVIDENCE_PREREGISTRATION.md unchanged since hashed | PASS | 008982cc703992afdc6f3109193fe3abd15ee6422856b38f2b8bf0b28176b57d |
| Selection rule not modified after the edge-isolation report was built | PASS | 2026-09-22T12:57:11.716391 |
| Selection-rule hash recorded BEFORE selection | PASS | c74000f922a197c025123915ecba1f556077c6fa704cf903bd999784484b3209 |
| Official ledger unchanged | PASS |  |
| No ledger (null, cohort, forward) shows a bar past the cutoff | PASS | [] |
| No cached real-market extract past the cutoff | PASS | 2026-08-14 16:59:00-04:00 |
| Source data files unchanged (no new bars appended) | PASS | {'NQ': '63b8f16dd1da0a35f2fdfdc9039686ffc8db0ada84333bfc7cd85f8f28d013e7', 'ES': '4a5dcac73b45f8097164e1242447fb490e6b2d52b4012cbe1ee3890f2d76edb2'} |
| Tests | PASS | 87 passed, 0 failed |

**ALL CHECKS PASSED**

# FINAL COHORT -- INTEGRITY CHECK (END, 2026-09-22T17:17 UTC)

| check | result | detail |
|---|---|---|
| Archive manifest hash unchanged | PASS | cfe9dc59ccd12762e46a32a889fbc119bcd69aa9adaf26b1acbe588ef371c5cb |
| All 192 archived files match | PASS | 0 |
| results/main identical to the archive | PASS | [] |
| Frozen cohort / stage results unchanged | PASS | [] |
| Official discovery freeze unchanged | PASS | c6da1c8ad6908f9a4ce94d8ed8e4cf5084bc465b94effd750556627be00f1d6b |
| All null worlds unchanged (200) | PASS | [] |
| Null-funnel tree identical to the edge-stage snapshot | PASS | [] |
| CLUSTERING_PREREGISTRATION.md unchanged since hashed | PASS | cf2d08497692b4f7bb230c026261b47c1ad95f4845fa5e011d5d8b1a9096a62c |
| CLUSTER_EVIDENCE_PREREGISTRATION.md unchanged since hashed | PASS | 008982cc703992afdc6f3109193fe3abd15ee6422856b38f2b8bf0b28176b57d |
| Selection rule not modified after the edge-isolation report was built | PASS | 2026-09-22T12:57:11.716391 |
| Selection rule identical to the pre-selection hash | PASS | c74000f922a197c025123915ecba1f556077c6fa704cf903bd999784484b3209 |
| Edge-isolation results unchanged since selection started | PASS | [] |
| Official ledger unchanged | PASS |  |
| No ledger (null, cohort, forward) shows a bar past the cutoff | PASS | [] |
| No cached real-market extract past the cutoff | PASS | 2026-08-14 16:59:00-04:00 |
| Source data files unchanged (no new bars appended) | PASS | {'NQ': '63b8f16dd1da0a35f2fdfdc9039686ffc8db0ada84333bfc7cd85f8f28d013e7', 'ES': '4a5dcac73b45f8097164e1242447fb490e6b2d52b4012cbe1ee3890f2d76edb2'} |
| Tests | PASS | 90 passed, 0 failed |

**ALL CHECKS PASSED**

