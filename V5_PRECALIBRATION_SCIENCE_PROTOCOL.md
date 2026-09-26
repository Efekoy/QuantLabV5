# V5 precalibration science protocol

**Status: FROZEN SCIENCE DESIGN.** This document becomes binding when
`V5_PRECALIBRATION_SCIENCE_FREEZE.json` has status `FROZEN`, its body and file
hashes verify, and the one-shot calibration state is `ARMED`. The ordinary
real-strategy guard remains closed until final `v5-prereg`.
The ledger already contains bootstrap structural counts and a one-day
DISCOVERY isolation probe from before this protocol. The science freeze will
disclose those reads; it establishes the design before the **new** nuisance
calibration access, not before every historical structural read.

## Scientific universe and decisions

The executable grammar is `quantlab5/v5/candidate_inventory.py`; the generated
inventory is `reports/V5_CANDIDATE_INVENTORY.json`. It contains 30 mechanisms,
60 Stage A directional specifications, 214 possible Stage B specifications,
at most 57 conditional Stage C evaluations per adaptive run, and 710 distinct
IDs across all branches. Signal, entry, stop and exit definitions are pinned by
`signals.py`, `market_search.py`, the cost configuration and the final science
freeze hash map. Stage A expansion is joint market-null family p ≤0.10 plus
≥120 executed trades, ≥6 active years, positive stress net R and positive
matched drift/time excess. All eligible families expand. Within each expanded
family, the Stage B parent with largest daily HAC t among rules having ≥120
trades, positive stress net and positive t generates the registered Stage C
interactions. Ties use candidate ID. Every evaluated rule is retained. A
discovery qualifier has ≥120 trades, ≥6 active years, positive baseline mean
daily R, positive stress net and positive matched excess. Every qualifier
advances; nomination, similarity and correlation annotate only.

Independent synthetic validation evaluates every qualifier without retuning.
For each family and direction, average its frozen member daily streams on the
common calendar, including zero-trade days. Apply the common-index stationary
bootstrap Romano-Wolf stepdown across **all** family-direction ensembles, with
500 resamples, expected block length 20, HAC lag 20, and alpha 0.05. If any
adjusted p is within 0.01 of 0.05, rerun all groups with 2,000 fresh
preassigned resamples; a group still within 0.01 is UNRESOLVED. Support
requires adjusted family-direction p ≤0.05, positive ensemble mean in each
chronological half, and positive whole-period mean for at least
`ceil(0.75 × number_of_members)` members. Every member of a supported group
survives if it has ≥40 executed trades, ≥2 active years, positive baseline
mean daily R, positive stress net and positive matched excess. A discovery
nominee is reported but never used to remove another qualifying member.
Unresolved adjusted-p decisions do not qualify. This validation rule supersedes
the earlier review draft's representative-only proposal, before any new
DISCOVERY calibration read.

## Nuisance access and zero-edge worlds

The one-shot worker may read only NQ and ES `DISCOVERY`, exactly
2010-06-08 through 2018-12-31, through `load_view` with the six canonical
OHLCV/symbol columns and reason `CALIBRATION_NUISANCE_ACCESS`. It has no
strategy evaluator, candidate P&L, PF, t statistic, expansion, qualification,
ranking or parameter optimizer. Its allowed outputs are exact timestamps and
contract-segment masks, per-clock observation counts and unconditional
absolute body/range/wick/volume median, p90 and zero fraction, absolute
session-gap quantiles, lag correlations of log absolute body and log volume,
median price level, and contemporaneous NQ/ES sign agreement and absolute
body dependence. These are nuisance parameters, not conditional future-return
statistics. Signed return sequences and conditional predictive statistics
remain inside the worker process. The worker writes a hash-pinned calendar
template and `V5_DISCOVERY_NUISANCE_CALIBRATION.json`, then marks the one-shot
access state COMPLETE. A crash leaves it ACTIVE and forbids automatic retry.

