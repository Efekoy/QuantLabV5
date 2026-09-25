# QuantLabV3 bootstrap report (2026-09-22)

**Status: bootstrap complete. V3 discovery has NOT started. QuantLabV2 is unchanged.**

## 1. Project

- Path: `C:\Users\Administrator\Desktop\QuantLabV3`. Package `quantlab3` lives in `core/quantlab3/`.
- **Why the package name changed:** V2 is pip-installed in this Python as `quantlab`. The new name
  means V3 can never import live V2 code.
- **V2 unchanged:** all 7,095 V2 files have the same paths, sizes and modification times before and
  after this task, and the V2 git status is identical.

## 2. What was copied from V2 (engineering only)

All SHA-256 hashes are recorded in `provenance/V2_CODE_PROVENANCE.json`.

**Copied unchanged except for the package rename (45 files):**

| Area | Files |
|---|---|
| Sessions, DST, rolls, data checks | `data/sessions.py`, `data/validation.py` |
| Causal resampling | `data/resample.py` |
| Synthetic test data | `data/synthetic.py` |
| Execution simulator | `engine/backtest.py`, `execution.py`, `managed.py`, `management.py` |
| Costs and metrics | `engine/costs.py`, `metrics.py` |
| Indicators | `features/indicators.py`, `cache.py` |
| Hashing | `freeze/hashing.py` |
| Candidate specs and IDs | `strategies/base.py`, `parameters.py`, `registry.py` |
| Evaluation | `discovery/evaluate.py`, `enumerate.py`, `deduplicate.py` |
| Look-ahead detector | `diagnostics/causality.py` |
| Utilities | `runtime.py` |
| Entry families | the 20 V2 entry families, needed by the engine tests |
| Tests | 8 test files |

The execution simulator covers next-bar fills, stops and targets, breakeven, trailing stops, partial
exits and runners. The candidate spec code produces the deterministic spec IDs. The entry families
are engineering reference only; they are **not** the V3 catalog.

**Copied without change (3 config files):** `costs.yaml`, `sessions.yaml`, `management_smoke.yaml`.

**Adapted (4 files):**
- `config.py`: V3 periods and partitions.
- `data/loader.py`: reads only registered partitions, logs to the ledger, refuses the raw files.
- `data/stage_gate.py`: replaces V2's `split_guard.py`.
- `tests/conftest.py`: builds synthetic V3 partitions.

**New (14 files):** the ledger, freezes, CLI, isolation tests, partition tool, hardening script and
project config.

**Not copied:** survivor lists, the final six, rankings, historical P&L, null-world results,
candidate results, V2 `search_space.yaml` and `management.yaml`, and all V2 reports.

## 3. Data partitions

The raw files were split once by `tools/partition_data.py`. It keeps every column and row unchanged,
inspects only timestamps, and computes no price statistics. Every raw row was placed in exactly one
partition: NQ 5,459,797 rows, ES 5,633,953 rows. The raw files were opened read-only and left unchanged.

Times are New York (the timestamps are bar starts).

| Inst | Partition | First bar | Last bar | Rows | SHA-256 |
|---|---|---|---|---|---|
| NQ | DISCOVERY | 2010-06-07 18:00 | 2018-12-31 16:59 | 2,776,632 | `a1f55ced817c91cf6111f7ac75ffe89113b1d34deddf12e80da9ffaf0c67324e` |
| NQ | CONFIRMATION | 2019-01-01 18:00 | 2022-12-30 16:59 | 1,407,095 | `bf55e231b08eeb0245c95bedbb3a978d314327e4dc2f26aed30b2fad1e42a320` |
| NQ | FINAL_HOLDOUT | 2023-01-02 18:00 | 2025-12-31 16:59 | 1,060,967 | `088e6ff4dae49d7e2ed76c5a6814a1ecc9ee3ef1347130e26fd93b5024c45d87` |
| NQ | SEALED_2026 | 2026-01-01 18:00 | 2026-08-10 19:59 | 215,103 | `c85a4f4d393785af8fb60fb85df461ce0105d24ba7f690eeb9999de4c8ad8343` |
| ES | DISCOVERY | 2010-06-07 18:00 | 2018-12-31 16:59 | 2,945,493 | `a4f4949f91c7179cd050f3493c49296facd76181528fd66128c4322a104ef069` |
| ES | CONFIRMATION | 2019-01-01 18:00 | 2022-12-30 16:59 | 1,407,376 | `fb2f788f2672337b2e820d281238c28c9e2b75625fbb036cc0b78179bce90cef` |
| ES | FINAL_HOLDOUT | 2023-01-02 18:00 | 2025-12-31 16:59 | 1,060,571 | `2e715ed836d8d5effb202c7503f934c33d4b7dce72dc313dd709a230b0b13b65` |
| ES | SEALED_2026 | 2026-01-01 18:00 | 2026-08-14 16:59 | 220,513 | `bd052becc67ce6235a8d27832b91b4eaf59d79caee1cb5f165e396eb04e774e1` |

