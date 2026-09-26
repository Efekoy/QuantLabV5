# V5.4 post-original-V5 broad discovery protocol

**Status: pre-outcome engineering design.** V5.4 is a new iteration inside
QuantLabV5. The original V5 result is immutable: 60 Stage A rules were tested,
none qualified, and validation, both historical audits, and LIVE_FORWARD were
unopened. That result motivated broader search. The 2010–2018 partition is
explicitly DEVELOPMENT/DISCOVERY data. V5.4 is not part of the original
`v5-prereg` campaign.

## Fixed scientific universe

The only 30 mechanism implementations are the original
`SignalContext.direction` branches E01–E30. The family-specific lookback and
threshold lists in `quantlab5/v54/universe.py` expand their existing numeric
axes; they do not replace mechanism code. E11 and E22 have no exposed numeric
core axis and therefore retain one core state each. The original C15 event and
its estimator are fixed within those families. Every family, every core state,
and every applicable filter, direction, session, entry, and management variant
is evaluated. There is no Stage A family kill, score rank, or top-N limit.

The canonical signal axes are long/short/both; the existing RTH, RTH AM, and
RTH PM windows; no filter, each of three applicable filters, or the one
registered two-filter interaction for that family; and entry at the next
eligible bar open or one bar later. A delayed entry requires the same session
and contract and still has to fall in the registered entry window. The
original V5 signal implementation only emits executable signals for next
opens in 09:35–15:15 New York; its Globex window is therefore exactly
equivalent to full RTH and is removed as a static semantic duplicate.

Filters use only completed-bar data. Volatility compares 20-bar to 120-bar
absolute-return means; high is ≥1.25 and low ≤0.8. Volume high is current
volume ≥1.5 times the *prior* 60-bar mean. Path efficiency is 15-bar net
displacement divided by the sum of absolute movements, ≥0.55. ES agreement
and disagreement compare the completed synchronized ES 15-bar return sign
to the candidate side and require valid ES alignment outside its roll mask.
Relative volatility high compares 30-bar NQ and ES absolute-return means at
ratio ≥1.5. Trend young and old are respectively ≤30 and ≥60 bars since a
30-bar EWMA sign change. Inapplicable and contradictory filter pairs are
absent. All such thresholds are fixed *filters*, not post-result choices.

There are six entry stop definitions: 0.75, 1.0, or 1.5 times the prior
completed 15-bar ATR-like point distance from the original V5 engine; the
signal-bar opposite extreme; and the 5- or 15-bar recent opposite swing
extreme. Structural stops use the signal bar and earlier bars plus the known
entry open. An entry with nonfinite or less than one tick of stop distance is
skipped. The 198 executable management variants are the disjoint template
list in `V5_4_SEARCH_UNIVERSE.json`, including fixed-R targets, session and
time exits, break-even, one-of-two-integer-MNQ partial exits, R trailing,
and a next-open exit when the original family state ceases to agree with the
position. Mechanism state is read at the prior completed bar. A partial
requires two whole MNQ contracts; a budget incapable of funding both is
recorded as a risk-floor skip. No fractional futures position is assumed.

The structure-stop/fixed-target template uses a structural protective stop and
a target at a fixed multiple of that risk. It is not a separately derived
structural price target. No unsupported mechanism-derived price target is
claimed. The shared sparse Numba kernel evaluates management from cached entry events.
It uses pessimistic stop-first resolution when a bar touches a stop and a
favorable order without a known opening sequence. A stop gap fills at the
worse open. A favorable target gap fills at the resting target, never a better
price. Break-even and trailing changes use the completed bar and become
effective only on the next bar. Time exits use elapsed bar-start minutes and
session/roll flats remain mandatory. Baseline and stress costs are the frozen
MNQ assumptions in `config/costs.yaml` for one round trip per integer
contract. Each candidate's net R divides its average per-contract points
after friction by its entry stop distance.

The configured MNQ $1 round-trip commission is explicitly marked an
unvalidated research placeholder in `config/costs.yaml`, inherited from the
original V5 protocol. It is frozen for comparability, with the existing
stress-cost scenario shown separately. Dollar-budget results are model
diagnostics and cannot establish a real firm's net deployability until
observed MNQ fees and execution costs are validated.

Q54 IDs are SHA-256 content IDs from canonical complete specifications in
namespace `quantlab5.v54.broad_discovery`. The finite axis lists and canonical
Cartesian iterator define the complete universe without an unwieldy
14-million-row JSON file. The inventory records attempted invalid
management combinations and the exact RTH/Globex duplicate removal.

