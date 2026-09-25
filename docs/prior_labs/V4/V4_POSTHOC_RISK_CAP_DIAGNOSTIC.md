# Post hoc risk-cap diagnostic: five frozen V4 strategies

The exact five strategies in `FINAL_COHORT_FREEZE` were rebuilt on the 2023–25 historical holdout and 2026 forward partition. Signals, parameters, stops, exits, MNQ cost model, integer sizing, the `stop_after_daily_loss_300` policy, and generic prop profiles were unchanged. For each finite per-trade cap, simultaneous open risk followed the existing **2 × per-trade budget** formula. This is a sizing diagnostic only; it does not alter the frozen $200 policy, strategy selection, or official conclusions.

**UNCAPPED definition (confirmed for this diagnostic):** size affordable trades using the $400 integer-MNQ floor rule, and use **one MNQ** whenever the one-micro stop risk exceeds $400. There is no per-trade risk ceiling in this case. The existing $400 case's **$800 simultaneous open-risk cap** and daily policy still apply. Thus every valid signal receives a size before portfolio checks, but some are still skipped by the portfolio or daily rules.

“Skipped” below means raw signals minus executed trades; it includes one-micro sizing rejection, simultaneous-risk rejection, and daily-policy rejection. Maximum risk is the tick-rounded stop exposure of an **executed** trade. Drawdown uses the chronological sequence of realized MNQ trade P&L, net of baseline MNQ cost.

## 2023–25 historical holdout: 1,372 signals, 775 sessions

| Per-trade cap | Executed | Skipped total | One-micro skips | Open-risk skips | Daily-policy skips | Net P&L | Max drawdown | Max actual single-trade risk | Generic EOD pass / fail | Generic intraday pass / fail |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| $400 | 1,008 | 364 | 7 | 104 | 253 | $26,939.00 | $9,348.00 | $400.00 | 43.3% / 56.7% | 43.3% / 56.7% |
| $500 | 942 | 430 | 2 | 116 | 312 | $35,386.50 | $11,622.00 | $500.00 | 37.5% / 62.5% | 37.5% / 62.5% |
| $600 | 920 | 452 | 0 | 119 | 333 | $52,016.00 | $12,704.50 | $600.00 | 26.8% / 73.2% | 26.4% / 73.6% |
| $800 | 914 | 458 | 0 | 120 | 338 | $71,296.00 | $17,461.50 | $800.00 | 20.1% / 79.6% | 19.7% / 80.0% |
| UNCAPPED | 1,012 | 360 | 0 | 106 | 254 | $26,716.50 | $9,582.00 | $590.00 | 41.6% / 57.9% | 41.6% / 57.9% |

The $800 EOD and intraday evaluations each have 0.3% incomplete starts; UNCAPPED has 0.5% incomplete starts. The other holdout rows have none. Each prop rate uses 656 heavily overlapping 120-session starts.

## 2026 forward partition: 309 signals, 157 sessions through August 10

| Per-trade cap | Executed | Skipped total | One-micro skips | Open-risk skips | Daily-policy skips | Net P&L | Max drawdown | Max actual single-trade risk | Generic EOD pass / fail | Generic intraday pass / fail |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| $400 | 217 | 92 | 19 | 31 | 42 | $9,300.50 | $2,210.00 | $398.00 | 13.2% / 86.8% | 13.2% / 86.8% |
| $500 | 202 | 107 | 6 | 37 | 64 | $9,867.00 | $3,540.50 | $500.00 | 21.1% / 78.9% | 21.1% / 78.9% |
| $600 | 202 | 107 | 0 | 36 | 71 | $12,446.50 | $4,193.00 | $598.00 | 21.1% / 78.9% | 21.1% / 78.9% |
| $800 | 191 | 118 | 0 | 40 | 78 | $22,788.00 | $5,549.50 | $794.00 | 18.4% / 81.6% | 18.4% / 81.6% |
| UNCAPPED | 217 | 92 | 0 | 39 | 53 | $6,712.00 | $3,863.00 | $576.50 | 13.2% / 86.8% | 13.2% / 86.8% |

All 2026 prop starts had a pass or fail result. Each prop rate uses just 38 heavily overlapping 120-session starts. Larger caps can reduce executed trade count because larger integer-MNQ positions consume more simultaneous-risk capacity and change when the fixed daily policy stops trading.

## The 19 signals skipped specifically by the $400 one-micro check in 2026

These are the 19 raw signals whose tick-rounded **one-MNQ stop risk exceeded $400**. To value their realized outcomes consistently, each is assigned **one MNQ** at the existing baseline MNQ cost, before portfolio and daily-policy filtering. This is a standalone attribution, not the incremental P&L of switching the whole portfolio to another cap.

| Frozen strategy | Signals | Winners | One-MNQ net P&L | Largest one-MNQ stop risk |
|---|---:|---:|---:|---:|
| VWAP `Q4-60857891da97d59c25f0f86c` | 1 | 1 | $198.50 | $480.50 |
| DIST `Q4-9757cb9ee92c11b68d2ad60b` | 10 | 2 | −$2,470.00 | $576.50 |
| RET `Q4-14478681d690cde198df1979` | 4 | 3 | $593.50 | $501.50 |
| RET `Q4-40aae8a2c827fb779e4dd7b9` | 4 | 3 | $521.50 | $500.50 |
| XMKT `Q4-c790712e4f51f6f4268b0033` | 0 | 0 | $0 | — |
| **Combined** | **19** | **9** | **−$1,156.50** | **$576.50** |

Their **win rate was 47.4%** and their **average was −$60.87 per trade**. The 10 DIST signals account for most of the loss. The UNCAPPED portfolio result differs from simply adding −$1,156.50 to the $400 result because admitting these trades also changes open-risk and daily-policy exclusions.

The generic prop profiles are research models, not a firm's actual rules. The MNQ $1 round-trip commission is an unvalidated placeholder. All higher-cap and UNCAPPED numbers are post hoc observations from already seen periods and are not a new live-policy selection.

Full precision and all profile details: `results/posthoc/RISK_CAP_DIAGNOSTIC.json`. Reproduce with `python research/p04_risk_cap_diagnostic.py` in an environment authorized to read the registered partitions.
