# NULL FUNNEL -- pre-registered comparison and classification rule

Written 2026-09-22 while the first null worlds were starting, BEFORE any null
world result had been seen. Hashed in CLASSIFICATION_RULE.sha256. Not to be
edited after results exist.

## Key metrics (real value verified from official files)

1. FINAL: final survivor count (passed 2021..2026).
2. ENTRIES: distinct entry rules (entry_key) among final survivors.
3. SHORT: short-only final survivors.
4. STRONG: final survivors with cumulative OOS trades >= 200 AND cumulative OOS PF >= 1.3.
5. STRONG_ENTRIES: distinct entry rules among STRONG.

Secondary (reported, not used for the classification): per-year survivor counts,
NQ/ES/long/short/both survivors, short-only median OOS PF, short-only entry
rules, NQ share, long share of OOS net P&L, final-survivor PF / WR / trades /
net / DD distributions, category survival.

## Empirical p-value

p = (1 + #null worlds with metric >= real) / (1 + #null worlds). Upper tail.
Computed for: all 200 worlds pooled; the ZERO-drift group (A0 + B0_blk5 + B0_blk30,
100 worlds); the DRIFT-preserving group (A1 + B1_blk5 + B1_blk30, 100 worlds);
and each of the six families separately (descriptive).

## Classification (uses the ZERO and DRIFT groups: 5 metrics x 2 groups = 10 p-values)

- STRONGLY ABOVE NULL: all 10 p-values <= 0.01 (the real value exceeds every
  null world in both groups for every key metric).
- ABOVE NULL, MODESTLY: all 10 p-values <= 0.10, but not STRONGLY.
- NULL-LIKE: at most 2 of the 10 p-values <= 0.05.
- MIXED: anything else. The report must say which metrics beat which null and why.

## Family / category comparisons

Categories are those already used by the official reporting system
(reporting/final_report.py BREAKDOWNS + target/WR/frequency buckets and
management style). For each category: real final survivors vs null distribution
(median, p95, p-value). Multiplicity across categories of one dimension is
handled with a max-statistic reference: for every null world and dimension,
z_c = (count_c - mean_c) / sd_c over null worlds (sd floored at 0.5), and the
world's max_c z_c is recorded; the family-wise adjusted p of a real category
is (1 + #worlds with max z >= real z_c) / (1 + #worlds).

## What this is not

An empirical comparison with the chosen surrogate processes, not a proof. It is
not a recommendation to trade.
