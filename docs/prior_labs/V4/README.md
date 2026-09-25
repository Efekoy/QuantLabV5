# QuantLabV4

Research infrastructure for a large, deterministic search over NQ/ES 1-minute OHLCV futures
data (2010-2026), with sealed later periods, a one-way research stage machine, and a
hash-chained record of every data access.

**Status: bootstrap complete, stage `DISCOVERY`. No strategy research has been run.**
See `V4_BOOTSTRAP_REPORT.md`.

## Rules that the code enforces

1. Research code gets market data **only** through `quantlab4.isolation.load_view` (or
   `load_bars`). It takes a *logical* request (instrument, partition, start, end, columns),
   never a path. A test scans the source tree for direct parquet/CSV access.
2. Every read attempt, allowed or refused, goes into `ledgers/DATA_ACCESS_LEDGER.jsonl`.
   The ledger is hash-chained, and allowed data is only returned after its record is written.
3. The stage (`ledgers/STAGE_STATE.json`) only moves forward, one step at a time, after its
   preconditions verify. It is cross-checked against the ledger on every read.
4. Partition files are SHA-256-verified on every read. The partition registry is pinned when
   DISCOVERY opens, and each freeze is pinned when its stage opens.
5. Real data and null worlds go through one evaluator (`quantlab4.search.pipeline`).

## Data partitions (CME sessions, 18:00-17:00 New York, labelled by end date)

| Partition | Sessions | Location | Readable from stage |
|---|---|---|---|
| DISCOVERY | 2010-06-01 .. 2018-12-31 | `data/discovery/` (project) | DISCOVERY |
| CONFIRMATION | 2019-01-01 .. 2022-12-31 | `C:\QuantLabV4_Vault\CONFIRMATION` | CONFIRMATION |
| FINAL_HISTORICAL_HOLDOUT | 2023-01-01 .. 2025-12-31 | vault | HISTORICAL_HOLDOUT |
| SEALED_2026_AUDIT | 2026-01-01 .. last complete session at bootstrap | vault | AUDIT_2026 |
| TRUE_FORWARD | sessions starting after FINAL_COHORT_FREEZE | vault (`TRUE_FORWARD/`) | TRUE_FORWARD |

SEALED_2026_AUDIT is **not** forward evidence, because earlier projects already looked at 2026.

## Stages

`BOOTSTRAP -> DISCOVERY -> DISCOVERY_FROZEN -> CONFIRMATION -> CONFIRMATION_FROZEN ->
FINAL_COHORT_FROZEN -> HISTORICAL_HOLDOUT -> AUDIT_2026 -> TRUE_FORWARD` (config/stage_policy.yaml)

## Layout

```
config/        partitions.json (definitions + registry), costs, sessions, stage policy, search,
               nulls, prop profiles, execution policy, paths
quantlab4/
  isolation/   load_view, stage_gate, ledger, manifests, freezes, forward (TRUE_FORWARD inbox)
  bootstrap/   partitioner (privileged, one-time)
  data/        schema (volume first-class), sessions/DST, rolls, resample, align, volume_qc
  features/    causal feature interface + trivial proof features
  engine/      next-bar-fill kernel, execution windows, costs, metrics
  search/      content-derived candidate IDs, generic grammar, deterministic generator,
               THE evaluation pipeline, screening/clustering/robustness skeletons
  nulls/       null generators (block sign-flip, session permutation) + runner
  validation/  purging, embargo, chronological DISCOVERY sub-periods (walk-forward, CSCV)
  risk/        fixed-dollar and fixed-contract sizing
  prop/        generic prop-evaluation account simulator
  diagnostics/ lookahead detector (future-rewrite test)
  synthetic/   synthetic markets with known properties (tests only)
research/      s00_bootstrap (privileged), s01_discovery_data_audit, s02_bootstrap_freeze
tools/         copy_v3_engine, write_provenance, check_isolation, harden_isolation.ps1
tests/         software-correctness suite (synthetic data only)
provenance/    source data, V3 copies, environment, config hashes, test results
ledgers/       DATA_ACCESS_LEDGER.jsonl, STAGE_STATE.json
freezes/       V4_BOOTSTRAP_FREEZE.json (+ later stage freezes)
docs/          architecture, V3 inheritance, OS isolation, remaining work
```

## Usage

```bash
python -m pytest                              # full test suite (synthetic data only)
python research/s01_discovery_data_audit.py   # structural DISCOVERY checks (counts only)
python tools/check_isolation.py               # is OS isolation active for this account?
```

```python
from quantlab4.isolation.load_view import load_view, load_bars
md = load_view("NQ", "DISCOVERY", "2012-01-01", "2012-12-31", ["open", "high", "low", "close", "volume", "symbol"])
bars = md.bars()     # read-only arrays; every read is ledgered
```

OS-level isolation is **not active** until `tools/harden_isolation.ps1` has been run by an
administrator and research is run as the non-admin account it creates (docs/OS_ISOLATION.md).
