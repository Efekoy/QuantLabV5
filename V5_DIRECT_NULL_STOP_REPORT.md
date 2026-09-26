# V5 direct-null engineering study: stop report

**STOP: neither preregistered direct-null method passed the frozen nuisance
and zero-edge gates.** The protocol was hash-frozen and committed as
`d7d7920` before the restricted worker accessed DISCOVERY. No method was
selected, and no selected-generator freeze or adaptive strategy run follows.

## Methods and decision

The frozen priority order was joint per-bar reflection, then joint
per-session reflection. Both used the same symmetric reflection bit for
NQ and ES at a matched timestamp or session. Six full paired diagnostic
worlds were run: seeds 9101, 9102, and 9103 for each method. Every world
had valid positive OHLCV and exact source calendar/segments. Reflection
preserved each bar's absolute body, high-low range, body/range ratio,
wick magnitudes, and volume, as well as their timing and paired magnitude
relationships. The complete per-seed metrics are in
`reports/V5_DIRECT_NULL_DIAGNOSTICS.json`.

| Method | Seed | Structural | Max NQ gap error | Max NQ close-close error | V5.1 directional max | Added directional max |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| Paired bar reflection | 9101 | Pass | 28.000 | 1.400 | 0.001088 | 0.308628 |
| Paired bar reflection | 9102 | Pass | 28.000 | 1.556 | 0.001436 | 0.308425 |
| Paired bar reflection | 9103 | Pass | 28.000 | 1.556 | 0.001684 | 0.308676 |
| Paired session reflection | 9101 | Pass | 14.626 | 12.168 | 0.022360 | 0.149081 |
| Paired session reflection | 9102 | Pass | 15.322 | 12.701 | 0.022360 | 0.149042 |
| Paired session reflection | 9103 | Pass | 14.687 | 12.409 | 0.022360 | 0.149062 |

The unchanged per-clock nuisance quantile limit is 0.25; the frozen
directional maximum is 0.01. NQ and ES body/range/volume quantile errors
were zero for both methods, but their gap and close-close errors exceeded
0.25. Per-bar reflection keeps each real open and independently changes
the candle direction. The mismatch between that open and the prior
transformed close creates large artificial gaps and lag-one close-close
sign dependence. Per-session reflection keeps a source session's internal
price sequence up to one sign; it therefore retains serial direction
within that session and creates distorted transitions between sessions.
These are general failure mechanisms across all three seeds, not a
seed-specific exception.

The additional directional diagnostic included close-close sign bias and
lags, gap-sign lags, conditional next close-close sign, and NQ/ES lead
checks. This exposed behavior that the inherited body-sign-only checks
alone would miss. Neither method may be chosen by ignoring those results.
The outcome does not establish that every direct structure-preserving
null is impossible; it establishes that these two frozen methods failed.
No new method or parameter was introduced after observing the results.

## Access and research boundary

The one restricted worker read only canonical NQ and ES DISCOVERY
2010-06-08 through 2018-12-31. Both reads are recorded as
`DIRECT_NULL_STRUCTURE_ACCESS` in the main and study hash-chained ledgers;
both chains verify, and the study access state is `COMPLETE`. The worker
exported only aggregate diagnostics. It exported no raw bars or original
direction sequence and calculated zero candidate outcomes on original
DISCOVERY. The ordinary real research guard remains closed. Validation,
both historical audits, and LIVE_FORWARD were untouched.

Seven focused pre-access tests passed (transformation properties, no
direct-file-access scan, and preregistration guard). Because the direct-null
diagnostic gate failed, the full suite, adaptive all-null calibration,
planted-edge power, final preregistration, and real discovery were not run.
No top-N rule or change to the 30 strategy families, candidate grammar,
advancement, validation, thresholds, or power targets was made.
