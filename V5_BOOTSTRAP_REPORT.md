# QuantLabV5 bootstrap report

This bootstrap covers infrastructure only. No strategy research was run, no V5 strategy catalog exists,
and no strategy performance was computed. The only data inspected was structural counts on DISCOVERY
(schema, volume validity, rolls), all read through `load_view`.

## Project

| | |
|---|---|
| Project path | `C:\Users\Administrator\Desktop\QuantLabV5` |
| Vault | `C:\QuantLabV5_Vault`, outside the project. NTFS ACL: Administrators + SYSTEM only, inheritance removed |
| Current stage | **DISCOVERY**. Only the DISCOVERY partition is readable (`ledgers/STAGE_STATE.json`, cross-checked against the ledger) |
| OS isolation | **NOT ACTIVE**, see below |
| Bootstrap freeze | `freezes/V5_BOOTSTRAP_FREEZE.json`, body SHA-256 `76aa9bea6d21c53044b7215917aef19684b4135a7359def0297e4e50fbdc0fb9`. It pins 233 tracked files, the registry, all partition and source hashes, the test results and ledger anchor seq 8. The reproduction check passed |
| Code commit pinned by the freeze | `3f783659eb5218b78049fd05cbdb242e37a04c27` |
| Git tag | `v5-bootstrap`, on the commit that adds this report and the freeze on top of the pinned commit |
| Registry hash (pinned in the stage state) | `8ba89bc09a91b3f61290c654384ca951a92add841a99a5bfb14f3e2009e4c81c` |

## V4 infrastructure reused

* Source: QuantLabV4 at HEAD `f491c796b859` (tag `v4-campaign1-complete`). Only committed, unmodified
  files were copied: **116 files**, by `tools/copy_v4_infra.py`.
  * 35 are byte-identical to V4. These include the cost, session, execution, null and prop configs, and
    several test modules.
  * 46 differ from V4 only by the mechanical rename `quantlab4` -> `quantlab5`, including the V4
    sub-package re-homed into the V5 layout.
  * 35 have V5 changes beyond the rename. These are isolation/stage/config/tooling/docs/tests, plus
    docstring-only notes in four search/prop modules.
  * **No engine, data, feature, null, risk, validation or kernel module changed beyond the rename.**
  * Records: `provenance/V4_COPIED_FILES.json` (source hash, copy hash, post-rename hash) and
    `provenance/V4_COPIED_FILES_FINAL.json` (final hash plus flags). Details are in `docs/INHERITED_FROM_V4.md`.
* Reused components:
  * backtest/execution engine with next-bar fills, pessimistic stop/target, 1-tick trade-through, and
    flat at session end and at rolls
  * costs and metrics (NQ $14 and ES $29 per round trip at baseline; MNQ/MES commissions are still
    unvalidated placeholders)
  * sessions/DST/rolls; resampling; OHLCV schema with volume as a first-class column; same-minute NQ/ES
    alignment
  * causal feature framework, primitives and the V4 feature library
  * content-derived candidate IDs, now `Q5-`/`quantlab5`
  * fixed-dollar MNQ sizing; prop-account simulator and cohort prop simulation
  * null generators, the single-evaluator null pipeline and search-adjusted inference
  * purging/embargo/walk-forward/CSCV; stage gate; hash manifests; hash-chained ledger; controlled
    `load_view`
  * synthetic markets
  * V4 performance optimisations: O(n) extrema, memoised group starts, CSR + galloping kernel
  * resume/checkpoint: the verified-output world runner and the hash-chained decision log with resume state
* **Proof that behaviour is unchanged:** `tests/test_v4_equivalence.py` (16 tests) imports V4's code from
  disk and requires bit-identical outputs on synthetic data. It covers bars/sessions/alignment,
  resampling, next-bar execution (3 modes), costs, feature library + outcome tables, a complete search
  world (every RULE and SYM candidate, screen, family statistics, per-candidate stat files), 5 null
  generators, fixed-dollar sizing and the prop simulator. The only intended difference, the candidate-ID
  namespace, is asserted explicitly.
