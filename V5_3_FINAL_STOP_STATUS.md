# QuantLabV5.3 final stop status

**STOP: frozen nuisance fidelity failed.** The V5.3 generator design was
hash-frozen and committed as `f457f4f` before decision seeds 9101–9103 were
run. No V5.3 generator adjustment follows this decision.

## Gate sequence

1. The V5.2 range diagnosis used the already permitted V5.1 unsigned tape.
   It recorded the complete per-clock median/p90 range quantile error vector
   in `reports/V5_3_RANGE_DIAGNOSIS.json`. V5.2 seed 9103 NQ had two errors
   above the frozen 0.25 limit; the maximum was 0.327393.
2. V5.3 separated positive causal open/close prices from point-valued
   intrabar wick excursions. The complete structural stress covered seeds
   0–999 and 1002: 1,001 valid NQ/ES worlds, zero invalid worlds, zero
   overflow/underflow events, zero OHLC failures, and a minimum OHLC value
   of 543.168986. The design and stress report were then hash-frozen.
3. The unchanged frozen nuisance and zero-edge checker ran only after that
   commit. All three decision seeds passed the zero-edge maximum of 0.01
   (observed maxima 0.000796, 0.001167, 0.001525). All three failed
   nuisance fidelity.

## Failed fidelity measurements

The frozen per-clock quantile error limit is 0.25 and the median-price
relative error limit is 0.20. Values below are the maximum errors reported
by the unchanged checker for each instrument and seed.

| Seed | Instrument | Body | Close-close | Gap | Range | Median price |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 9101 | NQ | 0.350076 | 0.349701 | 0.323845 | 0.211202 | 0.374564 |
| 9101 | ES | 0.314527 | 0.343947 | 0.333282 | 0.212941 | 0.458125 |
| 9102 | NQ | 0.287517 | 0.305172 | 0.093126 | 0.163787 | 0.081051 |
| 9102 | ES | 0 | 0 | 0 | 0 | 0.044308 |
| 9103 | NQ | 0.548385 | 0.488843 | 0.368434 | 0.318717 | 0.267937 |
| 9103 | ES | 0 | 0 | 0 | 0 | 0.122276 |

The V5.3 range separation reduced some range errors, but seed 9103 NQ
still exceeded the same range limit. The uncentered causal exponential
close path also distorted body, gap, close-close, and median-price metrics,
especially in seed 9101. These are observed failures of the frozen design,
not grounds to select a favorable seed or revise the limits.

## Engineering conclusion and boundary

V5.1 failed positivity, V5.2 passed positivity but failed range fidelity,
and V5.3 passed broad structural stress but failed multiple frozen nuisance
metrics. This sequence is evidence that the current fully synthetic OHLC
construction has not preserved the joint price and intrabar nuisance
structure needed for this calibration. A future separately authorized study
could assess a direct structure-preserving null using the existing lawful
unsigned representation; these results do not prove every fully synthetic
approach impossible. There is no automatic V5.4 here.

No final null-generator freeze, adaptive all-null or planted-power run,
V5.3 preregistration, real strategy discovery, later partition access, or
new real-market read was performed. The V5, V5.1, and V5.2 failure archives,
strategy grammar, candidate IDs, thresholds, and sealed partitions remain
unchanged.

The decision evidence is `reports/V5_3_NUISANCE_FIDELITY.json`; the pinned
generator design is `V5_3_GENERATOR_PROTOCOL_FREEZE.json`.
