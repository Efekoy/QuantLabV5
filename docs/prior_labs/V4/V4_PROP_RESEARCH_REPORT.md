# V4 prop research report (selection data: DISCOVERY + VALIDATION, 2010-2022)

Prop-eligible: **True**. The cohort passed the predictive gates (discovery global null, validation null). Generic research profiles, NOT any firm's rules: $50k account, $3,000 target, $2,000 max loss, EOD or intraday trailing (trail locks at the start balance), $1,000 daily loss (halt day), 50% consistency, 5 minimum days, 120-day evaluation cap. An evaluation starts on EVERY session. Sizing: MNQ micros with fixed-dollar risk (SKIP when one micro exceeds the budget); portfolio open risk capped at 2 x risk. The MNQ commission is an unvalidated placeholder ($1 per round trip + 1 tick slippage per side).

| risk $ | daily policy | trades | net $ | EOD pass | EOD fail | median days to pass | p90 days | INTRADAY pass | INTRADAY fail | funded 60-day survival |
|---|---|---|---|---|---|---|---|---|---|---|
| 100 | none | 4415 | 25,700 | 0.18 | 0.23 | 88.0 | 111.0 | 0.18 | 0.23 | 0.97 |
| 100 | stop_after_daily_loss_300 | 4402 | 26,239 | 0.18 | 0.22 | 88.0 | 111.0 | 0.18 | 0.22 | 0.97 |
| 100 | stop_after_first_winner | 3361 | 233 | 0.03 | 0.26 | 95.0 | 110.5 | 0.03 | 0.26 | 1.0 |
| 100 | stop_after_daily_pm_2R | 4209 | 13,338 | 0.08 | 0.25 | 96.0 | 117.0 | 0.08 | 0.25 | 1.0 |
| 150 | none | 4954 | 53,960 | 0.48 | 0.39 | 64.0 | 99.0 | 0.48 | 0.39 | 0.93 |
| 150 | stop_after_daily_loss_300 | 4833 | 52,608 | 0.47 | 0.41 | 65.0 | 100.0 | 0.47 | 0.41 | 0.88 |
| 150 | stop_after_first_winner | 3724 | 8,132 | 0.18 | 0.41 | 92.0 | 116.0 | 0.18 | 0.41 | 0.84 |
| 150 | stop_after_daily_pm_2R | 4674 | 27,142 | 0.36 | 0.44 | 80.0 | 111.0 | 0.36 | 0.44 | 0.88 |
| 200 | none | 5209 | 83,184 | 0.53 | 0.44 | 42.0 | 79.0 | 0.52 | 0.45 | 0.74 |
| 200 | stop_after_daily_loss_300 | 4964 | 86,343 | 0.54 | 0.44 | 44.0 | 78.0 | 0.53 | 0.44 | 0.78 |
| 200 | stop_after_first_winner | 3889 | 11,739 | 0.35 | 0.50 | 68.0 | 105.0 | 0.35 | 0.50 | 0.64 |
| 200 | stop_after_daily_pm_2R | 4911 | 48,081 | 0.47 | 0.50 | 53.0 | 86.0 | 0.47 | 0.50 | 0.71 |
| 250 | none | 5329 | 105,566 | 0.51 | 0.48 | 33.0 | 64.5 | 0.51 | 0.49 | 0.64 |
| 250 | stop_after_daily_loss_300 | 4989 | 109,813 | 0.54 | 0.45 | 35.0 | 71.0 | 0.53 | 0.47 | 0.61 |
| 250 | stop_after_first_winner | 3975 | 12,780 | 0.37 | 0.58 | 47.0 | 88.0 | 0.37 | 0.58 | 0.56 |
| 250 | stop_after_daily_pm_2R | 5008 | 56,514 | 0.45 | 0.55 | 39.0 | 76.0 | 0.45 | 0.55 | 0.55 |

**Frozen choice (preregistered rule: maximise P(pass) - P(fail) on EOD; ties to the lower risk): risk $200, policy `stop_after_daily_loss_300`.**

Honest reading: even the best configuration passes only about 54% of 120-day evaluations and fails about 44%. This is modest geometry. Evaluation outcomes are close to a coin flip with a slight edge, and time to pass is long (median about 44 sessions). The 'stop after the first winner' policy destroys the edge, consistent with continuation strategies whose profit comes from later trades in a day.
