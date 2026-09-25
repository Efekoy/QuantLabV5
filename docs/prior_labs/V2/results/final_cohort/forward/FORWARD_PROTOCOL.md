# FORWARD PROTOCOL -- FINAL FROZEN COHORT (fixed at freeze; hashed in the cohort manifest)

## Start
- FORWARD_START_SESSION = 2026-08-17; FORWARD_START_TIMESTAMP = 2026-08-16 18:00 America/New_York.
- Derived without reading any new bar: the official ledger shows the last bar read for ES at
  2026-08-14 16:59 NY (session 2026-08-14) and for NQ at 2026-08-10 19:59 NY (the first two hours of
  session 2026-08-11; NQ sessions 2026-08-11..14 are absent from the current file and were never read).
  The next session after 2026-08-14 (Friday) is Monday 2026-08-17, which opens Sunday 2026-08-16 18:00 NY
  (not a US market holiday). It is the first session untouched for BOTH instruments.
- All six frozen strategies trade NQ (one uses ES as information) and enter only 09:30-15:30 / 09:30-12:00
  NY, so the first possible forward entry is 2026-08-17 09:30 NY. If a future NQ file does contain the
  never-read NQ sessions 2026-08-11..14, they are NOT forward data (they precede the forward start) and
  are not used.

## Immutable
Frozen specifications (`FINAL_FORWARD_COHORT_SPECS.parquet`, hashes in the manifest), execution engine,
costs and sessions never change. No parameter, stop, target, breakeven, trailing, partial, session or cost
change; no replacement after losses; no dropping; no additions from other historical survivors.

## Warm-up policy
- Each forward evaluation loads bars from 30 calendar days BEFORE the forward start (the official
  warm-up length) through the newest available bar. Bars before the forward start are used only to
  initialise indicator state.
- A trade counts as forward evidence only if BOTH its signal bar (the bar before the entry bar) AND
  its entry bar belong to a session >= 2026-08-17 and start at or after
  2026-08-16 18:00 America/New_York. No position opened before the forward start can exist, because every
  strategy is flat by 16:00 each session.
- Every forward data load is recorded in `forward/FORWARD_DATA_ACCESS_LEDGER.jsonl` (and the guarded
  loader's own ledger).

## Tracking
- All frozen strategies stay in every report for the whole forward period, winners and losers.
- Statuses are descriptive (ACTIVE, FAILED_FORWARD, ...); they never remove a strategy from the cohort
  statistics.
- There are NO kill rules (no "stop after N losses", no "drop when PF < 1"). The forward period is
  evidence collection.

## Metrics (per strategy and cohort)
- Trades, WR, PF, gross P&L, BASELINE net P&L (official), MODERATE and STRESS net P&L, average trade,
  average winner / loser, max DD, trade frequency, long / short P&L, monthly results, cumulative
  equity curve.
- Cohort: equal-weight (one contract each) combined equity and per-strategy table; median strategy PF;
  number of strategies with net > 0. Summed P&L is reported as the equal-weight cohort, one contract
  each -- never extrapolated.

## Evaluation horizon
- Interim reports are descriptive only.
- The first evaluation report is due at the later of (a) six calendar months of forward sessions
  (through the session of 2027-02-16) and (b) the date every strategy has at least 100 forward trades,
  capped at 24 months of forward data.
- Nothing is decided on the basis of interim results.
