# CLUSTERING PRE-REGISTRATION -- edge isolation

Written 2026-09-22, after the integrity check and BEFORE any clustering of real or null
survivors was run (no cluster count, size or cluster-level result had been computed). Hashed
in CLUSTERING_PREREGISTRATION.sha256. Not to be edited once results exist.

## Population

- REAL: the official final survivors (profitable in every unseen period: 2021, 2022, 2023,
  2024, 2025 and 2026 up to the cutoff), from `results/main/<year>/results.parquet`.
- NULL: in each of the 200 null worlds, that world's final survivors. Their trades are
  regenerated deterministically from the stored generator version, family and seeds. The
  regeneration must reproduce each world's stored OOS trade counts and net P&L exactly, or the
  analysis stops.
- The SAME rule is applied to the full survivor set, to the stronger subset (cumulative OOS
  trades >= 200 AND cumulative OOS PF >= 1.3), and to the short-only survivors, separately.
  Each is clustered within itself, identically in real and null.

## Behavioural data (OOS only, 2021-01-01 .. cutoff)

- Trades: the stored official trades (real); regenerated trades (null). Baseline net P&L per
  trade = points x point value - baseline round trip (the official definition).
- **Daily P&L vector:** net P&L summed by the trade's session (session labelled by its end date).
  The index is every session with at least one bar of NQ or ES in 2021..2026 (identical calendar
  for real and null). A session without a trade = 0. No normalisation beyond the correlation
  itself.
- **Entry-event set:** (5-minute UTC bucket of the entry bar's start time, direction). A trade at
  09:31 and one at 09:33 in the same direction are the same event; opposite directions never match.

## Similarity views

- **View A -- P&L (PRIMARY):** Pearson correlation of daily P&L vectors; distance d = 1 - rho.
  Spearman, downside (days where either is negative), losing-day and high-volatility-day
  correlations are computed WITHIN clusters for description only; they do not define clusters.
- **View B -- entry behaviour:** Jaccard similarity of entry-event sets, J = |A n B| / |A u B|;
  distance d = 1 - J. Exit-event Jaccard (same construction on exit bars) is reported descriptively.
- The descriptive labels (family, instrument, direction, management, target, stops, frequency,
  PF, WR) are NOT clustering inputs. They are used only to describe clusters.

## Algorithm

- Average-linkage (UPGMA) agglomerative hierarchical clustering on the full pairwise distance
  matrix (`scipy.cluster.hierarchy.linkage(method="average")`). The tree is cut at distance
  1 - tau (`fcluster(criterion="distance")`): every cluster's members are, on average,
  correlated / overlapping at >= tau with the rest of the tree branch that joined them.
- Deterministic. Rows are ordered by candidate_id; the algorithm has no random component (seed
  not needed; numpy seed fixed at 0 anyway). Cluster IDs are renumbered by size (desc), then
  smallest member candidate_id.
- A candidate with a constant daily P&L vector (zero variance; not expected) gets correlation 0
  with everyone and becomes a singleton.
- There are no missing values: every survivor has >= 1 trade; days without trades are 0.
- Singletons are kept as clusters of size 1 (they are real, distinct behaviours; they are NOT
  merged or dropped).

## Thresholds (fixed a priori; standard interpretation of correlation strength)

| level | tau (View A rho, View B Jaccard) | meaning |
|---|---|---|
| VERY TIGHT | 0.9 | near-duplicates |
| TIGHT | 0.7 | strong association |
| **MODERATE (PRIMARY)** | **0.5** | large effect by Cohen's convention (r = 0.5); shared variance >= 25% |
| LOOSE | 0.3 | medium effect (Cohen r = 0.3) |

## PRIMARY specification

**View A (daily OOS P&L Pearson), average linkage, tau = 0.5.**

Why: the question is how many independent pieces of evidence the survivors represent. Two
strategies whose daily P&L correlates at 0.5 or more share at least a quarter of their
variance and will win and lose on largely the same days. Counting them as independent would
overstate the evidence. Average linkage avoids single-linkage chaining (A~B, B~C, but A not
~C) and complete linkage's over-fragmentation. P&L is primary rather than entry overlap
because P&L is what an edge produces: strategies with different entries but the same P&L are
one exposure. View B is the cross-check.

## Sensitivity (reported, not used downstream)

All four levels in both views: number of clusters, median and largest cluster size,
singletons, and the share of strategies in clusters of >= 20 members. Agreement between views
at the primary level: adjusted Rand index, and the share of View-A same-cluster pairs that
are also View-B same-cluster pairs.