`calibrated_null.py` independently redraws symmetric signs for every minute,
couples same-minute NQ/ES signs at the calibrated agreement rate, draws
absolute body/volume/wick magnitudes from the per-clock distributions with
lag-one nuisance persistence, preserves exact timestamps, missing-minute and
roll patterns, and randomizes signed session gaps. It does not consume raw
real OHLCV or signed return sequences. This destroys serial directional
dependence and any real sign-volume predictive alignment. It preserves
calendar, time-of-day magnitude structure, approximate magnitude clustering,
and contemporaneous cross-market nuisance association. The main research
process may inspect the permitted nuisance artifact and **synthetic** worlds,
never real DISCOVERY prices during this phase. Model-fit checks must report
per-clock median/p90 errors for body, range and volume, lag-one magnitude
and volume dependence error, NQ/ES sign-agreement and absolute-body correlation errors and missing/roll
pattern identity. The zero-edge simulator is rejected if median/p90 relative
error beyond one OHLC tick exceeds 25% on clocks with ≥100 observations
(volume has no tick allowance), lag-one correlation error
exceeds 0.10, sign-agreement error exceeds 0.05, or calendar/roll/missing
patterns differ. Contemporaneous absolute-body correlation error must be
≤0.10. The diagnostic code and thresholds must be pinned before
the worker runs.

## Market plants and executable calibration

`market_plant.py` predeclares the E03 long mechanism as the planted target.
Four plant shapes are isolated Stage A needle, neighboring-rule plateau
(at least two E03 variants fire), heterogeneous neighboring family
(at least one variant fires, with prespecified 0.65/0.85/1.0/1.15 strength),
and regime-specific effect (`|r_t| ≤ 2v_t` at the completed decision bar).
Only completed-bar causal E03 signals select synthetic opportunities. A fixed
seed draws nonoverlapping opportunities at approximately 100, 250 or 500 per
252 sessions. The plant adds expected NQ drift of 0.05R, 0.075R, 0.10R or
0.15R after selected decisions and before the frozen exit, using unbiased
stochastic tick rounding. A fixed bracket-and-eight-step bisection sets one
global dose factor per **synthetic** world using the selected-event
counterfactual executed R shift; it does not change selected events or consult
real market outcomes. Report both requested and realized net-executable
effect; a requested grid cell is invalid if the realized mean shift differs
by more than 20% or the realized annual event frequency differs by more than
20% from its 100/250/500 target. Discovery and independent synthetic validation worlds use
disjoint seeds. A target qualifies for the primary end-to-end power event only
if E03 Stage A expands, its Stage C branch is evaluated, an affected frozen
candidate qualifies, nomination occurs for plateau/heterogeneous shapes, and
an affected candidate survives independent validation. Count every failed
step separately.

Use 19 independent zero-edge worlds for the Stage A family-max reference,
500 independent full adaptive zero-edge worlds for sequential global search
inference at cumulative looks 50/100/200/500, and 200 separate all-null
market searches for false-positive measurement. Reuse the common reference
worlds only as the frozen test reference, never as test replicates. Run 20
independent discovery-plus-validation planted pairs in every effect × frequency
× shape cell. Run 100 pairs for the two core plateau cells at 500/year and
0.10R/0.15R. All-null size passes only when the one-sided 95% exact-binomial
upper bound on **any false validation survivor** is ≤0.10. The practical power
gate passes only when the one-sided 95% lower bound on the complete primary
event is ≥0.70 for 0.10R plateau at 500/year and ≥0.90 for 0.15R plateau at
500/year. All other cells are reported without threshold changes. A failed
gate ends V5 launch; nuisance findings may not be used to redesign strategies.

`run_v5_executable_calibration.py` runs the search and validation only on
generated zero-edge or planted markets. Its checkpoint contains synthetic
seeds, per-world decisions and hashes of the precalibration freeze and nuisance
inputs. No real strategy outcome is calculated before final `v5-prereg`.
