# QuantLabV5.3 generator protocol

**Status: FROZEN GENERATOR DESIGN.** V5.3 is an
engineering successor to archived V5.2, which fixed positivity but failed
the unchanged seed-9103 NQ range quantile limit. The V5, V5.1 and V5.2
failure commits, tags, outcomes and thresholds remain unchanged. V5.3
changes only the synthetic null OHLC construction. All 30 strategy families,
candidate IDs, Stage A/B/C grammar, advancement, validation, power and
later-stage rules are inherited unchanged.

## Inputs and access

The generator uses only the already permitted V5.1 unsigned paired nuisance
tape and its calibration artifact. There is **no new real DISCOVERY read**.
The tape supplies exact NQ/ES timestamps, segments, unsigned per-bar gap,
body and upper/lower wick ticks, volume, and a within-bar gap/body sign
relation without an absolute historical sign. The artifact supplies the
instrument median-price anchor and contemporaneous NQ/ES sign agreement.
Raw real price and sign sequences are unavailable to the generator.

## Causal close and body process

For each minute, draw a fresh symmetric NQ body sign. Draw ES signs
independently except at matched timestamps, where signs are coupled at the
preexisting artifact's same-minute agreement probability. Sign draws are
independent across time and do not consult future nuisance or candidate
outcomes. Randomize the opening-gap sign consistently with the unsigned
within-bar gap/body relation. Let `delta[t]` be the resulting signed gap plus
signed body in points, and `anchor` the permitted instrument median price.
The log close is

`log_close[t] = log(anchor) + cumulative_sum(delta[0:t]) / anchor`.

The log open is `log_close[t] - signed_body[t] / anchor`. Exponentiation
gives strictly positive open and close for finite representable values.
No path-wide median centering or future statistic is used. The same fixed
anchor applies to every seed. No clipping, winsorization, selected-seed
bound or tail adjustment is applied.

## Separate intrabar excursions

Upper and lower wick tick magnitudes are taken from the unsigned tape;
their orientation is independently randomized per bar. Let
`upper_core = max(open, close)`, `lower_core = min(open, close)`, and `u,d`
be the unsigned upper and lower excursion points. Set

`high = upper_core × exp(log1p(u / upper_core))`,
`low = lower_core × exp(−log1p(d / lower_core))`.

High equals upper core plus the recorded upper excursion up to floating
rounding. Low is positive and its downward excursion approaches `d` when
`d` is small relative to price. This intrabar range process is separate
from the evolving close-price multiplier. Paired NQ/ES magnitude, wick,
volume and session states come from the same source tape. This preserves
their contemporaneous and lagged nuisance structure as far as the frozen
metrics test. The body magnitude still arises from the multiplicative
close process; it is not independently retuned.

## Numerical and structural validity

The generator raises on nonfinite or nonpositive OHLC, overflow or underflow.
Every complete world must have finite OHLCV, positive open/high/low/close,
`high ≥ max(open,close)`, `low ≤ min(open,close)`, `high ≥ low`, nonnegative
volume, strictly increasing timestamps, exact tape calendar per instrument,
and more than one million matched NQ/ES timestamps. There is no post-hoc
repair of an invalid world.

Before the fidelity decision, run complete structural worlds for deterministic
seeds `0..999` plus the original failing seed `1002` (1,001 worlds). The
target is zero invalid worlds, zero numerical overflow/underflow events,
and positive minimum price. A structural failure requires a general
mathematical correction and a new full stress run before design freeze.
Development unit/property checks use small artificial tapes and verify wick
effect, causal prefix invariance, sign variation and OHLC validity. They do
not use the frozen fidelity decision seeds.

## Unchanged nuisance and zero-edge decision

After structural success, hash-freeze this document, generator, artifacts,
stress result, seed policy, tests, unchanged V5.1 fidelity checker and
thresholds in `V5_3_GENERATOR_PROTOCOL_FREEZE.json`, then commit. Only
afterward run the unchanged V5.1 nuisance fidelity on seeds
`9101, 9102, 9103`. Every instrument, every world, every per-clock
median/p90, zero-fraction, lag, paired dependence, session dependence and
median-price requirement remains binding. In particular, NQ range maximum
relative quantile error stays ≤0.25, and no failed seed can be averaged
away. The unchanged general zero-direction diagnostic maximum stays ≤0.01.
If either fidelity or zero-edge fails, STOP and report it. Do not adjust
the generator against that seed or create V5.4 automatically.

## Conditional downstream calibration

Only after structural validity, nuisance fidelity and zero-edge pass,
create a final null-generator freeze. Then use the inherited actual adaptive
Stage A/B/C search, 19 Stage A reference worlds, 500 adaptive null reference
worlds, 200 all-null test worlds, sequential Monte Carlo looks 50/100/200/500,
and the unchanged false-survivor upper-95 ≤0.10 gate. Plant 0.05, 0.075,
0.10 and 0.15 R at 100/250/500 events/year in isolated needle, stable
plateau, heterogeneous family and regime-specific forms, with 20 pairs per
cell and 100 for core 0.10/0.15 R 500/year plateau cells. Their original
lower-95 power limits ≥0.70 and ≥0.90 remain binding. No stream proxy or
real DISCOVERY strategy outcome is permitted during calibration.

Final V5.3 preregistration and tag `v5.3-prereg` are allowed only after all
frozen gates and complete tests pass. Until then, the ordinary real-market
strategy guard remains closed and later partitions stay sealed.
