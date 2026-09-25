# QuantLabV3

Research core for the next round of NQ/ES intraday research. It inherits **engineering only** from
QuantLabV2 (copied, not imported; see `provenance/V2_CODE_PROVENANCE.json`) and adds physical data
partitions, a one-way stage gate, a hash-chained access ledger and two immutable freezes.

## Periods (CME sessions, 18:00–17:00 New York, labelled by end date)

| Period | Sessions | Where the data lives |
|---|---|---|
| DISCOVERY | 2010-06-07 .. 2018-12-31 | `data/discovery/` (in the project) |
| CONFIRMATION | 2019-01-01 .. 2022-12-31 | vault `C:\QuantLabV3_Vault` |
| FINAL_HOLDOUT | 2023-01-01 .. 2025-12-31 | vault |
| SEALED_2026 | 2026-01-01 .. latest bar | vault |
| TRUE FORWARD | after the final V3 cohort is frozen | not yet a partition |

## Stage gate

`DISCOVERY -> DISCOVERY_FROZEN -> CONFIRMATION -> FINAL_COHORT_FROZEN -> FINAL_HOLDOUT -> SEALED_2026_AUDIT -> TRUE_FORWARD`

- One step forward at a time. CONFIRMATION needs a verified `freezes/DISCOVERY_FREEZE.json`.
  FINAL_HOLDOUT (and 2026) need a verified `freezes/FINAL_COHORT_FREEZE.json`.
- Both freezes are re-verified before **every** data read, so a frozen spec can't change once a
  later period is open.
- The only way to get bars is `quantlab3.data.loader.load_view(settings, instrument, window)`. It
  accepts no file path, reads only the registered partitions (after checking their SHA-256), refuses
  the original full-history files, and writes a ledger record before it returns any data.

## Isolation layers

1. **OS (hard):** the vault is readable only by Administrators and SYSTEM. Discovery runs as the
   standard user `qlv3research` (created by `tools/harden_isolation.ps1`), which Windows denies access
   to the vault and to the Administrator profile that holds the raw files.
2. **Software:** the stage gate, the partition whitelist and the hash checks.
3. **Evidence:** `ledgers/DATA_ACCESS_LEDGER.jsonl` (append-only, hash-chained) and `ledgers/STAGE_STATE.json`.

## Commands (no install needed)

```
python ql3.py status            # state, readable partitions, ledger summary
python ql3.py smoke             # load DISCOVERY bars (rows/timestamps only)
python ql3.py check-isolation   # can THIS OS user open sealed files? (reads 0 bytes)
python ql3.py verify-ledger
python ql3.py advance DISCOVERY_FROZEN     # etc., one step at a time
python -m pytest                # 69 inherited V2 correctness tests + 13 isolation tests
```

## Layout

`core/quantlab3/` package · `strategies/` V3 catalog (next) · `config/` · `tests/` · `provenance/` ·
`preregistration/` · `freezes/` · `ledgers/` · `results/` · `data/discovery/` · `tools/`

## First V3 campaign (completed 2026-09-22)

Master record: `results/V3_MASTER_RESEARCH_RECORD.md`. Pipeline scripts: `research/s0_verify_engine.py` ...
`research/s10_report.py` (run in order; each stage asserts the stage-gate state). Preregistrations:
`preregistration/V3_*`. Freezes: `freezes/DISCOVERY_FREEZE.json`, `FINAL_COHORT_FREEZE.json`,
`V3_RESEARCH_FREEZE.json`. Gate state: TRUE_FORWARD (starts with session 2026-09-24; not started).
Forward protocol: `forward/FORWARD_PROTOCOL.md`, evaluator `forward/run_forward.py`.
