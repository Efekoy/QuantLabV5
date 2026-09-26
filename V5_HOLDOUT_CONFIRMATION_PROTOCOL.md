# V5 holdout-confirmation protocol

**Pre-DISCOVERY design.** This protocol supersedes the failed null-market
calibration prerequisite. It is frozen before any original real V5 strategy
outcome is calculated. The exact program is pinned in
`V5_HOLDOUT_CONFIRMATION_PROTOCOL_FREEZE.json`.

## Fixed search universe and exploratory qualification

The 30 mechanisms, 60 long/short Stage A specifications, applicable
one-factor Stage B variants, conditional Stage C interactions, deterministic
Q5 IDs, causal next-open entry, common stop/exit, baseline/stress costs,
duplicate annotation, and four MNQ risk budgets are those in the pinned
code/config. No new rule, threshold, side, family, filter, or top-N cap may
be introduced after DISCOVERY opens.

Stage A family expansion retains its frozen threshold: adjusted family
max-t p ≤0.10, ≥120 executed trades, ≥6 active years, positive stress
net R, and positive matched drift/time excess. Because the market-null
reference failed calibration, the p-value reference is now the centered
stationary bootstrap of the **complete 60-rule Stage A daily net-R matrix**.
Use 500 preassigned resamples, one common session-day index across all
rules, expected block length 20 days, Bartlett HAC lag 20, seed 515001,
and the maximum t across every Stage A rule in each resample. The same
reference maximum adjusts each family's observed maximum over its two
sides. This p-value allocates exploratory expansion and is not a
confirmatory discovery claim. All qualifying families expand; the
unchanged deterministic B winner and C interaction rules apply.

Every evaluated candidate is reported. A candidate qualifies for
validation when it has ≥120 baseline executed trades, ≥6 active calendar
years, positive mean daily baseline net R, positive stress-cost net R,
and positive matched drift/time excess. Nomination and correlation are
annotations. Every qualifier advances, even when duplicate or not a
representative. If none qualify, freeze an empty discovery cohort and
report a negative exploratory search.

## Primary validation test and classification

VALIDATION is 2019-01-02 through 2022-12-30. Evaluate every exact frozen
Q5 specification unchanged. The hypothesis family is all discovery
qualifiers, including correlated and duplicate rules. The primary
one-sided positive-mean test is common-index stationary-bootstrap
Romano-Wolf stepdown of Bartlett-HAC daily net-R t statistics. Include
zero-trade session days. Center each candidate stream at its observed
mean for the boundary null. Use common resampled day indices across all
candidate streams, mean block length 20 sessions, HAC lag 20, alpha 0.05,
500 resamples, seed 515005. If any adjusted p is within ±0.01 of 0.05,
rerun the entire candidate set at 2,000 fresh resamples, seed 517005.
Any adjusted p still within ±0.01 is Monte Carlo unresolved.
Each holdout period begins with its own causal within-period feature
warm-up. Bars from a later partition never train an earlier model; no
warm-up trades are borrowed from a previous performance period.

`SUPPORTED` requires resolved adjusted p ≤0.05, ≥40 executed validation
trades, ≥2 active validation years, positive mean daily baseline net R,
positive stress-cost net R, and positive matched drift/time excess.
`REJECTED` requires the upper one-sided 95% Bartlett-HAC bound on mean
daily net R below zero, or a documented frozen-rule execution failure.
All other results are `INCONCLUSIVE / UNDERPOWERED`, including positive
but multiplicity-unconfirmed performance. Unadjusted one-sided HAC p is
descriptive. A family ensemble or nominee label cannot confer exact-rule
support. Every `SUPPORTED` exact candidate survives; no rank or
correlation deletion applies.

Stationary bootstrap is approximate under nonstationary regimes. Report
validation trade count, active years, baseline/stress expectancy, PF,
net R, drawdown, adjusted/unadjusted p, HAC upper bound, and the exact
classification for every candidate. These remain historical holdout
claims because prior V2/V3/V4 program knowledge exists.

## Scientific cohort, portfolios and audits

Freeze all supported validation survivors as the scientific cohort.
This revision does **not** select or claim a portfolio or prop configuration.
The old draft's portfolio-selection templates are archived planning ideas,
not operative V5 gates. Individual $250/$300/$350/$400 integer MNQ
coverage and cost diagnostics remain required for every evaluated
candidate in each accessible period. The frozen portfolio set is empty;
it cannot remove a scientific survivor. Any later portfolio exercise
must be separately labeled post hoc and cannot alter this cohort.

Before either audit, pin the complete cohort IDs and specifications,
costs, code hashes, classifications, portfolio definitions, and an
evaluation-only blind audit runner. Audit 1 covers 2023-01-03 through
2025-12-31. Audit 2 covers 2026-01-02 through the frozen common usable
NQ/ES endpoint from the registry. The runner evaluates exactly the same
cohort in both periods without search, tuning, ranking, replacement, or
removal. Audit 1 results are sealed before Audit 2 access; the
controlling process receives no audit performance until both result
hashes and candidate sets verify. Reveal both simultaneously. A rule
failing Audit 1 still appears in Audit 2.

Each audit reports baseline/stress net, trade count, daily HAC estimate
and interval, exact-candidate common-day stepdown adjusted p across the
frozen cohort, matched drift/time excess, drawdown, and the four MNQ
budgets. `SUPPORTED` in an audit requires adjusted one-sided p ≤0.05,
positive stress net, positive matched excess, and ≥20 trades;
`REJECTED` requires upper one-sided 95% HAC bound below zero or
non-executability; otherwise `INCONCLUSIVE / UNDERPOWERED`. Audit labels
do not change membership. A dual-audit support statement requires support
in each audit independently; it is not a newly selected cohort.

The audit inference uses the same centered common-day stationary-bootstrap
stepdown, 20-session expected blocks, Bartlett HAC lag 20, and 0.05
one-sided threshold as validation. Each audit starts with 500 resamples:
Audit 1 seed 615005 and Audit 2 seed 715005. If an adjusted p lies within
±0.01 of 0.05, the whole cohort is rerun with 2,000 resamples using seed
617005 or 717005 respectively. Values still within that band are
Monte Carlo unresolved and cannot be labeled `SUPPORTED`.

LIVE_FORWARD stays sealed. No historical period is described as genuinely
prospective; evidence from sessions arriving after the final V5 freeze is
stronger.
