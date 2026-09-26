# V5.2 diagnosis: V5.1 seed 1002 nonpositive price

This replay used only the archived V5.1 unsigned nuisance tape and synthetic
seed 1002. It did not evaluate a strategy or access raw real prices.

The V5.1 null reconstructs prices **additively**:

`change[t] = randomized_gap[t] + randomized_body[t]`,
`close[t] = base + cumulative_sum(change)[t]`,
`open[t] = close[t] - randomized_body[t]`.

It sets `base` so the synthetic median close equals the observed permitted
NQ median of 4109.25 points. For seed 1002, `base` was 4658.50 and the
first open was 4658.50. The synthetic cumulative change fell to −5335.25
points. The minimum NQ open and close were both −676.75 points at bars
2,773,907 and 2,773,906 respectively (2018-12-27 23:05 and 23:04 UTC).
The final close was −238.50. The first nonpositive **close** occurred at
bar 2,752,042 (2018-12-04 10:40 UTC, −1.50); the first nonpositive **open**
occurred one bar later (10:41 UTC, −1.25). The frozen generator checked open
before forming the wick and raised there. Its largest individual NQ bar
change was +84.00 points and smallest −104.25 points. The failure came from
the cumulative additive random walk relative to a fixed price anchor, not
from one singular return explosion.

OHLC reconstruction has a second positivity problem: it sets
`low = min(open, close) - randomized_down_wick`. Replaying the same random
sequence without aborting shows the first nonpositive NQ low at bar
2,718,635 (2018-10-30 14:20 UTC, −2.50), while the bar's cumulative change
was −4651.50 and its down wick was 9.50 points. Thus even a positive open
and close can yield an invalid low. A close-only multiplicative fix would
not suffice.

ES remained positive in the same replay: minimum open/close 322.25 and
minimum low 320.00. NQ's signs are drawn independently across time; the
same-minute cross-market coupling sets ES signs from NQ and cannot cause the
NQ price crossing. Both markets do share the paired unsigned nuisance tape.

The V5.2 correction must construct **all** OHLC components as positive
multiplicative ratios. It must preserve the tape's relative body, gap, wick,
range, volume, calendar, and cross-market relationships as far as the frozen
fidelity metrics require, and must pass those unchanged metrics and the
original seed 1002 before any new generator freeze or power test.
