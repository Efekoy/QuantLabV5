# V5 direct structure-preserving null study protocol

**Status: FROZEN DESIGN BEFORE DISCOVERY STRUCTURE ACCESS.** This is a new
controlled engineering study after the archived V5, V5.1, V5.2, and V5.3
calibration failures. It is not V5.4. No real strategy search is authorized.

## Authorized source and boundary

Only `research/run_direct_null_study.py`, through `load_view` and the
`quantlab5.direct_null.access.scope` gate, may read canonical synchronized
NQ/ES DISCOVERY 2010-06-08 through 2018-12-31, with columns open, high,
low, close, volume, symbol. Every read is recorded as
`DIRECT_NULL_STRUCTURE_ACCESS` in both the main and study ledgers. The
worker keeps source bars in process memory and emits only aggregate
diagnostics. It emits no raw OHLCV, original sign sequence, candidate P&L,
PF, expectancy, t statistic, ranking, or qualification. The ordinary
preregistration guard remains closed. Validation, both historical audits,
and LIVE_FORWARD are outside this scope.

## Frozen methods and selection

The methods, in priority order, are `joint_bar_reflection` and
`joint_session_reflection`. For each seed, a symmetric bit is drawn for
every unique paired timestamp (bar reflection) or paired session-end date
(session reflection). The same bit applies to both instruments when the
key matches. A positive bit leaves the source candle unchanged; a negative
bit reflects all OHLC prices about the original bar open or the source
session's first open, respectively. Reflection swaps the transformed high
and low correctly. Timestamps, volume, contract segments, and the observed
NQ/ES synchronization stay exact. Both methods preserve each individual
bar's body magnitude, high-low range, body/range ratio, and wick magnitudes,
with upper and lower orientation exchanged under reflection. They also
preserve volume and magnitude clustering, time-of-day patterns, and
contemporaneous NQ/ES magnitude/range/volume dependence. Bar reflection
does not preserve the original gap or close-close process. Session
reflection preserves within-session signed increments up to one common
sign but can change transitions between sessions. Neither property may be
silently excluded from the fidelity decision.

Reflection is deliberately a diagnostic candidate, not presumed a valid
null. Original opens or within-session directional sequences may still
carry predictive information; the frozen zero-edge checks below must
detect that. No source bars or transformed worlds are exported by this
first worker. If a method passes every gate, a separate selected-generator
freeze and restricted calibration worker must be committed before any
additional structure access or adaptive calibration.

## Diagnostic worlds and gates

Seeds are exactly 9101, 9102, 9103 for each method, yielding six complete
paired worlds. No seed may be replaced or averaged away. A method passes
only if **every** world passes all requirements:

1. Structural: finite OHLCV, positive OHLC, correct ordering, nonnegative
   volume, monotonic timestamps, exact original calendar/segment masks,
   and matching paired NQ/ES timestamp keys. No clipping or seed repair.
2. Nuisance: the unchanged V5.1 checker and thresholds: every per-clock
   median/p90 body, range, gap, close-close, and volume quantile error at
   most 0.25 after its original tick allowance; zero-fraction error at
   most 0.02; lag body/volume error at most 0.10; median-price relative
   error at most 0.20; cross-market nuisance error at most 0.10; and
   same-minute sign-agreement error at most 0.05. The frozen checker also
   covers volatility-state and session-conditioned dependence. These
   limits are not weakened after result inspection.
3. Zero-edge: unchanged V5.1 directional maximum at most 0.01, **plus**
   close-close sign bias, lags 1/2/5/30, gap-sign lags 1/5, next close-close
   sign conditional on prior close-close magnitude half, and NQ-to-ES and
   ES-to-NQ next aligned close-close sign correlations. Every added
   absolute diagnostic maximum must be at most 0.01. These are generic
   directional diagnostics, independent of the 30 strategy families.

The first method in the fixed priority list passing all six per-method
world gates is selected. If neither passes, stop immediately and write
`V5_DIRECT_NULL_STOP_REPORT.md`. Do not tune either method to failed
seeds, add a method after inspection, run adaptive strategy calibration,
or create an automatic fully synthetic successor.

## Conditional calibration

Only after a selected method passes: freeze and commit its transformation,
seed policy, original-nuisance comparisons, zero-edge limits, and source
access rules in `V5_DIRECT_NULL_GENERATOR_FREEZE.json`. Then run the actual
unchanged adaptive V5 Stage A/B/C executable on 19 Stage A reference,
500 adaptive null reference, and 200 all-null test worlds under the frozen
sequential Monte Carlo 50/100/200/500 procedure. The false-survivor
upper-95 gate remains at most 0.10. If that passes, run 0.05/0.075/0.10/
0.15 R planted effects at 100/250/500 trades/year for isolated needle,
stable plateau, heterogeneous family, and regime-specific shapes: 20
pairs per cell, 100 for core broad 0.10/0.15 R 500/year plateau cells.
The inherited lower-95 power limits are 0.70 and 0.90 for the respective
core cells. No stream proxy may stand in for executable search. No top-N
scientific cutoff is introduced. Only a complete pass permits final
`V5_PREREGISTRATION_FREEZE.json` and tag `v5-prereg`; real DISCOVERY
strategy research remains closed until that tag and all hashes verify.
