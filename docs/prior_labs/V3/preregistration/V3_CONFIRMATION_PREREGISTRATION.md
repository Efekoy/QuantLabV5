# V3 CONFIRMATION / NULL / CLUSTER / EVIDENCE / SELECTION PREREGISTRATION

Written 2026-09-22 19:12:19 in stage DISCOVERY_FROZEN -- before any 2019+ bar was opened. JSON twin content_sha256 `3804d9c1d33c608cca1b5b64ee562d0411063f595fa8c357e4f7de926a12db69`.

## confirmation

- **period**: sessions 2019-01-01 .. 2022-12-31 (30 calendar days of discovery data as indicator warm-up; no trade before 2019-01-01)
- **what_runs**: every DISCOVERY_FREEZE candidate (PRIMARY + diagnostics), unchanged, one contract, the same engine, costs and execution assumptions
- **metrics**: trades, gross/moderate/baseline/stress P&L, PF, WR, avg trade, sd, t-stat of the mean net trade, max DD, longest losing streak, avg winner/loser, per-year 2019-2022, long/short split
- **years**: each calendar year reported; a negative year does NOT by itself reject a candidate

## supports

- **management_support**: share of the candidate's entry's Stage-A management variants (discovery universe) that are PRIMARY AND have confirmation BASELINE net > 0
- **parameter_support**: share of the candidate's one-step grid neighbours (discovery universe; same family, instrument, direction, management and non-numeric parameters) that are PRIMARY AND have confirmation BASELINE net > 0; undefined if the candidate has no neighbours
- **structure_file**: {'path': 'results/confirmation_prep/structure.json', 'sha256': '351c15722ef3e4fb21ac7db91f3852945efa9e2334e94e63bdf6f43ca4142619'}

## evidence_tiers

- **STRONG**: n>=50, BASELINE net>0, t>=2.0, STRESS net>0, >=3 of 4 confirmation years positive, management support>=0.5, parameter support>=0.5 (or no grid neighbours), null p<=0.05
- **PROMISING**: not STRONG; n>=30, BASELINE net>0, t>=1.0, >=2 of 4 years positive, management support>=0.25 or parameter support>=0.25, null p<=0.20
- **REJECTED**: n>=30, BASELINE net<=0 and the confirmation mean net trade is significantly below the discovery mean: (mean_conf - mean_disc)/(sd_conf/sqrt(n)) <= -1.645 (rejected with adequate evidence)
- **WEAK**: n>=30, BASELINE net<=0, but not significantly below the discovery estimate (unsupported, underpowered to reject)
- **INCONCLUSIVE**: everything else: n<30 (UNDERPOWERED) or positive but below PROMISING

## null

