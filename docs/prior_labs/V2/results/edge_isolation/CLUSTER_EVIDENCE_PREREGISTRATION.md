# CLUSTER-LEVEL EVIDENCE PRE-REGISTRATION -- edge isolation

Written 2026-09-22 together with CLUSTERING_PREREGISTRATION.md, BEFORE any real or null
cluster had been computed. Hashed in CLUSTER_EVIDENCE_PREREGISTRATION.sha256. No composite
score. W = 200 null worlds.

## Per-cluster quantities (identical for real and null clusters)

- s = members; e = distinct entry rules (entry_key); k = STRONG members (cumulative OOS trades
  >= 200 AND cumulative OOS PF >= 1.3).
- Median member cumulative OOS trades, median OOS PF, median OOS WR.
- Family / instrument / direction / management composition; robustness composition
  (BROAD_PLATEAU / MODERATE / NARROW / CLIFF / NO_NEIGHBOURS); entry-edge class composition.

## The null reference for one real cluster (world-level, family-wise)

Clusters have no one-to-one identity across worlds, so a real cluster is compared with the
BEST cluster any single null world produced (this also handles the fact that many real
clusters are examined):

- M_s(w), M_e(w), M_k(w) = the largest s, e and k of any cluster in null world w.
- p_size = (1 + #{w : M_s(w) >= s}) / (1 + W); likewise p_entries (e) and p_strong (k).

## Evidence classification of a real cluster (dimensions A, B and C/D combined)

- **CLEARLY ABOVE NULL:** p_size <= 0.01 AND (p_entries <= 0.01 OR p_strong <= 0.01).
  No single chance world produced a cluster this large AND this diverse or this rich in strong
  members.
- **MIXED:** not CLEARLY, but at least one of p_size, p_entries, p_strong <= 0.05.
- **NULL-LIKE:** none of the three <= 0.05. Chance worlds routinely produce such clusters,
  including every small cluster and singleton.

## Descriptive dimensions (reported per cluster, never used to classify)

- **D. OOS PF:** the real cluster's median OOS PF, as a percentile among null clusters of the
  same size band (1, 2-4, 5-19, 20-99, 100-499, 500+).
- **C. OOS sample:** median OOS trades, also as a percentile within the size band.
- **E. Null recurrence of the same strategies (identity-based):** the cluster's FOOTPRINT = all
  frozen candidates sharing its entry rules (any management). For each year y, the real
  conditional survival rate of the footprint (survivors / entrants that year) is compared with
  the same footprint's rate in each null world. Reported: null median and p95 per year, and
  whether real > null p95.
- **F. Year consistency and recency:** per year, the median member net P&L per trade (a_y).
  Classes, assigned in this order:
  - PERSISTENT: min_y a_y >= 0.5 x median_y a_y
  - 2022-2024 DOMINATED: mean(a_2022..a_2024) > 2 x mean(a_2021, a_2025, a_2026)
  - RECENTLY WEAK: mean(a_2025, a_2026) < 0.5 x mean(a_2021..a_2024)
  - RECENTLY STRONG: mean(a_2025, a_2026) > 1.5 x mean(a_2021..a_2024)
  - otherwise INTERMITTENT

  Every member is profitable in every year by construction, so these classes describe strength,
  not survival. The footprint survival in 2025 and 2026 vs null (E) is the "signs of life" test.
- **Plateau and management structure:** member composition, compared with null clusters of the
  same size band.

## Aggregate comparisons (upper-tail p = (1 + #worlds >= real) / (1 + W))

- Number of primary clusters; clusters of size >= 5, >= 20 and >= 100; singletons (reported,
  not tested one-sided).
- **HIGH-CONFIDENCE clusters** (defined without reference to the null): s >= 10 AND e >= 2 AND
  k >= 5 AND median OOS PF >= 1.2. Real count vs null distribution.
- Counts of CLEARLY ABOVE NULL / MIXED / NULL-LIKE clusters by majority family, instrument and
  direction. By construction a null world has no cluster beyond its own maximum, so these counts
  are reported for the real funnel only.
- The same framework applied separately to the stronger subset and the short-only survivors,
  each clustered within itself, with null references from the same subset of every null world.
- Family level: survivors, entry rules, primary clusters (by majority family), strong members and
  high-confidence clusters, real vs the null distribution.
- High-frequency buckets (cumulative OOS trades 200-500, 500-1,000, 1,000-2,500, 2,500+):
  survivors, entry rules, clusters touched, PF/WR distribution, management style; real vs null
  counts.

## What this is not

A descriptive, empirical comparison with the chosen surrogate processes. It does not prove any
cluster has an edge, and nothing here selects or recommends a strategy.
