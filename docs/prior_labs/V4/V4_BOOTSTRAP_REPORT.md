# QuantLabV4 bootstrap report

Infrastructure only. No strategy research was run, no strategy performance was computed, and
no price or volume statistics from any period were inspected. The only exception is the
structural DISCOVERY volume checks listed below, which are counts only.

## Project

* Absolute path: `C:\Users\Administrator\Desktop\QuantLabV4`
* Sealed vault: `C:\QuantLabV4_Vault` (outside the project tree)
* Current research stage: **DISCOVERY** (`ledgers/STAGE_STATE.json`, cross-checked against the ledger)
* Code commit pinned by the bootstrap freeze: `1ad8049765f7fd2607af264ac955643517969a40`
* Bootstrap freeze: `freezes/V4_BOOTSTRAP_FREEZE.json`, body SHA-256
  `b10f8c7f0476f2ccf1dd574855ead09673acc66470db161f117d9dc0ca8d79fa`. It covers 111 tracked files,
  and a reproduction check re-verified every hash.
* Git tag: `v4-bootstrap`. It points at the commit that adds this report and the freeze on top of
  the pinned code commit.
* Superseded: `freezes/V4_BOOTSTRAP_FREEZE_R1_SUPERSEDED.json` (body `e6327288...`). It was written
  while one over-broad static test was failing. It is kept unchanged for the record, and the bug
  is logged in `ledgers/RESEARCH_DECISION_LOG.jsonl`.

## Source data (read-only, never modified)

| Instrument | Path | Bytes | SHA-256 | Rows | Coverage (UTC) | Sessions |
|---|---|---|---|---|---|---|
| NQ | `C:\Users\Administrator\Desktop\Quant\data\NQ\nq_continuous_front_1m.parquet` | 84,200,073 | `63b8f16dd1da0a35f2fdfdc9039686ffc8db0ada84333bfc7cd85f8f28d013e7` | 5,459,797 | 2010-06-07 22:00 .. 2026-08-10 23:59 | 2010-06-08 .. 2026-08-11 (final session **incomplete**) |
| ES | `C:\Users\Administrator\Desktop\Quant\data\ES\es_continuous_front_1m.parquet` | 78,272,794 | `4a5dcac73b45f8097164e1242447fb490e6b2d52b4012cbe1ee3890f2d76edb2` | 5,633,953 | 2010-06-07 22:00 .. 2026-08-14 20:59 | 2010-06-08 .. 2026-08-14 (complete) |

The hashes match the provenance recorded by the Quant project (`Quant/data/*/meta`).

Schema (identical Arrow schema for NQ and ES):
`ts_event timestamp[ns, UTC]`, `rtype int16`, `publisher_id int16`, `instrument_id int64`,
`open/high/low/close double`, **`volume int64`**, `symbol string`, `roll_session string`,
`roll_boundary bool`, `duplicate_timestamp bool`, `source_duplicate_count int32`.
Continuous front contract, unadjusted prices. The roll rule is the highest previous-session volume.

## Partitions

Sessions run 18:00-17:00 New York and are labelled by end date. Over all 11.09M source rows the
rule gives **0** disagreements with the source `roll_session` column.