- **worlds**: 100 = 50 ZERO_DRIFT + 50 DRIFT_PRESERVING (seeds 20260922+i and 20261922+i)
- **generator**: research/v3nulls.py: per-minute random sign flips SHARED by NQ and ES applied to each bar's gap, body and high/low excursions in log space (mirrored bars); prices rebuilt from each contract segment's first real open; DRIFT_PRESERVING adds back the window's mean per-bar log return per instrument. Preserves absolute bar moves (vol level, intraday seasonality, clustering, fat tails, gap sizes), calendar/session/roll structure and the same-minute NQ-ES relation; destroys sign predictability and lead-lag.
- **worlds_built_from**: the same loaded confirmation views (incl. warm-up)
- **what_runs**: every PRIMARY candidate, unchanged, with the same evidence procedure (pre-null tier)
- **candidate_p_value**: statistic = t-stat of the mean BASELINE net trade; p_style = (1 + #worlds with null t >= real t)/(1 + 50) for each style; p_null = max(p_zero, p_drift) (conservative); resolution 1/51
- **global_comparison**: real vs null distribution of: pre-null STRONG count, PROMISING count, positive candidates, stress-positive candidates, behaviours (clusters at 0.50) among pre-null STRONG/PROMISING, STRONG behaviours, eligible behaviours, selected cohort size, and survivor counts per confirmation-trade bucket [(30, 100), (100, 300), (300, 1000), (1000, 1000000000)]; empirical p = (1 + #null >= real)/(1 + worlds), per style and pooled
- **familywise**: descriptive max-t p-value per trade-frequency bucket: share of null worlds whose maximum PRIMARY t-stat in the candidate's bucket reaches the candidate's t

## clustering

- **data**: confirmation daily BASELINE net P&L by entry session (0 on days without a trade)
- **method**: Pearson correlation; average-linkage hierarchical clustering on 1 - rho
- **primary_threshold**: 0.5
- **sensitivity**: [0.3, 0.5, 0.7, 0.9]
- **members**: STRONG and PROMISING PRIMARY candidates
- **reported**: candidate / entry-rule / behaviour counts, cluster sizes, singletons, family, direction, parameter and management composition

## selection

- **eligible_behaviour**: >= 1 STRONG member, or >= 2 PROMISING-or-better members with DISTINCT entry rules
- **representative**: pool = STRONG members if any else all members; keep the fewest confluence conditions; medoid = highest mean daily-P&L correlation to all cluster members; ties -> lowest id
- **order**: STRONG behaviours first, then breadth (distinct entry rules) desc, size desc, representative id
- **correlation_rule**: accept a representative only if its confirmation daily-P&L correlation with every already accepted representative is < 0.50
- **size**: no forced size; an empty cohort is a valid result (then there is no holdout test)
- **never_by**: highest PF / WR / P&L / Sharpe / best 2022 / best-looking equity curve

## holdout

- **period**: 2023-01-01 .. 2025-12-31 (warm-up from 2022); run ONLY after FINAL_COHORT_FREEZE
- **classification**: {'SUPPORTED': 'net > 0, t >= 1.0 and the mean net trade is not significantly below the confirmation mean (z = (mean_h - mean_conf)/(sd_h/sqrt(n)) > -1.645)', 'WEAKER_THAN_EXPECTED': 'net > 0 but t < 1.0 or significantly below the confirmation mean', 'FAILED': 'net <= 0, n >= 20 and significantly below the confirmation mean (z <= -1.645)', 'INCONCLUSIVE': 'net <= 0 but not significantly below expectation, or n < 20'}
- **expectation**: the confirmation mean net trade of the strategy
- **nulls**: 100 null worlds of the holdout period, same generator; per-strategy p (t-stat) and cohort p (combined net)
- **cohort**: equal weight (one contract per strategy); combined net, PF of pooled trades, max DD of daily equity, worst day/week, monthly results, pairwise daily correlations, max simultaneous positions, concentration by family and direction

## 2026
same strategies, same procedure and classification (vs the confirmation expectation), saved separately; called SECONDARY HISTORICAL AUDIT, never true forward

## costs
GROSS / MODERATE / BASELINE (primary) / STRESS from config/costs.yaml, unchanged. No volatility-scaled slippage model is added (declined before holdout).

## hashes
```
{
 "research_code": {
  "v3lib.py": "27fa05b74df51f1cdb00ead6758656ccc449328237a6dfc57fa22b148792c086",
  "v3nulls.py": "47c8bcbda22540f11294c8d3a2b4e7a8673f4d828351afab720a1f47830024c9",
  "v3evidence.py": "1fc0e56b47149d194a30f3fd03b0b6011d784976166b4cad01f97b357616c7e5",
  "v3cluster.py": "dd7561a551c1aa07058c8dfbc67264a8c002f11db631a810ff33633554df1bee",
  "s4_confirmation.py": "5b2d085a15336e70d699a5fd9e7e8234d6999c67b34cb3518b557bcda0459e9e",
  "s5_nulls.py": "f53ddf3675b2aca0fb29134b77f206e1ba3bc723504d01de5e45cad51b2383c8",
  "s6_evidence_select.py": "b570cf9aadca8725e121ca84b7ec9f41d935da4d21c0074d6185a3bba7611a56",
  "s7_holdout.py": "4a550625e853b50d7e2acea07da3afc46182350f4d34609a2d99be6ce1cadf5a"
 },
 "behaviour_code_sha256": "a05d4436e1e81e4e1905ab84aa24570a006bf461abf852b2e12e5c73084927c7",
 "strategy_registry_sha256": "950a256470df4cdfdfeb98625be522f43d4a4b7ca948beae9fb7077a9f60e4c9",
 "config": {
  "research": "f7392ef3e19a82fe071e16ec9ac9552e81270b4bc4b02f4a5618534a0a70caa8",
  "costs": "a27ed5df0c04611fce85e81a2380963f9d63d955a88081a4c12b6e543c98624a",
  "sessions": "fffc52681f6b3e5a2222f073aaaaa73a0ccfecdcc555c7ba7a2907b5447c5460",
  "partitions": "1161208105e16d4d782b2014c5282a9f3b64a5969f867756722323b9f42831a9",
  "search_space": "49243942ec9edf81a346603bf7779e51c0cc0eaf6ba1394f19d65e5dc8478b2d",
  "management": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"
 }
}
```
