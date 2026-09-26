# V5.3 diagnosis of V5.2 range distortion

This diagnosis uses the archived V5.2 generator, the already permitted V5.1
unsigned nuisance tape, and seeds 9101–9103. It contains no real strategy
outcome. The complete frozen session-clock × median/p90 range-quantile vector
for each instrument and seed is in `reports/V5_3_RANGE_DIAGNOSIS.json`.

## Full-vector findings

Each NQ world has 2,730 tested clock/quantile cells and each ES world 2,732.
The frozen error subtracts one 0.25-point tick from the absolute quantile
gap and divides by the target quantile (with a 0.25-point floor).

| Seed | Instrument | Maximum frozen range error | Cells above 0.25 | Median signed relative difference | Fraction of cells with generated range above target |
| --- | --- | ---: | ---: | ---: | ---: |
| 9101 | NQ | 0.064563 | 0 | +0.019458 | 0.6150 |
| 9101 | ES | 0.074238 | 0 | +0.101790 | 0.7522 |
| 9102 | NQ | 0.179806 | 0 | +0.140121 | 0.8542 |
| 9102 | ES | 0.000000 | 0 | +0.030977 | 0.5981 |
| 9103 | NQ | **0.327393** | **2** | +0.128915 | 0.8033 |
| 9103 | ES | 0.080822 | 0 | +0.054534 | 0.7178 |

For seed 9103 NQ, the worst cell is session minute 1310, p90: target
6.50 points, generated 8.878055, frozen error 0.327393. The other failing
cell is minute 130, p90: target 1.50, generated 2.155191, error 0.270127.
Seed 9102 NQ shows the same upward tendency without exceeding the limit;
its worst p90 is minute 934, 7.25 versus 8.803595, error 0.179806.
The distortion is therefore systematic in direction and variable in size,
not an isolated numerical glitch at seed 9103.

## Mechanical cause

V5.2 forms latent additive open, close, high and low from the unsigned body,
gap, and wick tape, then applies the same exponential price map to all four.
For small intrabar excursions, the transformed range is approximately
`local_price / anchor × latent_range`. The local price multiplier changes
along each synthetic cumulative path. This makes the recorded point-valued
body **and both wicks** expand or contract together with the close-price
level. Seed 9103's path gives NQ a high enough local multiplier to inflate
range p90 at many clocks, especially the two failing cells.

The high/low calculation preserves ordering and positivity, so OHLC
validity itself did not fail. The separate V5.2 body quantile error for
seed 9103 NQ was 0.170496, below 0.25; range error was larger because
transformed upper and lower wick excursions also grew. The original
body-to-range relationship is only approximately preserved under the
nonlinear map. Time-of-day conditioning remained in the tape, but the
path-dependent multiplier changed each clock's point-valued quantiles.
The underlying volume sequence and its clustering were unchanged; V5.2
volume error was zero. Existing paired NQ/ES magnitude, range and session
dependence passed their frozen limits, but this does not excuse the NQ
per-clock range failure. Gaps were transformed by the same map as body and
wicks; they were not the largest failed V5.2 metric. No tail cap or
winsorization was used, and the range distortion is not attributed to a
single extreme return.

## V5.3 architectural response

The close path must remain multiplicative to guarantee positivity. Upper
and lower intrabar excursions will instead be generated separately from
the already permitted unsigned wick tape, using positive log-distance
constructions around the transformed open/close body. This removes the
unnecessary multiplication of wick points by the evolving close level.
The design will be frozen before the unchanged fidelity seeds are used to
judge it.