* Not copied into the active pipeline: V4 survivors, cohorts, results, freezes, ledgers, the
  preregistration numbers, and research scripts s03-s12 / p01-p09.
* Prior labs: V2 (25 files), V3 (32) and V4 (39) catalogs, preregistrations, freezes and reports are in
  `docs/prior_labs/`, reference only. They are hashed in `provenance/PRIOR_LABS_MANIFEST.json`. Code files
  are stored as `.py.txt`, and V3's 54 MB discovery freeze is stored gzipped. A static test forbids any
  V5 code from referencing the folder.

## Source data (read-only, never modified)

These are the same files, with the same SHA-256, that V4 verified. `s00` refuses to run if either hash differs.

| Inst | Path | Bytes | SHA-256 | Rows | Coverage (UTC) |
|---|---|---|---|---|---|
| NQ | `C:\Users\Administrator\Desktop\Quant\data\NQ\nq_continuous_front_1m.parquet` | 84,200,073 | `63b8f16dd1da0a35f2fdfdc9039686ffc8db0ada84333bfc7cd85f8f28d013e7` | 5,459,797 | 2010-06-07 22:00 .. 2026-08-10 23:59 (final session 2026-08-11 **incomplete**) |
| ES | `C:\Users\Administrator\Desktop\Quant\data\ES\es_continuous_front_1m.parquet` | 78,272,794 | `4a5dcac73b45f8097164e1242447fb490e6b2d52b4012cbe1ee3890f2d76edb2` | 5,633,953 | 2010-06-07 22:00 .. 2026-08-14 20:59 (complete) |

## Partitions

Sessions run 18:00-17:00 New York and are labelled by the date they end. Every source row landed in
exactly one partition, except the 120 NQ rows of the incomplete session 2026-08-11. Row accounting is
exact, and there are 0 `roll_session` label disagreements.