## Development qualification and local stability

The exact five V5 economic discovery conditions are reused as the V5.4
nomination gate: at least 120 executed trades, at least six active calendar
years, positive baseline net R, positive stress-cost net R, and positive
matched same-clock/direction drift excess. The shadow benchmark is the
original unconditional 60-minute same-clock directional drift normalized by
the original 15-bar point risk, with MNQ baseline friction. There is no
discovery p-value requirement and no rank or correlation deletion. Every
rule meeting all five conditions advances, even if many are similar.

All 2010–2018 outcomes are exploratory. For each qualifier record exact
2010–12, 2013–15, and 2016–18 contributions and its adjacent lookback and
threshold neighbors, holding every other choice fixed. Report the fraction
of neighbors with positive baseline *and* stress net R. A zero-neighbor
family is marked not applicable. This is a descriptive stability score; no
unregistered threshold is inserted into the five-part nomination gate.
Identical entries, side overlap, position overlap, and daily-P&L correlation
are descriptive annotations among qualifiers and never remove one.

## Primary 2019–2022 confirmation

Only after the complete V5.4 discovery result and exact qualifying candidate
set are frozen may 2019–2022 be opened. Every Q54 candidate is evaluated
unchanged. The primary hypothesis is a **one-sided positive mean daily net R**
test, with zero-trade session days included. Per-candidate Bartlett HAC lag
20 standard errors give one-sided normal-tail p-values. Apply Holm stepdown
across the entire frozen exact-candidate hypothesis family at alpha 0.05.
Holm controls familywise error under arbitrary cross-candidate dependence;
it is the frozen conservative choice because the original Romano-Wolf
matrix bootstrap cannot be assumed computationally safe for an unbounded
qualifier set that may reach tens of thousands or more. No multiplicity
method is chosen after validation results.

`SUPPORTED` requires Holm-adjusted p≤0.05, at least 40 executed validation
trades, at least two active years, positive mean daily baseline net R,
positive stress-cost net R, and positive matched excess. `REJECTED` requires
the upper one-sided 95% HAC bound below zero or an execution failure of the
frozen rule. Every other exact candidate is `INCONCLUSIVE / UNDERPOWERED`.
All supported candidates enter the scientific cohort; no cap or correlation
deletion applies. No portfolio selection is part of the primary V5.4
campaign because no new portfolio rule is established by this iteration.

## Historical audits and access

The complete supported cohort and evaluation code/costs are frozen before
historical audits. The same exact candidate set is evaluated on 2023–2025
and 2026 through the frozen common NQ/ES endpoint. Audit 1 performance is
sealed until Audit 2 is complete and both cohort/hash checks pass; then the
reports are revealed together. A weak Audit 1 candidate still appears in
Audit 2. No historical period is called genuinely prospective because prior
V2/V3/V4 program knowledge exists. LIVE_FORWARD remains sealed.

Each audit is labeled separately using the original V5 frozen audit rule:
one-sided positive mean daily net R with Bartlett HAC lag 20, Holm correction
over the complete scientific cohort at alpha 0.05, positive stress net and
matched excess, and at least 20 trades for `SUPPORTED`. An upper one-sided
95% HAC bound below zero is `REJECTED`; otherwise the label is
`INCONCLUSIVE / UNDERPOWERED`. A dual-audit survivor requires `SUPPORTED`
in both audits, regardless of the first audit's result at the time the
second is evaluated.

The existing V5 stage machine is already at `VALIDATION_FROZEN` after its
empty cohort. V5.4 therefore uses a separate tagged preregistration gate
and V5.4-specific read purposes. Full DISCOVERY NQ/ES reads are permitted
only after `v5.4-prereg` verifies. A V5.4 validation read additionally
requires a verified complete V5.4 discovery freeze; each audit requires the
preceding cohort/report freeze. A V5.4 read never authorizes LIVE_FORWARD.

## Computation and auditability

The first pass stores one compact metric row per specification in a
checkpointed memory-mapped array. A checkpoint commits only after all
management rows for one signal configuration have flushed. On restart,
committed groups are skipped and any uncommitted group is overwritten.
Every qualifier is rerun with full captured trades; its compact metrics
must match exactly. Integer MNQ risk-floor coverage is recorded at
$250/$300/$350/$400. The full search has no adaptive stop for weak or
strong families. All gates, source hashes, inventory, data-access ledger,
and completed test evidence must be frozen before original real V5.4
strategy outcomes are calculated.
