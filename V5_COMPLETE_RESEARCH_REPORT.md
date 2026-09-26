# V5 historical research report

Final pre-DISCOVERY commit/tag: `2281074995c7168f4eb15efe8b725067025b4829` / `v5-prereg`.
Complete pre-DISCOVERY suite: 330 passed, 0 skipped.
Stage inventory actually evaluated: A=60, B=0, C=0; total=60.
DISCOVERY qualifiers: 0; exact candidates tested in VALIDATION: 0.
VALIDATION SUPPORTED=0, INCONCLUSIVE / UNDERPOWERED=0, REJECTED=0.

## Frozen discovery decision

All 30 Stage A family adjusted p-values were 1.0 against the preregistered
60-rule common-day bootstrap reference (500 resamples, 20-session blocks,
Bartlett HAC lag 20). No family met the p≤0.10 expansion gate, so the frozen
Stage B and C rules had no eligible family to expand. Of the 60 Stage A rules,
56 executed at least one trade, 50 reached 120 trades, 52 reached six active
years, 3 had positive baseline net R, 1 had positive stress net R, and 47
had positive matched drift/time excess. None met all five economic/stability
conditions together. These counts are descriptive, with overlap between
conditions; no candidate was promoted by its rank or duplicate status.

The complete specifications, per-candidate outcomes, daily streams,
subperiods, pair similarities, duplicate annotations, and four MNQ budget
diagnostics are frozen in `reports/V5_DISCOVERY_EXECUTABLE.json`. Its hash
is pinned in `V5_DISCOVERY_FREEZE.json` and `freezes/DISCOVERY_FREEZE.json`.

## Complete scientific cohort

Empty: no DISCOVERY candidate qualified for validation. The validation
cohort was frozen empty; no 2019–2022 market data was read or tested.

## Historical audit outcomes

No scientific cohort existed; neither 2023–2025 nor 2026 audit partition
was opened. No audit classification or dual-audit support claim exists.

## Duplicates, deployment and limitations

Exact signal duplicates annotated: 3; behavioral duplicates annotated: 3. No duplicate annotation removed a qualifier.
All three duplicate annotations map `Q5-63e037ce69c3ee395538ee81`,
`Q5-93bdc0b4375af1ba94219d4f`, and
`Q5-dd52031ac8dc461c744d843f` to
`Q5-8405ec22d1bf2da2da62c316`. The 1,344 recorded candidate pairs
include 1,338 finite daily-P&L correlations (range −0.118 to 0.812),
six high-overlap pairs, and zero other behaviorally similar pairs.
Individual integer MNQ coverage at $250/$300/$350/$400 is retained in each period's full JSON. No portfolio or prop configuration was selected in this revised scientific campaign.
Across the 60 exploratory Stage A records, median executed/valid signal
coverage was 0.223 at each of the four budgets. The sum of executed-trade
counts was 249,273 against 1,185,792 summed valid-signal counts at each
budget; these are overlapping strategy diagnostics, not distinct trades
or a portfolio backtest. Contract sizes and candidate-level coverage
remain in the frozen JSON report.
The synthetic/direct-null market program was abandoned after its frozen gates failed; its reports and tags remain intact. Discovery is exploratory. Day-block bootstrap inference is approximate under regime change; costs include unvalidated MNQ commission assumptions. Earlier V2/V3/V4 knowledge contaminates researcher-level historical blinding. The strongest future evidence requires sessions arriving after final V5 freeze.

## Access status

Stage: `VALIDATION_FROZEN`. Main ledger: ok (24 records). Allowed DATA_READ records: 11. LIVE_FORWARD allowed reads: 0. LIVE_FORWARD remains sealed.
