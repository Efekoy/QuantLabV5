Written by the analyst after the pre-registered analysis ran, from `cluster_summary.csv` and
`tables/`. It changes no classification.

### 1. Redundancy: 11,462 survivors are about 259 behaviours

- **567 entry rules; 259 primary P&L clusters.** Median cluster size is 4. The largest cluster
  holds 1,728 members (97 entry rules, mostly long FVG). 64 singletons.
- **The count depends on how "the same" is defined, but it is stable in order of magnitude:**
  - P&L view: 2,482 clusters at rho 0.9, 731 at 0.7, 259 at 0.5 and 94 at 0.3.
  - Entry-overlap view: 1,527, 635, 460 and 286 at the same four levels.
- **The two views agree at the tight end (ARI 0.67 at 0.9) and diverge at the primary level.**
  78% of entry-overlap pairs are also P&L pairs. Only 16% of P&L pairs share entries, so many
  P&L clusters join DIFFERENT entries that carry the same daily exposure. This is why P&L is the
  primary view: entry rules undercount the redundancy.
- 22 clusters of >= 100 members hold most of the survivors; 93% of all survivors sit in
  clusters of >= 20.

### 2. Real vs null at the level of behaviours

- **The excess is many behaviours, not one giant family.** The real market has more distinct
  surviving behaviours than any null world:
  - 259 clusters vs null median 102 and max 184.
  - Clusters of >= 20 members: 69 vs 12 (max 39).
  - Clusters of >= 100: 22 vs 1 (max 11).
  - High-confidence clusters (>= 10 members, >= 2 entry rules, >= 5 strong members, median
    PF >= 1.2): 38 vs null median 4 and max 21.
  - All at p = 0.005, the smallest attainable with 200 worlds.
- **No single cluster of the full survivor set is individually beyond every null world.** Some
  chance world always produced a cluster as large as each real one (the null world maximum
  reaches 1,781 members). Result: 0 CLEARLY ABOVE NULL, 7 MIXED, 252 NULL-LIKE.
- The 7 MIXED clusters are the large FVG, momentum and mean-deviation clusters (293-1,728
  members). Each passes on size or strong-member count, never on all three dimensions together.
- Per-cluster evidence is much weaker than cohort-level evidence. The funnel's excess is spread
  across dozens of medium and large behaviours, each of which on its own looks like something a
  lucky null world could produce.
- **In the stronger subset** (>= 200 OOS trades AND OOS PF >= 1.3; 4,362 candidates, 138 entry
  rules):
  - 70 clusters vs null median 19 and max 48.
  - 3 clusters are CLEARLY ABOVE NULL. No null world produced a strong cluster this large with
    this many strong members:
    - mean deviation, long, NQ+ES: 981 members, 22 entry rules
    - momentum, NQ: 632 members, 22 entry rules
    - mean deviation, both directions, NQ: 496 members, 9 entry rules
  - 3 are MIXED: cross-market NQ (298 members), momentum NQ (271 members, 2 entry rules) and
    momentum NQ (62 members).
  - The other 64 are NULL-LIKE.
- **Families:**
  - Momentum, mean deviation and cross-market lead on every family-level measure (survivors,
    entry rules, clusters, strong members, high-confidence clusters; p <= 0.02).
  - FVG has many survivors, clusters and entry rules, but almost no strong members (2 vs null
    median 1). Its large cluster is low-PF (median 1.13), high-frequency and long.
  - Gap, overnight range, rolling breakout, price structure, time of day and failed breakout are
    null-like on clusters.
- **High frequency is many independent behaviours, but concentrated:**
  - 2,500+ OOS trades: 23 clusters vs null median 3 (p95 11), but 54% of those survivors sit in
    one cluster.
  - 1,000-2,500 OOS trades: 81 clusters vs 19 (p95 41), 39% in the largest.
  - Higher frequency means thinner per-trade margins: median PF 1.09 at 2,500+ vs 1.43 at
    200-500.
- **Structure:**
  - Real clusters of >= 5 members are more often "entry edge, robust across management types"
    than null clusters (76% vs 64%).
  - They are less often management-dependent (2% vs 6%) or cliff-heavy (cliff share 17% vs 20%).
  - They are slightly more often on broad plateaus (22% vs 19%).
  - The differences are modest. The excess looks like predictive entries rather than payoff
    shaping, but plateau structure does not separate real from null strongly.
- **Short-only** (1,227 candidates, 70 entry rules): 47 clusters vs null median 22.5 (p = 0.045).
  - Entry rules: p = 0.035. Clusters >= 100 members: 4 vs null max 5 (p = 0.015).
  - Two MIXED clusters (mean deviation NQ, 300 members; cross-market NQ, 171 members); no
    CLEARLY.
  - Short-only net is not concentrated in 2022-2024 (46% of the six-period total, vs 46% for all
    survivors). 2025 and 2026 are 24% and 18%.
  - Modest evidence, consistent with the null funnel.
- **Recency:**
  - All members were profitable every year by construction. On per-trade strength, 57 clusters
    are PERSISTENT, 107 RECENTLY STRONG, 23 2022-2024 DOMINATED, 70 INTERMITTENT and 2
    RECENTLY WEAK. Of the 7 MIXED clusters: 4 PERSISTENT, 2 RECENTLY STRONG, 1 INTERMITTENT.
  - Footprint test (all candidates sharing the cluster's entry rules): in 2025 and 2026 the real
    conditional survival is above the null MEDIAN for 6 of the 7 MIXED clusters, but above the
    null p95 for none. Only 3 of all 259 clusters exceed the null p95 in either year.
  - The recent signal is positive but no longer statistically unusual. This matches the null
    funnel: most of the excess was earned in 2022-2024.

### 3. Supported

- The survivors contain many more distinct profitable behaviours than chance produces under the
  null, and the excess is spread across dozens of clusters, not one.
- Within the stronger subset, three behaviours (two mean-deviation, one momentum; NQ-led) are
  individually beyond every null world, and three more are borderline.

### 4. Not supported

- That any MEMBER of those clusters has an edge rather than sharing a cluster that does.
- That the full-survivor clusters are individually unusual: none is CLEARLY ABOVE NULL.
- That FVG's large cluster, short-only or high-frequency survival is strong individual evidence.
- That the effect is still unusual in 2025-2026: positive, but within the null range.
- That these clusters would survive in the future. Only the untouched forward period can test that.
