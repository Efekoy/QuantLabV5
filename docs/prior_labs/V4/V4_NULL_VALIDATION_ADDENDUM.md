# Addendum to V4_NULL_VALIDATION_REPORT.md: power diagnostics (synthetic data only)

This was run after the preregistration freeze, which is why it is a separate file. It changes nothing
that was frozen. The same machinery was run on the two plants that were not convincingly detected at
1× strength, this time at **2× strength**, each against 4 of its own Null-A worlds.

| plant | world T_G | own A-nulls T_G | detected |
|---|---|---|---|
| volume-conditioned 2× (drift 0.10 sd/bar for 30 bars after a volume spike) | **9.34** (788 passing) | 3.84, 3.10, 3.22, 3.32 | yes, clearly |
| persistence 2× (AR(1) φ = 0.5 in 60-bar regimes) | **4.16** (107 passing) | 3.18, 3.27, 3.13, 3.22 | yes, weakly (just above the zero-world range) |

Conclusion: the 1× misses are a **power limit, not a machinery bug**. The search, the outcome tables and
the nulls respond correctly once the effect is large enough. V4 detects effects of this kind only once
they are about twice the 1× planted size.
