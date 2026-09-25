# Remaining work before strategy research begins

Ordered roughly by when it is needed.

1. **OS isolation.** Run `tools/harden_isolation.ps1` and do all research as `qlv4research`
   (docs/OS_ISOLATION.md). Optionally review the pre-existing CodexSandboxUsers Modify grant on
   `Desktop\Quant\data`.
2. **DISCOVERY volume audit** (the next planned step): time-of-day normalisation, roll-day
   effects, outliers, early-year (2010-2012) coverage, and missing minutes vs zero-volume.
   The structural audit found no zero-volume rows, so minutes with no trades are probably absent
   rows rather than zero-volume rows. The audit should confirm this. DISCOVERY only.
3. **Missing-minute / gap policy.** Decide how features treat absent minutes. Candidates are
   no fill (current behaviour) and explicit gap flags. The source README reports thin early-ES
   coverage.
4. **Cost model realism.** The V3 baseline ($4 + 1 tick/side) is one fixed friction model. Decide
   whether to vary costs by era (2010 vs 2026 spreads and commissions) and by session (RTH vs
   overnight). Validate the MNQ/MES commission placeholders before any micro-contract result is used.
5. **V4 feature library** on the `features.base.Feature` interface. Every feature must pass
   `assert_causal` and declare its lookback, warmup, session reset and instrument requirements.
6. **V4 strategy grammar and pre-registration.** Write `config/search.yaml: grammar`, the
   screening thresholds, the multiple-testing plan, the null-world counts and generators, and
   the robustness criteria before any DISCOVERY P&L is computed.
7. **Generator scalability.** Ordinals are computed by a full pass over the index order. At
   ~10^7+ specs, precompute validity masks or count valid specs per shard.
8. **Multi-leg trade management** (breakeven, trailing, partials). Port generic parts of V3's
   managed kernel after review, or write new code. The single-position kernel is ready now.
9. **Null calibration.** Choose the null generators and block lengths per hypothesis family,
   and check on DISCOVERY that the nulls keep volatility clustering and the time-of-day profile.
10. **Prop profiles.** Replace the illustrative GENERIC_* profiles with real rules for the target
    firms, taken from their published documents.
11. **Ledger hardening.** Consider an append-only ledger service, or mirror ledger anchors into
    the vault at each freeze.
