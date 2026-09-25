# V4 LIVE_FORWARD protocol

LIVE_FORWARD means market sessions that **start after the FINAL_COHORT_FREEZE timestamp
`2026-09-25T05:20:01Z`** (freeze body `1708eddcf919a46daef57cf8b01014f8e196f4e39f20acb08842fb2604b7f307`).
Neither the frozen V4 system nor the researchers could have known those outcomes at freeze time.
Historical 2026 data (up to 2026-08-14) is **not** LIVE_FORWARD.

## Procedure (no parameter, strategy, sizing or policy may change)

1. Obtain new NQ and ES continuous-front 1-minute bars in the canonical schema. Use the same Databento
   front-contract rules, cleaning v1 and the same columns.
2. Ingest them. Ingestion is privileged and runs as the administrator.
   ```
   python tools/ingest_live_forward.py NQ <nq_file.parquet>
   python tools/ingest_live_forward.py ES <es_file.parquet>
   ```
   * If any row belongs to a session that started before the freeze, the whole file is refused.
   * Overlapping files are refused.
   * Accepted files are hashed, made read-only and recorded in `C:\QuantLabV4_Vault\TRUE_FORWARD\FORWARD_MANIFEST.jsonl`
     and in the data-access ledger.
   * This mechanism is tested in `tests/test_forward.py`.
3. Evaluate the frozen cohort. The stage is already `TRUE_FORWARD`.
   ```
   python research/s12_live_forward.py
   ```
   This reuses the pinned evaluator `research/s11_frozen_evaluation.py` unchanged, including the frozen
   classification rules, the $200 MNQ prop policy and the generic profiles. Results are written to
   `results/live/EVALUATION.json`.
4. Append the results to `V4_LIVE_FORWARD_STATUS.md` with the date range, trades, net points, t, PF,
   the classifications and the fixed-risk result. Report every member of the cohort.

A live window shorter than the 120-session evaluation cap gives no complete rolling evaluation. The
per-strategy and cohort statistics are still reported.
