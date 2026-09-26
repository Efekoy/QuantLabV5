# V5.1 nuisance/null-engine protocol

**Status: FROZEN ENGINEERING PROTOCOL.** This is an engineering successor
to stopped V5, archived at `v5-calibration-failed`. The 30 strategy families,
Stage A/B/C grammar, candidate IDs, no-cap advancement, validation rules,
power targets, execution, risk diagnostics and later-stage gates are inherited
unchanged. No real V5 strategy outcome has been observed. V5.1 changes only
the nuisance/null engine and its fidelity measurement.

## Access and permitted worker output

After `V5_1_NUISANCE_PROTOCOL_FREEZE.json` verifies, a one-shot worker may
read only NQ/ES DISCOVERY, 2010-06-08 through 2018-12-31, and exactly
`open, high, low, close, volume, symbol`, through `load_view`. Access uses
reason `V5_1_CALIBRATION_NUISANCE_ACCESS` and is mirrored in a fresh V5.1
hash-chained ledger. The worker does no candidate evaluation, P&L, PF,
expectancy, t statistic, ranking, qualification, or parameter search.

The worker emits an unsigned paired nuisance tape: exact timestamps and
contract-segment masks; absolute opening-gap, body and upper/lower-wick ticks;
volume sequence; and the within-bar gap/body sign relation without either
absolute sign. It emits median instrument price and contemporaneous NQ/ES
sign agreement globally and by quartile of joint unsigned body magnitude.
Tied quartile cuts use right insertion; an empty tied bucket uses the global
agreement rate.
No raw prices or historical absolute return-sign sequence leave the worker.
The tape preserves exact non-directional time, state, cross-market, and
volume structure. It is restricted to null engineering and may not be fed
to a real candidate evaluator. Only generated zero-edge OHLCV worlds may be
evaluated. The worker writes an artifact, tape hashes, seed manifest, and
fresh-ledger entries, then closes one-shot access. A crash leaves access
ACTIVE and forbids an automatic retry.

## Frozen candidate architectures

All three modes are evaluated on the same three diagnostic seeds 9101–9103.

1. `paired_sign`: retain the exact paired nuisance tape and draw independent
   symmetric body signs by time. Couple matched NQ/ES signs at the worker's
   global contemporaneous agreement rate. Draw gap sign from the unsigned
   within-bar relation; randomize wick orientation.
2. `paired_day_resample`: permute donor sessions within each calendar month,
   using the same donor-day mapping for NQ and ES. Reassign matched clock
   nuisance states, retaining each instrument's original timestamp and roll
   mask; fall back to the target clock state where a donor bar is missing.
   Draw signs as in mode 1.
3. `state_conditioned_sign`: retain the exact paired tape, but couple
   same-minute signs at the worker's prespecified agreement rate for the
   current joint unsigned body-magnitude quartile. Signs remain independent
   across time. This is a state-conditioned *contemporaneous* sign law, not a
   forecast process.

Mode 1 is also the hybrid structure-preserving null: real unsigned structure
is retained and only directional signs are replaced. Every mode destroys the
historical absolute sign sequence, serial sign dependence and future-conditioned
directional alignment. Selection is deterministic: test all modes; choose
the first passing mode in the listed order. If none passes, STOP. No rerun,
threshold edit, architecture edit or seed substitution is permitted on the
same DISCOVERY calibration information.

## Frozen fidelity metrics and limits

For each seed and instrument, calendar/roll masks must match exactly. At every
session-clock cell with at least 100 observed bars, maximum median/p90
relative error for absolute body, full range, volume, absolute opening gap,
and absolute close-to-close return must be ≤0.25. Synthetic median price must
be within 20% of the worker's instrument median price. The OHLC measures allow one
tick (0.25 points) of quantile discrepancy before relative scaling; volume
allows none. Maximum zero-fraction error for each is ≤0.02. Log absolute-body
and log-volume lag correlations at 1, 5 and 30 bars, within session and
contract segment, must each differ by ≤0.10. This retains every V5 fidelity
dimension and adds gap, close-to-close, zeros and longer lags.

At exact matched NQ/ES timestamps, absolute-body, range, volume and absolute
close-to-close log correlations must each differ by ≤0.10. Their RTH and
non-RTH conditional correlations must each differ by ≤0.10. Thirty-bar
rolling absolute-body cross-market state correlation must differ by ≤0.10.
The generated nonzero-body same-minute NQ/ES sign-agreement fraction must
differ from the worker target by ≤0.05. These are nuisance measurements only;
no candidate-family result is inspected.

## General zero-direction diagnostics

For each generated world, absolute NQ and ES body-sign bias, within-session
sign autocorrelation at lags 1, 2, 5 and 30, next-bar mean sign conditional
on prior body or volume above/below its median, and lagged NQ/ES sign
correlation must each be ≤0.01. These general sign checks do not search the
V5 strategy universe. Any failed world fails its mode. A mode passes only if
all three seeds pass every nuisance and zero-direction check. A generation
exception counts as a failed world and is recorded. The selected
mode is the only one used for executable calibration.

## Downstream executable calibration

If fidelity passes, use the unchanged V5 adaptive search, qualification,
nomination, independent synthetic validation, and plant machinery on worlds
from the selected mode. Use 19 Stage A reference worlds (1000–1018), 500
adaptive null reference worlds (2000–2499), 200 distinct all-null test worlds
(3000–3199), and the frozen 48-cell plant grid at 0.05/0.075/0.10/0.15 R,
100/250/500 events per 252 sessions, and four shapes. Use 20 independent
discovery/validation pairs per cell, except 100 pairs for the 0.10 and 0.15 R
500/year stable-plateau core cells. The original V5 exact-binomial false
survivor upper-95 limit ≤0.10 and end-to-end power lower-95 limits ≥0.70 and
≥0.90 remain binding. Failed realized plant dose/frequency checks fail the
campaign. No real strategy search begins until all checks pass and the final
V5.1 preregistration is committed and tagged `v5.1-prereg`.

The later-stage sequence remains DISCOVERY → VALIDATION → both historical
audits revealed together → LIVE_FORWARD, with each freeze and no-cap rule
unchanged. This engineering access never opens a later partition.