| Inst | Partition | Data sessions | Sessions | Rows | SHA-256 | Location |
|---|---|---|---|---|---|---|
| NQ | DISCOVERY | 2010-06-08 .. 2018-12-31 | 2,198 | 2,776,632 | `fe96495715c37d1fea42c228e0cf9c13f4b5df12682d3ac611701695faa6baa9` | project `data\discovery\NQ_DISCOVERY.parquet` |
| NQ | VALIDATION | 2019-01-02 .. 2022-12-30 | 1,034 | 1,407,095 | `da3c6f5e7da762787cf6ba2166a92e374758f7e8881e7ad6606426ab04ead421` | vault `VALIDATION\` |
| NQ | HISTORICAL_AUDIT_1 | 2023-01-03 .. 2025-12-31 | 775 | 1,060,967 | `596a0f68e0738f5e6f7044e07d295010c723b1e440a9d214217cd7bc6d09c890` | vault `HISTORICAL_AUDIT_1\` |
| NQ | HISTORICAL_AUDIT_2 | 2026-01-02 .. **2026-08-10** | 157 | 214,983 | `95e65133d0f196eacf1f91c7626f0295d79cd9d7dda8dd9b63632ad64c9e1c5c` | vault `HISTORICAL_AUDIT_2\` |
| ES | DISCOVERY | 2010-06-08 .. 2018-12-31 | 2,198 | 2,945,493 | `25b0c9f27dc2b662b1be736eeb8b811d757d0fcb9700290627a1e6f81f9a88f2` | project `data\discovery\ES_DISCOVERY.parquet` |
| ES | VALIDATION | 2019-01-02 .. 2022-12-30 | 1,034 | 1,407,376 | `f48df4e60adb5e62af9a7bd69e52f5037a9be79853e164c8121868eae8ea06e5` | vault |
| ES | HISTORICAL_AUDIT_1 | 2023-01-03 .. 2025-12-31 | 775 | 1,060,571 | `45ea6cbc913f41737ea18b32ecd309acdd47e12e27b54555ba5d8008cca926f1` | vault |
| ES | HISTORICAL_AUDIT_2 | 2026-01-02 .. **2026-08-14** | 161 | 220,513 | `bd052becc67ce6235a8d27832b91b4eaf59d79caee1cb5f165e396eb04e774e1` | vault |
| both | LIVE_FORWARD | sessions starting after the future V5 final-cohort freeze | 0 | 0 | none | vault `LIVE_FORWARD\{inbox,accepted}` (empty; ingestion refused until the freeze) |

* The joint (NQ and ES) last complete session is 2026-08-10.
* Cross-check: every one of the 8 V5 partition files is **byte-identical (same SHA-256, same rows)** to
  the V4 partition covering the same period. The comparison used V4's registry hashes only; V4's
  partition files were not opened.

## Access rules (stage machine)

`BOOTSTRAP -> DISCOVERY -> DISCOVERY_FROZEN -> VALIDATION -> VALIDATION_FROZEN -> FINAL_COHORT_FROZEN ->
HISTORICAL_AUDIT_1 -> HISTORICAL_AUDIT_2 -> LIVE_FORWARD`. It moves one step at a time and never backwards.

* VALIDATION opens only after a DISCOVERY_FREEZE that contains the candidates, the qualifying set and the
  validation rules.
* HISTORICAL_AUDIT_1 opens only after the VALIDATION_FREEZE (all survivors) and a FINAL_COHORT_FREEZE that
  contains all survivors, parameters, prop-selection, risk, portfolio and sizing rules.
* HISTORICAL_AUDIT_2 additionally requires the audit-1 report to be frozen. LIVE_FORWARD additionally
  requires the audit-2 report to be frozen.
* **No candidate cap.** The stage gate enforces it on the freeze contents, both when a freeze is written
  and on every later read:
  * every qualifying discovery candidate advances; duplicates may only be annotated;
  * validation evaluates every frozen candidate;
  * the final cohort equals the validation survivors exactly. Tests cover 7 and 70 survivors, a top-5 cut
    (refused), an added non-survivor (refused) and zero survivors (recordable, but the audits never open).
* Data-access ledger at freeze time: 10 records, chain verified. Research reads: 3, all ALLOWED, all
  DISCOVERY (the s01 structural check for NQ and ES, and a one-session NQ probe by `check_isolation`).
  No VALIDATION or audit partition has been read through the research API.

## OS isolation

**Not active.** Research runs as `Administrator`. `tools/check_isolation.py` shows as OPENABLE every V5
vault file, both raw source files and the V3/V4 vault and data files
(`provenance/ISOLATION_CHECK_Administrator.json`). The software gate is kept: load_view, the stage
gate, registry/freeze pins, the ledger, refusal of earlier labs' data stores, and a static test against
direct file access. Physical placement and the NTFS ACL on the vault are active, but neither restricts an
administrator. `tools/harden_isolation.ps1` (user `qlv5research`) is prepared but was not run, because it
needs a password that you choose. See `docs/OS_ISOLATION.md`.

## Tests

**252 tests, 252 passed, 0 failed, 0 skipped** (`provenance/TEST_RESULTS.xml`, `provenance/TEST_ENVIRONMENT.json`).
Python 3.12.10 on Windows Server 2022. numpy 2.5.2, pandas 3.0.5, pyarrow 25.0.1, numba 0.67.0,
llvmlite 0.49.0, PyYAML 6.0.3, pytest 9.1.1. The full pip freeze is in `provenance/ENVIRONMENT.json`.

| Required check | Tests |
|---|---|
| next-bar execution | test_engine_timing, test_engine_synthetic_markets, test_search_pipeline (outcomes/kernel = reference engine), test_v4_equivalence |
| no lookahead | test_features_causality, test_search_pipeline (every feature/trigger/filter/symbol plus an intentional-leak detector) |
| resampling causality | test_resample |
| NQ/ES synchronisation | test_features_causality (same-minute only, no forward fill), test_v5_bootstrap (Market via load_market), null joint flips in test_nulls_pipeline |
| volume handling | test_schema_volume_rolls, test_load_view_isolation, test_resample; real DISCOVERY structural check below |
| DST/session handling | test_sessions_dst |
| partition hashes | test_load_view_isolation (tampered/corrupted partitions refused), test_v5_bootstrap (real registry metadata, DISCOVERY hash, spec dates, no overlap, row accounting) |
| stage locking | test_stage_gate (27, incl. the no-cap rule and both audits), test_forward |
| ledger tamper detection | test_ledger, test_load_view_isolation (forged stage state) |
| fixed-dollar sizing | test_fixed_dollar, test_propsim |
| prop-account math | test_prop_account, test_propsim |
| null pipeline | test_nulls_pipeline |
| purging/embargo | test_validation_splits |
| deterministic candidate IDs | test_candidates |
| resume/checkpoint | test_research_log, test_v5_bootstrap (world-runner resume, resume state) |
| V4 behaviour unchanged | test_v4_equivalence (16) |

Per module: candidates 11, cleaning 3, costs_metrics 8, engine_synthetic_markets 11, engine_timing 8,
features_causality 9, fixed_dollar 14, forward 4, ledger 11, load_view_isolation 26, manifests_hashing 3,
no_direct_data_access 3, nulls_pipeline 11, performance_optimizations 9, prop_account 14, propsim 3,
resample 8, research_log 2, schema_volume_rolls 10, search_pipeline 14, sessions_dst 7, stage_gate 27,
v4_equivalence 16, v5_bootstrap 12, validation_splits 8.

Real DISCOVERY structural check (counts only; `provenance/DISCOVERY_STRUCTURAL_CHECK.json`). For both
NQ and ES:
* volume is int64, with 0 unparseable, 0 negative, 0 missing and 0 zero-volume rows;
* 35 symbol-derived rolls equal the 35 `roll_boundary` flags, and all fall at session starts;
* there are 0 duplicate-timestamp flags;
* the NQ and ES schemas are identical.

## Deviations and problems

1. **Nothing but LIVE_FORWARD is unseen.** V4 evaluated strategies on exactly the VALIDATION,
   HISTORICAL_AUDIT_1 and HISTORICAL_AUDIT_2 periods, and V2/V3 examined them too. Their reports are now
   in `docs/prior_labs` at your request. The sealing prevents V5 code from reading those periods. It
   cannot remove what the researcher already knows about them. Only post-freeze LIVE_FORWARD sessions
   are genuinely out-of-sample.
2. HISTORICAL_AUDIT_2 ends on a different date for each instrument: NQ 2026-08-10 (its source file ends
   mid-session) and ES 2026-08-14. Work that uses both instruments must intersect sessions (joint last:
   2026-08-10). Sessions between those dates and the future freeze belong to no partition.
3. Stricter than specified: the audits open one after the other, and LIVE_FORWARD also needs the audit-2
   report to be frozen.
4. The first git commit was made under the global `core.autocrlf=true`. That normalised CRLF files and
   treated some PDFs as text. Fixed in the next commit (`.gitattributes: * -text`, repo-local autocrlf
   off), and every blob was verified to equal its working file. The problem is logged in
   `ledgers/RESEARCH_DECISION_LOG.jsonl`.
5. During porting, `tests/test_propsim.py` read V4's `config/prereg_v4.yaml`. The generic profile values
   are now inlined as a test fixture, so V4's preregistration is not part of V5.
6. `search/reference_grammar.py` and `search/reference_screen.py` are V4's grammar and screen. They were
   kept so the inherited kernels, world runner and their tests work. **They are not the V5 catalog.**
7. MNQ/MES commissions are still the unvalidated placeholders inherited from V4.
8. Pre-existing condition, not changed: the raw data folder grants Modify to `CodexSandboxUsers` and to an
   unresolved SID.

## Stopped here

The V5 strategy catalog has not been created and discovery has not begun. The next step waits for your
next prompt.