Notes on the table:
- The partitions keep the raw `volume` column, which V2 never used.
- The NQ file ends four days before the ES file.
- The partition manifest is in `config/partitions.json`, with a copy at `C:\QuantLabV3_Vault\VAULT_MANIFEST.json`.

## 4. Isolation

**Software (active now):**
- The loader accepts no file path and reads only whitelisted `<INST>_<PERIOD>.parquet` files.
- It checks each file's SHA-256 against the manifest before reading, and refuses the raw files by path.
- The stage gate allows only DISCOVERY in the current state.
- The freezes are re-verified before every read.
- Every read, and every refused read, is written to the hash-chained ledger before any data is
  returned. If the ledger can't be written, no data is returned.

**OS (in place now):**
- The vault `C:\QuantLabV3_Vault` is limited to Administrators and SYSTEM; the ordinary Users read
  access it inherited from `C:\` was removed.
- The raw files are in the Administrator profile, which is limited to Administrators and SYSTEM. The
  existing `CodexSandboxUsers` group also has Modify on `Desktop\Quant\data`.
- No other copy of market data was found outside the Administrator profile on C:, the only drive.

**Current classification: ONLY SOFTWARE/PROCEDURAL ISOLATION ACHIEVED.**
- The only OS account today is Administrator, and `check-isolation` confirms it can open every sealed file.
- An Administrator process can always override file permissions, so hard isolation needs research to
  run as a non-admin user.
- Creating that account (and choosing its password) is the one manual step: `tools\harden_isolation.ps1`.
- The script verifies the result **as that user** and prints `HARD DATA ISOLATION ACHIEVED` only if
  Windows denies every sealed file while discovery still loads.

**Residual risks, even with hard isolation:**
- The research user can edit `ledgers/` and `STAGE_STATE.json`. The hash chain makes edits
  detectable but can't prevent them, and the vault stays OS-denied either way.
- The researchers had already seen 2019–2026 in V1/V2. No file permission can undo that.

## 5. Tests

`python -m pytest` in QuantLabV3: **82 passed, 0 failed**.

- **69 inherited V2 correctness tests:** look-ahead 20, management 23, engine timing 9,
  costs/metrics 5, cross-market 3, resample 3, sessions/DST 4, reference 2.
- **13 isolation tests:**
  - discovery can't read confirmation, the holdout or 2026 (3 tests)
  - a window that crosses the discovery boundary is refused
  - the DISCOVERY_FROZEN state still can't read confirmation
  - confirmation can't open before the discovery freeze
  - the holdout can't open before the final-cohort freeze, and 2026 stays sealed during the holdout
  - a frozen spec edited after the holdout opens blocks all reads
  - the raw full-history files are refused
  - an altered partition is refused
  - every read is logged with all the required fields
  - with no ledger, no data is returned
  - an edited ledger breaks the hash chain

All tests use synthetic partitions only.

## 6. Real data accessed during this task

- **V3 research loader:** only DISCOVERY, via `ql3.py smoke` (2 reads, NQ and ES). Highest bar read:
  **2018-12-31 16:59 New York**. The ledger chain verifies OK.
- **Refusals:** the real gate refused CONFIRMATION, FINAL_HOLDOUT and SEALED_2026 (recorded as
  `DATA_READ_REFUSED`).
- **Disclosure:**
  - The one-time partition tool necessarily copied every raw row to create the partitions. It
    inspected only timestamps and printed only the boundaries in the table above.
  - `check-isolation`, run as Administrator, opened the sealed files to test permissions but read 0 bytes.
  - No 2019+ price was read, computed, summarised or printed.

## 7. State

- Stage: **DISCOVERY**.
- Discovery started: **NO**.
- Confirmation, final holdout and 2026 opened by V3 research code: **NO**.

## 8. Next

1. As Administrator, run `tools\harden_isolation.ps1` once (details in the final message).
2. Log on as `qlv3research` (Remote Desktop), install and sign in to Claude Code for that user, and
   open `C:\Users\Administrator\Desktop\QuantLabV3`. Run `python ql3.py check-isolation`; it must say
   `HARD DATA ISOLATION ACHIEVED`.
3. Write the pre-registration (`preregistration/README.md`), then build the V3 catalog in `strategies/`.
