# QuantLabV5

The successor to QuantLabV4. It reuses V4's proven infrastructure (engine, sessions/DST/rolls, resampling,
features, search kernels, nulls, purging/embargo, sizing, prop simulator, isolation, ledger, resume)
unchanged in behaviour, over the same verified NQ/ES 1-minute data, with new partitions, a new vault and a
new stage machine.

**Status: stage `DISCOVERY`, with real research access held by the preregistration guard. All 30 Stage A market-signal families and the adaptive A/B/C search runner execute on synthetic markets. Full market-level planted-edge and all-null calibration, independent validation machinery, and blind historical-audit architecture remain incomplete. No real V5 strategy search has run. The review hash pin is `REVIEW_REQUIRED` and does not authorize discovery.**

Design documents: `V5_PRIOR_LAB_COVERAGE.md`, `V5_STRATEGY_CATALOG.md`, `V5_POWER_CALIBRATION_REPORT.md`, `V5_NULL_METHOD_REPORT.md`, `V5_RESEARCH_PREREGISTRATION.md`, `V5_EXECUTABLE_PIPELINE_STATUS.md`, and `V5_PREREGISTRATION_FREEZE.json`.
See `V5_BOOTSTRAP_REPORT.md`.

## Rules that the code enforces

1. Research code gets market data **only** through `quantlab5.isolation.load_view` / `load_bars` /
   `data.market.load_market`. These take a *logical* request, never a path. A static test forbids direct
   parquet/CSV access and forbids naming any vault, earlier lab's data store, or `docs/prior_labs`.
2. Every read attempt, allowed or refused, is written to `ledgers/DATA_ACCESS_LEDGER.jsonl`, which is
   hash-chained. Data is returned only after its record has been written.
3. The stage (`ledgers/STAGE_STATE.json`) only moves forward, one step at a time, after its preconditions
   verify. It is cross-checked against the ledger on every read.
4. Partition files are SHA-256-verified on every read. The registry is pinned at DISCOVERY, and each freeze
   is pinned when its stage opens.
5. **No arbitrary candidate limit.** Every qualifying discovery candidate advances. Validation evaluates all
   of them. The final cohort is exactly the set of validation survivors. Behavioural duplicates are only
   annotated. The stage gate enforces all of this on the freeze contents.

## Partitions (CME sessions 18:00-17:00 New York, labelled by end date)

| Partition | Sessions | Location | First readable at |
|---|---|---|---|
| DISCOVERY | 2010-06-08 .. 2018-12-31 | `data/discovery/` (project, git-ignored) | DISCOVERY |
| VALIDATION | 2019-01-02 .. 2022-12-30 | `C:\QuantLabV5_Vault\VALIDATION` | VALIDATION (after candidates + validation rules are frozen) |
| HISTORICAL_AUDIT_1 | 2023-01-03 .. 2025-12-31 | vault | HISTORICAL_AUDIT_1 (after ALL survivors + prop/risk/portfolio rules are frozen) |
| HISTORICAL_AUDIT_2 | 2026-01-02 .. last complete session | vault | HISTORICAL_AUDIT_2 (after the audit-1 report is frozen) |
| LIVE_FORWARD | sessions starting after the V5 final-cohort freeze | vault `LIVE_FORWARD/` | LIVE_FORWARD |

VALIDATION and both historical audits were already examined by V2-V4 (see `docs/prior_labs/README.md`).

## Layout

```
config/       partitions (definitions + registry), costs, sessions, stage policy, search, nulls, prop, execution, paths
quantlab5/    data/ engine/ features/ search/ validation/ nulls/ risk/ prop/ isolation/ (+ bootstrap, diagnostics,
              synthetic, util)    -- see docs/ARCHITECTURE.md
research/     s00_bootstrap (privileged), s01 structural check, s02 bootstrap freeze, run_worlds (resumable)
tools/        copy_v4_infra, collect_prior_labs, write_provenance, check_isolation, harden_isolation.ps1,
              ingest_live_forward
tests/        inherited V4 suite + V5 tests (synthetic data; tests/test_v5_bootstrap.py reads real METADATA only)
freezes/      V5_BOOTSTRAP_FREEZE.json (+ later stage freezes)
provenance/   source data, V4 copies (+final hashes), prior-lab manifest, environment, config hashes, tests, isolation
ledgers/      DATA_ACCESS_LEDGER.jsonl, RESEARCH_DECISION_LOG.jsonl, STAGE_STATE.json
results/ reports/   (empty; research outputs later)
docs/         ARCHITECTURE, INHERITED_FROM_V4, OS_ISOLATION, prior_labs/ (V2/V3/V4 catalogs + reports, reference only)
```

## Usage

```bash
python -m pytest                                     # full suite
python tools/check_isolation.py                      # is OS isolation active for this account?
```

```python
from quantlab5.isolation.load_view import load_view
md = load_view("NQ", "DISCOVERY", "2012-01-01", "2012-12-31", ["open", "high", "low", "close", "volume", "symbol"])
```
