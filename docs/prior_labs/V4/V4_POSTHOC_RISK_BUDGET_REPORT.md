# Post hoc MNQ risk-budget sensitivity

The five strategies in `FINAL_COHORT_FREEZE` were rerun with maximum stop risk per trade of **$200, $250, $300, $350, and $400**. Strategy signals, exits, MNQ cost assumptions, the one-micro `SKIP` rule, `stop_after_daily_loss_300`, and the generic prop profiles stayed as recorded in the freeze. At each budget, the simultaneous open-risk cap was the original **2 × budget** rule. This is a post hoc sizing test; the official frozen $200 results and strategy classifications remain the reference.

The $200 reproduction matches the official evaluation in both periods: **$10,761** net on the 2023–25 holdout and **−$2,724.50** net in 2026.

## 2023–25 historical holdout (1,372 raw signals, 775 sessions)

| Risk budget | Skipped: one MNQ too risky | After sizing | Executed after cap and daily policy | Net MNQ P&L | Max trade-sequence DD | Generic EOD eval pass / fail |
|---:|---:|---:|---:|---:|---:|---:|
| $200 | 240 | 1,132 | 1,017 | $10,761 | $6,465 | 45.4% / 49.1% |
| $250 | 108 | 1,264 | 1,113 | $10,607 | $8,490 | 32.3% / 58.8% |
| $300 | 43 | 1,329 | 1,134 | $16,026 | $10,087 | 32.6% / 61.9% |
| $350 | 23 | 1,349 | 1,060 | $17,480 | $8,904 | 33.7% / 64.5% |
| $400 | 7 | 1,365 | 1,008 | $26,939 | $9,348 | 43.3% / 56.7% |

## 2026 forward partition (309 raw signals, 157 sessions through August 10)

| Risk budget | Skipped: one MNQ too risky | After sizing | Executed after cap and daily policy | Net MNQ P&L | Max trade-sequence DD | Generic EOD eval pass / fail / incomplete |
|---:|---:|---:|---:|---:|---:|---:|
| $200 | 183 | 126 | 115 | −$2,725 | $2,725 | 0% / 71.1% / 28.9% |
| $250 | 119 | 190 | 166 | −$2,920 | $3,725 | 0% / 100% / 0% |
| $300 | 77 | 232 | 199 | $363 | $1,805 | 0% / 0% / 100% |
| $350 | 44 | 265 | 208 | $3,121 | $2,068 | 94.7% / 5.3% / 0% |
| $400 | 19 | 290 | 217 | $9,301 | $2,210 | 13.2% / 86.8% / 0% |

**2026 by frozen strategy.** Each cell is `one-micro skips / executed trades / net MNQ P&L` after the portfolio cap and daily policy.

| Strategy | $200 | $250 | $300 | $350 | $400 |
|---|---:|---:|---:|---:|---:|
| VWAP `25f0f86c` | 15 / 32 / −$431 | 8 / 37 / −$1,644 | 3 / 41 / −$1,222 | 2 / 39 / −$634 | 1 / 36 / $558 |
| DIST `8d2ad60b` | 93 / 35 / −$1,381 | 67 / 54 / −$1,569 | 43 / 78 / −$1,372 | 25 / 85 / $64 | 10 / 90 / $2,440 |
| RET `98df1979` | 19 / 27 / −$469 | 9 / 32 / $10 | 8 / 30 / $48 | 6 / 26 / $77 | 4 / 26 / $264 |
| RET `9e4dd7b9` | 50 / 21 / −$444 | 31 / 41 / $448 | 20 / 48 / $2,771 | 10 / 54 / $3,313 | 4 / 59 / $6,068 |
| XMKT `268b0033` | 6 / 0 / $0 | 4 / 2 / −$166 | 3 / 2 / $139 | 1 / 4 / $301 | 0 / 6 / −$28 |

At $200, **183 of 309** 2026 signals could not fit even one MNQ. At $400, that falls to **19**, and the executed portfolio changes from a loss to a $9,301 gain. The `9e4dd7b9` RET strategy supplies $6,068 of that $400 result. More admitted signals do not necessarily mean more executed trades: higher sizing causes more skips under the 2 × budget portfolio cap and the fixed daily loss policy.

The $350 EOD pass figure is **36 of 38** rolling 120-session starts. Those starts overlap heavily and are not 38 independent trials. The sharp fall to **5 of 38** at $400 reflects the modeled account path and drawdown constraints despite higher total P&L. Neither figure is a reliable pass probability for a new account. MNQ commission remains the unvalidated $1 round-trip placeholder in `config/costs.yaml`; the generic evaluation profiles are not any firm's rules. The sensitivity uses already observed 2023–26 data, so selecting a new live budget from its best row would be post hoc tuning.

Full precision, profile details, and per-strategy results: `results/posthoc/RISK_BUDGET_SENSITIVITY.json`. Reproduce with `python research/p03_risk_budget_sensitivity.py` in an environment authorized to read the registered partitions.
