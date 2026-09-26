# Prior laboratory coverage and V5 boundaries

The V5 2019–2022 validation and 2023–2026 audits are historical
holdouts of exact frozen V5 candidates, not perfectly researcher-blind
or genuinely prospective tests. The strongest future evidence will be
sessions arriving after the final V5 freeze. The prior-study table is
context, not a candidate-selection or null-method instruction; V5's
current inference protocol is `V5_HOLDOUT_CONFIRMATION_PROTOCOL.md`.

This is a literature map, **not** a source of V5 candidate rankings. V2/V3/V4 reports were available to the researcher, including later historical outcomes. Consequently V5 historical audits are software-sealed but not perfectly researcher-blind. Every V5 mechanism, threshold and portfolio decision must be fixed before V5 validation/audits are read; prior survivors cannot be used to choose among V5 variants.

| Prior work | Coverage relevant to V5 | Design consequence |
|---|---|---|
| V2, ~2.66M specifications | N-bar momentum, price deviation, session-open distance, breakouts, gaps, levels, candle patterns, FVG, simple NQ/ES cross-market, large stop/target/management grid | No repeat of parameter-only variants. New rules need a different *state variable* or conditional mechanism. |
| V3, broad behavior study | Trend/efficiency, variance ratio/autocorrelation, opening drive, day type, simple correlation and trend continuation; staged confirmation/audit | Compare new state models against simple continuation controls and report incremental timing information. |
| V4, 14.08M specifications | 208 features in 14 families including price/path, volume, bar VWAP, jumps, persistence, NQ/ES, technicals, ML; 1,201 discovery passes, 114 behavior groups, 43 validation survivors | Stage A tests mechanism-level additions; do not rebuild the large old grid. Behavior groups annotate redundancy but never delete qualifying candidates. |
| V4 calibration | Small planted volume/persistence effects often missed; edge-free max search t about 3–4 | Estimate V5 power at specific effect sizes and trade frequencies; negative result can mean underpowered. |
| V4 nulls | Sign-flip nulls can erase drift; path-preserving 30-minute blocks retained much more apparent edge | Use paired path-preserving diagnostics and drift/time controls. A path-preserving transform retaining an edge is a stringent comparator, not an edge-free null. |
| V4 fixed risk | $200 MNQ floor skipped many signals when stops widened; post-hoc $250–$400 results were sensitive to risk and drawdown | Track four budgets prospectively and freeze prop selection using 2010–2022 only. Do not choose a budget from V4's later outcomes. |

Sources: `docs/prior_labs/V2/STRATEGY_CATALOG.md`, `docs/prior_labs/V3/results/V3_MASTER_RESEARCH_RECORD.md`, `docs/prior_labs/V4/V4_FEATURE_CATALOG.md`, `docs/prior_labs/V4/V4_MASTER_RESEARCH_RECORD.md`, `docs/prior_labs/V4/V4_NULL_VALIDATION_REPORT.md`, and `docs/prior_labs/V4/V4_POSTHOC_RISK_BUDGET_REPORT.md`.

V5 now has an executable 30-family A/B/C grammar. The current stage is
DISCOVERY, and no V5 strategy search on original DISCOVERY has started.