| Inst | Partition | Data sessions | Sessions | Rows | SHA-256 | Physical location |
|---|---|---|---|---|---|---|
| NQ | DISCOVERY (def. 2010-06-01..2018-12-31) | 2010-06-08 .. 2018-12-31 | 2198 | 2,776,632 | `fe96495715c37d1fea42c228e0cf9c13f4b5df12682d3ac611701695faa6baa9` | project `data\discovery\NQ_DISCOVERY.parquet` |
| NQ | CONFIRMATION (2019-01-01..2022-12-31) | 2019-01-02 .. 2022-12-30 | 1034 | 1,407,095 | `da3c6f5e7da762787cf6ba2166a92e374758f7e8881e7ad6606426ab04ead421` | vault `CONFIRMATION\` |
| NQ | FINAL_HISTORICAL_HOLDOUT (2023-01-01..2025-12-31) | 2023-01-03 .. 2025-12-31 | 775 | 1,060,967 | `596a0f68e0738f5e6f7044e07d295010c723b1e440a9d214217cd7bc6d09c890` | vault `FINAL_HISTORICAL_HOLDOUT\` |
| NQ | SEALED_2026_AUDIT (2026-01-01..last complete) | 2026-01-02 .. **2026-08-10** | 157 | 214,983 | `95e65133d0f196eacf1f91c7626f0295d79cd9d7dda8dd9b63632ad64c9e1c5c` | vault `SEALED_2026_AUDIT\` |
| ES | DISCOVERY | 2010-06-08 .. 2018-12-31 | 2198 | 2,945,493 | `25b0c9f27dc2b662b1be736eeb8b811d757d0fcb9700290627a1e6f81f9a88f2` | project `data\discovery\ES_DISCOVERY.parquet` |
| ES | CONFIRMATION | 2019-01-02 .. 2022-12-30 | 1034 | 1,407,376 | `f48df4e60adb5e62af9a7bd69e52f5037a9be79853e164c8121868eae8ea06e5` | vault |
| ES | FINAL_HISTORICAL_HOLDOUT | 2023-01-03 .. 2025-12-31 | 775 | 1,060,571 | `45ea6cbc913f41737ea18b32ecd309acdd47e12e27b54555ba5d8008cca926f1` | vault |
| ES | SEALED_2026_AUDIT | 2026-01-02 .. **2026-08-14** | 161 | 220,513 | `bd052becc67ce6235a8d27832b91b4eaf59d79caee1cb5f165e396eb04e774e1` | vault |

* TRUE_FORWARD holds no historical data. The inbox and accepted folders exist in the vault, and
  ingestion is refused until a FINAL_COHORT_FREEZE is pinned.
* Every source row was placed in exactly one partition, except **120 NQ rows of the incomplete
  final session 2026-08-11**, which were excluded. The joint (NQ and ES) last complete session is 2026-08-10.
* The registry hash is pinned in the stage state: `acf93cf1e7bb8c9c87f148f39d1cd1e30fb8562cb5614ade23f5a9116345a02d`.

## Isolation

* Software isolation: **ACTIVE**. Every read goes through `load_view`, which re-verifies the stage,
  the ledger chain, the registry pin, the freezes and the partition hash, and ledgers every
  attempt before returning data.
* Physical placement: **ACTIVE**. The sealed partitions are outside the project, and the vault
  ACL allows Administrators and SYSTEM only.
* **OS isolation: NOT ACTIVE.** Research runs as `Administrator`, and
  `tools/check_isolation.py` confirms that every vault and raw file is openable by this
  account (`results/ISOLATION_CHECK_Administrator.json`). `tools/harden_isolation.ps1` has been
  prepared but not run, because it creates an account with a password you choose.
  See `docs/OS_ISOLATION.md`.
* Pre-existing condition, not changed: `Desktop\Quant\data` (the raw files) grants Modify to
  `CodexSandboxUsers` and to an unresolved SID.
* Data-access ledger: 13 records at freeze time. The only allowed research reads are of the
  DISCOVERY partition, and no non-DISCOVERY partition was read through the research API.

## Tests

**180 tests, 180 passed, 0 failed** (`provenance/TEST_RESULTS.xml`, `provenance/TEST_ENVIRONMENT.json`).
Per module: candidates 11, costs/metrics 8, engine on synthetic markets 11, engine timing 8,
feature causality 9, fixed-dollar 14, forward 4, ledger 11, load_view isolation 26, manifests 3,
no direct data access 3, nulls and pipeline 11, prop account 14, resample 8, research log 2,
schema/volume/rolls 10, sessions/DST 7, stage gate 12, validation splits 8.
All tests use synthetic data or throw-away synthetic projects.

## Volume confirmation (DISCOVERY only, counts)

| | NQ | ES |
|---|---|---|
| column present, dtype | yes, int64 | yes, int64 |
| unparseable / negative / non-integral | 0 / 0 / 0 | 0 / 0 / 0 |
| missing | 0 | 0 |
| zero-volume rows | 0 | 0 |
| symbol-derived rolls = `roll_boundary` flags | 35 = 35, all at session starts | 35 = 35, all at session starts |
| duplicate-timestamp flags | 0 | 0 |

NQ and ES loaded schemas are identical (after the fix below).

## Data-quality and engineering problems encountered

1. The NQ source file embeds pandas metadata that makes `roll_boundary` load as nullable
   `boolean`, while ES loads as `bool`. **Fixed**: load_view now takes dtypes from the Arrow schema only.
   There is a regression test.
2. **A bug inherited from V3**: the synthetic generator placed Sunday 18:00 session starts at
   17:00 on DST-ending days. The V4 partitioner caught it on synthetic data. Fixed, with a regression test.
3. The Windows ledger lock raced between writers: `PermissionError` while a lock file was pending
   deletion. **Fixed**, and stress-tested at 0 failures in 40 runs × 6 writers.
4. Arrow reports float64 as `double`, so the schema checker would have rejected the real files.
   Caught on synthetic data before the real run.
5. NQ source ends mid-session, 2026-08-11. That session was excluded.
6. There are no zero-volume rows. Minutes with no trades are therefore likely **absent** rather
   than zero-volume, which the full DISCOVERY audit will check.

## Inherited from V3 / not inherited

See `docs/INHERITED_FROM_V3.md` and `provenance/V3_COPIED_FILES(_FINAL).json`. 20 files were copied
from V3 HEAD `cee42fe`, and all 20 were adapted. Costs were inherited unchanged:
NQ $4 + 1 tick/side → $14 per round trip; ES $29 per round trip. Execution semantics were inherited.
Nothing from V3's strategy catalog, management library, results, cohorts, freezes or ledgers was used.

## Deviations from the bootstrap specification

* Stage names are kept as implemented: the VALIDATION period is the `CONFIRMATION` partition/stage,
  SEALED_2026_FORWARD is `SEALED_2026_AUDIT`/`AUDIT_2026`, and LIVE_FORWARD is `TRUE_FORWARD`.
  The mapping is in `V4_REPORT_INDEX.md`.
* Added a precondition: `AUDIT_2026` requires a frozen holdout report (`HOLDOUT_REPORT_FREEZE`).
* The V3 multi-leg management kernel was not ported (it is coupled to V3's template library).
* Freeze R1 was superseded (see above).

## Remaining before strategy research

Full DISCOVERY data audit, feature catalog, strategy grammar and preregistration freeze.
OS isolation stays inactive, as a documented limitation. See `docs/REMAINING_WORK.md`.
