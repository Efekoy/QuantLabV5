# V5.1 diagnosis of the failed V5 generator

V5 is archived at `v5-calibration-failed`. This diagnosis uses only its
permitted nuisance artifact, generated synthetic worlds, frozen fit report,
and simulator source. It uses no real DISCOVERY strategy outcome.

## Measured failure

The V5 artifact's contemporaneous NQ/ES log absolute-body correlation is
0.712227. Every diagnostic world missed it by 0.159802–0.161240, implying
synthetic correlation near 0.551. The generator drew NQ and ES magnitude
innovation streams independently and mixed only matched ES innovations with
`1.45 × 0.712227`, clipped to 0.995. Independent zero-body draws, tick
rounding, and different clock-conditioned marginals attenuate observed
correlation after that latent mix. The `1.45` factor was a heuristic, not a
calibration of the final measured statistic. Same-minute sign agreement was
preserved within 0.001, so the failure is magnitude coupling, not sign
coupling.

ES log-volume lag-one target was 0.815052; synthetic error was
0.130671–0.131004, implying synthetic lag correlation near 0.684. The
generator placed the target correlation directly in a Gaussian AR(1) latent
state. Independent zero-volume draws, nonlinear lognormal transforms,
clock-varying marginal scales, and session/roll resets attenuate measured
log-volume persistence. It did not jointly generate NQ/ES volumes, so their
contemporaneous and state dependence was not controlled at all.

The worst ES per-clock volume median/p90 relative errors were 0.274448 and
0.300000 against 0.25. The generator treated the observed unconditional
median and p90 as parameters of the **positive** lognormal draw, then
independently inserted observed zero fractions and rounded. The final mixture
quantiles therefore need not equal the supplied unconditional quantiles. A
lognormal also cannot generally reproduce heavy tails, discrete volume, or
intraday state mixtures from just two quantiles.

Calendar, missing-bar and roll masks passed exact equality. Thus broken
time-of-day *indices* and roll locations did not cause the reported failure;
time-of-day *conditional distributions* were approximated inadequately.
Session/roll resets contributed to lag attenuation. The old generator sampled
gap magnitudes only at session or roll boundaries, leaving other opening
discontinuities unmodeled; its fidelity report did not test this dimension.
No paired range, volume, or state-dependence metric existed in V5, so those
properties cannot be claimed to have passed.

## Engineering implication

A paired, structure-preserving nuisance tape can retain the observed
non-directional magnitude, range, wick, gap and volume sequences exactly,
including cross-market and time-of-day dependence, while drawing independent
timewise signs. V5.1 will compare this with preregistered paired resampling
and state-conditioned sign variants under a new frozen protocol. It will also
test that synthetic signs have no lagged directional edge. This work changes
the null engine only; the V5 strategy grammar, qualification, validation and
power gates are inherited unchanged.
