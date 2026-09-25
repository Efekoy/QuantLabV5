# V4 DISCOVERY data audit (NQ, ES; sessions 2010-06-08 .. 2018-12-31)

Scope: DISCOVERY only, read through `load_view` (every read is in the ledger). No later partition
was opened. Machine output: `results/discovery/S03_DISCOVERY_DATA_AUDIT.json`
(and `S01_DISCOVERY_DATA_AUDIT.json`). Script: `research/s03_discovery_data_audit.py`.

## Integrity

| Check | NQ | ES |
|---|---|---|
| rows / sessions | 2,776,632 / 2198 | 2,945,493 / 2198 |
| duplicate, out-of-order, non-minute-aligned timestamps | 0 / 0 / 0 | 0 / 0 / 0 |
| bars inside the 17:00-18:00 ET break | 0 | 0 |
| high < max(open, close); low > min(open, close); non-positive; off 0.25 tick grid | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| zero-range bars (h = l) | 363,764 (13%) | 287,472 (10%) |
| rtype / publisher_id | {33} / {1} | {33} / {1} |
| source duplicate-timestamp flags | 0 | 0 |
| rolls (symbol changes) | 35, all at session start | 35, all at session start |
| instrument_id changes = symbol changes = `roll_boundary` | yes | yes |
| session rule vs source `roll_session` | 0 mismatches | 0 mismatches |

## Coverage and missing bars

* A Globex session has at most 1380 one-minute bars (18:00-16:59). The median NQ session has
  1278.5 bars, the ES median is 1356.
* RTH (09:30-15:59): 2124 NQ and 2132 ES sessions have all 390 bars. 66 sessions have < 300
  RTH bars (half-days and holidays), and 5 sessions have no RTH bars at all.
* Missing RTH minutes on normal sessions: NQ 177, ES 164 over 8.5 years (negligible).
* Overnight coverage is lower for NQ, especially 2010-2012. The median overnight minute is present
  in 90% of NQ sessions and 99% of ES sessions. **A missing minute is an absent row.** There are
  no zero-volume rows, so a minute with no trades simply has no bar. Nothing is filled.
* Minute 16:15-16:29 ET has < 50% coverage, which is the pre-2021 CME daily halt.

## DST

The 09:30 ET bar sits at 13:30 UTC in 1451 sessions (summer) and 14:30 UTC in 742 (winter),
and never at any other hour. The session, RTH and window arithmetic is correct across all DST
transitions (see also tests/test_sessions_dst.py).

## NQ/ES synchronisation

* Both instruments have the same 2198 sessions. No session is NQ-only or ES-only.
* RTH: 99.996% of NQ minutes have a same-minute ES bar, and 99.98% of ES minutes have an NQ bar.
* Overall: 99.45% of NQ minutes have ES. Only 93.75% of ES minutes have NQ, because ES trades
  more overnight minutes.
* The roll sessions are **not identical**. Each market's roll follows its own previous-session
  volume, and two quarters (2018-03, 2018-06) differ by one session. Cross-market features
  therefore never assume a common roll.

## What the volume represents

`volume` is the traded volume of the **single front contract** that was selected for that session.
It is **not** aggregated across contract months. The evidence:

* In the session immediately **before** each roll, daily volume collapses to **0.40× (NQ) and
  0.38× (ES)** of the pre-roll median, then returns to ~0.9-1.1× on the roll session. Liquidity
  has already migrated to the next contract, which the file does not include that day. The
  sessions at -2 and +1..+5 days are at ~0.9-1.1×.
* The roll rule itself (hold last session's highest-volume outright) implies this.

## Volume behaviour (DISCOVERY)

* Median 1-minute volume: NQ 394 in RTH and 20 overnight; ES 2340 in RTH and 118 overnight.
* The intraday seasonality is strong and U-shaped. Relative to the RTH median minute: the 09:30
  bar is 6.8× (NQ) and 5.5× (ES), 12:00 is ~0.94-1.04×, the 15:59 bar is 8.0× (NQ) and 14.9× (ES),
  and overnight minutes are 0.24-0.39×. The RTH share of daily volume is ~0.80-0.86 (NQ)
  and 0.77-0.80 (ES).
* The year-to-year scale moves a lot. Median daily NQ volume was 210k-290k per day in 2010-2017
  and 403k in 2018. ES was 1.2M-2.1M per day with a downward drift. **Raw volume is not
  comparable across years or times of day, so all V4 volume features are causally normalised.**
* Extreme minutes (> 20× the median for the same session-minute): NQ 11,402 and ES 9,450
  (≈0.4%). Above 50×: 1,392 and 1,409. These are kept. They cluster at macro-release times
  and the open and close, and they are real prints. Features use ratios and ranks, so no winsorising is applied.

## Cleaning pipeline v1 (frozen with the preregistration)

`quantlab4/data/cleaning.py` (`clean_v1_2026-09-23`), tested in `tests/test_cleaning.py`:

1. No bar is removed and no price is changed, because no invalid bar exists.
2. Missing minutes are left absent, with no forward fill. Cross-market alignment uses the
   same minute only.
3. A **causal roll-window flag** is set on every bar of a session whose held contract is the
   expiring quarterly contract, from the 8th of the expiry month onwards. It covers **100% of the
   degraded pre-roll sessions** in DISCOVERY for both markets and flags 5.4% of sessions.
   Volume-derived features are masked (NaN) inside the window, and time-of-day volume
   baselines exclude those sessions.
4. Prices are unadjusted. Positions never cross a roll, and returns across a roll are NaN.

The same frozen function is applied unchanged to CONFIRMATION, HOLDOUT and 2026 when those
stages open.
