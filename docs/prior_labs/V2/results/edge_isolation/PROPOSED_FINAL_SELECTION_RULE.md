# PROPOSED FINAL SELECTION RULE (NOT EXECUTED)

Status: **proposal only.** No strategy has been selected, named or frozen as
FINAL_FORWARD_COHORT. The rule was written using aggregate cluster information only (cluster
evidence classes, sizes, composition, and correlations between cluster-AVERAGE P&L series), before
any individual representative was computed. Executing it requires explicit approval. On approval it
is hashed before it runs.

## 0. Principles

- Select behaviours, not backtests. One representative per genuinely distinct cluster.
- Eligibility comes from the pre-registered null evidence, not from PF, net P&L or win rate.
- Within a cluster, choose the most TYPICAL member (medoid), not the best-looking one.
- Recent performance is reported, never optimised.
- The number that results is whatever the rule gives.

## 1. Cluster eligibility

Use the STRONGER-SUBSET clustering: the pre-registered primary rule applied to the 4,362 candidates
with >= 200 OOS trades AND OOS PF >= 1.3 (`tables/cluster_summary_strong.csv`).

- **Tier 1:** clusters classified CLEARLY ABOVE NULL. There are 3.
- **Tier 2:** clusters classified MIXED. There are 3.
- NULL-LIKE clusters are not eligible, whatever their PF, size or recency.

Why the stronger subset: in the full-survivor clustering no cluster is individually beyond the
null, while the stronger subset contains the only individually null-beating behaviours. Its
thresholds (200 trades, PF 1.3) were fixed in the earlier stage, before the null funnel ran.

## 2. Candidate eligibility (inside an eligible cluster)

1. A member of the cluster (hence >= 200 OOS trades and OOS PF >= 1.3).
2. Discovery entry robustness BROAD_PLATEAU, MODERATE or NARROW. Not CLIFF, not NO_NEIGHBOURS.
3. Management robustness not CLIFF.
4. No other filter. Nothing on PF, net, win rate, drawdown, 2025/2026 results or discovery results.

## 3. Representatives per cluster: exactly one

- Compute each eligible member's average daily-OOS-P&L correlation to all other members of its
  cluster (centrality).
- Take the eligible members within 0.02 of the maximum centrality ("central set").
- From the central set, choose in this order:
  1. the lowest entry complexity (family grid tier 1 < 2 < 3);
  2. simple management (stop/target/time) before BE, trailing, runner, partial;
  3. fewest legs;
  4. the smallest candidate_id (deterministic).
- **Management variants:** only one per cluster, so a cluster never contributes several variants of
  one entry.
- **NQ vs ES:** no quota. If the chosen member's cluster spans both instruments, the instrument is
  whatever the rule picks. NQ and ES versions of one behaviour are one behaviour.
- **Long vs short:** no quota. A short-only behaviour enters only if its cluster is eligible under 1.

## 4. Redundancy cap between representatives

- Process clusters in order: Tier 1 before Tier 2; within a tier, larger clusters first; ties by
  cluster ID.
- **Maximum daily-OOS-P&L correlation between any two final representatives: 0.5** (the same
  threshold that defines a cluster).
- If a cluster's representative exceeds 0.5 with an already-accepted representative, try the next
  member of that cluster's ordering (central set first, then by descending centrality). If no
  member satisfies the cap, the cluster contributes nothing. Its behaviour is already represented.

## 5. Expected size

- At most 6 (3 Tier 1 + 3 Tier 2).
- Correlations between the eligible clusters' AVERAGE daily P&L series: momentum (632) vs mean
  deviation (496) 0.74; the momentum 62-member cluster vs those two 0.68 and 0.59; mean deviation
  (981) vs momentum (632) 0.56. Every other pair is <= 0.37.
- Individual members correlate less than cluster averages, so the cap will not necessarily bind.
  The likely result is **3 to 6 representatives**, most probably 4-5. The exact number is
  whatever the rule produces. It is not tuned.

## 6. Guarding against selection bias

- **Frozen in advance:** the rule is hashed before execution, and the forward evaluation plan
  (section 7) is frozen at the same time.
- **Selection has spent 2021-2026:** those years are now IN-SAMPLE for this cohort. The null
  funnel and cluster evidence are its justification, but its test is only the forward period.
- **The chosen members are not claimed to be best:** medoids are typical members; their individual
  OOS PF may be below their cluster's best. That is intended.
- **Report everything:** the full eligible-cluster list, the members skipped by the cap and why,
  and the cohort's correlation matrix.
- **Researcher disclosure:** the researchers saw 2021-2026 in an older project. Only data after the
  cutoff is clean.
- **No second pass:** the rule is not re-run with other thresholds if the result is disappointing.

## 7. Forward test (to be pre-registered at execution)

- **Start:** the session of **2026-08-17** (opens Sunday 2026-08-16 18:00 New York). It is the
  first session of which no bar has been read for either instrument (ES was read through
  2026-08-14 16:59; NQ through 2026-08-10 19:59, and NQ 2026-08-11..14 is absent from the file
  and never read).
- **Frozen:** specs, costs (BASELINE official; MODERATE and STRESS reported) and execution
  unchanged.
- **Minimum horizon:** declared before starting (e.g. 6 months or 100 trades per strategy,
  whichever is later).
- **Reported:** per strategy and as an equal-weight cohort, never as a summed portfolio of
  overlapping strategies.
- Paper or simulated tracking only. Nothing here is a recommendation to trade.
