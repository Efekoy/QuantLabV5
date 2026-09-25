# V3 TRUE-FORWARD PROTOCOL

- Research freeze: **2026-09-22T23:27:42.806385+00:00** (UTC) = 2026-09-22 19:27:42.806385-04:00 New York.
- **TRUE_FORWARD_START = session 2026-09-24** (the CME session that opens at 18:00 New York the evening before and
  ends on 2026-09-24). first complete CME session (18:00-17:00 New York, labelled by end date) that starts after the research freeze timestamp; if that date is an exchange holiday, the next trading session.
- Status at freeze: **TRUE FORWARD HAS NOT STARTED (no market data after the freeze exists in the lab)**. The latest bars in the lab end {'NQ': '2026-08-10 19:59 NY', 'ES': '2026-08-14 16:59 NY'}.
  All data up to then is historical (2026 data = SECONDARY HISTORICAL AUDIT, never forward).
- Strategies: exactly the 25 members of `freezes/FINAL_COHORT_FREEZE.json`
  (sha256 `f5666dac728aa2539b2f8223309012914d71923ab71f3363e9e035344ace8f03`), evaluated with `forward/run_forward.py`, which verifies the
  freeze and refuses to change anything. No parameter, entry, exit, stop, target, session, cost or
  management rule may change. No member may be removed or added because of forward results.
- Data: new one-minute NQ and ES bars with the same schema as the partitions (ts_event, open, high, low, close,
  symbol). Bars before TRUE_FORWARD_START may only be used as indicator warm-up (up to 30 calendar days);
  a trade counts only if its entry session is >= 2026-09-24.
- Costs: config/costs.yaml unchanged (BASELINE primary; GROSS, MODERATE, STRESS reported).
- Evaluation: per strategy and equal-weight cohort, using the preregistered classification vs the confirmation
  expectation (SUPPORTED / WEAKER_THAN_EXPECTED / FAILED / INCONCLUSIVE); report cumulative results at each
  review; do not stop, restart or re-select the cohort because of interim results.
- Every forward evaluation appends a FORWARD_EVALUATION record to ledgers/DATA_ACCESS_LEDGER.jsonl.
