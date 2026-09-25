# What V5 inherited from QuantLabV4, and what changed

Source: `C:\Users\Administrator\Desktop\QuantLabV4`, git HEAD `f491c796b859...` (tag `v4-campaign1-complete`).
Every copied file was committed and unmodified at that HEAD. `tools/copy_v4_infra.py` copied each file
byte for byte and recorded its SHA-256. It then applied a mechanical rename (`quantlab4` -> `quantlab5`,
and `quantlab4.v4.*` re-homed into the V5 layout) and recorded the hash again.
`provenance/V4_COPIED_FILES.json` holds the copy-time record. `provenance/V4_COPIED_FILES_FINAL.json` holds
the final hashes, with `byte_identical_to_v4`, `changed_beyond_rename` and `source_still_matches` for every file.

## Ported (116 files)

* The whole `quantlab4` package (bootstrap, data, diagnostics, engine, features, isolation, nulls, prop,
  risk, search, synthetic, util, validation, project, research_log).
* The V4 campaign sub-package `quantlab4/v4`, re-homed:

| V4 | V5 |
|---|---|
| v4/ops.py | features/ops.py |
| v4/featurelib.py | features/library.py |
| v4/market.py | data/market.py |
| v4/synth.py | synthetic/market_builders.py |
| v4/outcomes.py | engine/outcomes.py |
| v4/kernel.py | search/kernel.py (CSR + galloping kernel, V4 performance audit) |
| v4/world.py | search/world.py |
| v4/ml.py | search/ml.py |
| v4/analysis.py | search/analysis.py |
| v4/grammar.py | search/reference_grammar.py (reference only, NOT a V5 catalog) |
| v4/screen.py | search/reference_screen.py (reference only, V4 thresholds) |
| v4/inference.py | nulls/inference.py |
| v4/propsim.py | prop/propsim.py |

* All 24 V4 test modules. Three were renamed: test_v4_pipeline -> test_search_pipeline,
  test_v4_optimizations -> test_performance_optimizations, test_v4_propsim -> test_propsim.
* Config: costs, execution, nulls, prop_profiles and sessions are byte-identical to V4. Paths, search and
  stage_policy were rewritten for V5.
* research/s00_bootstrap, s01 (structural check), s02_bootstrap_freeze, run_worlds (resume runner).
* tools/check_isolation, write_provenance, harden_isolation.ps1, ingest_live_forward.

## Behaviour of the proven engine: unchanged

No change was made to execution, fills, costs, sessions/DST, rolls, resampling, features, outcome tables,
search kernels, null generators, sizing or the prop simulator. The regression guard is
`tests/test_v4_equivalence.py`. It imports the V4 code from disk and requires bit-identical outputs on
synthetic data for bars/sessions/alignment, resampling, next-bar execution, costs, feature library +
outcomes + kernel, a complete search world with every RULE and SYM candidate, five null generators,
fixed-dollar sizing and the prop-account simulator.

## Intentional changes (each covered by a test)

| Change | Where | Test |
|---|---|---|
| Stages/partitions renamed: CONFIRMATION->VALIDATION, FINAL_HISTORICAL_HOLDOUT->HISTORICAL_AUDIT_1, SEALED_2026_AUDIT->HISTORICAL_AUDIT_2, TRUE_FORWARD->LIVE_FORWARD; stage HISTORICAL_HOLDOUT->HISTORICAL_AUDIT_1, AUDIT_2026->HISTORICAL_AUDIT_2 | config/stage_policy.yaml, isolation/*, bootstrap/partitioner.py, project.py | test_stage_gate, test_load_view_isolation, test_forward |
| New freeze kinds: validation, audit_1_report, audit_2_report (V4: confirmation, holdout_report). LIVE_FORWARD now also needs the audit-2 report frozen | stage_gate.py | test_stage_gate (V5 additions) |
| Required sections for every freeze. The discovery freeze must carry validation_rules. The final cohort must carry prop_selection_rules, risk_rules and portfolio_rules | stage_policy.yaml, stage_gate.py, freezes.py | test_stage_gate |
| **No-candidate-cap rule** on freeze contents (write time + every read) | stage_gate.check_no_cap | test_stage_gate::test_no_cap_* |
| Clustering helper `duplicate_annotations` (annotation only) | search/clustering.py | test_v5_bootstrap |
| Candidate-ID default prefix Q4 -> Q5, namespace quantlab4 -> quantlab5 (same function) | search/candidate_id.py, config/search.yaml, reference_grammar.py | test_candidates, test_v4_equivalence |
| load_view refuses files inside an earlier lab's data store | isolation/load_view.py, config/paths.yaml | test_v5_bootstrap |
| Static data-access guard also forbids V2-V5 vault names, earlier labs' data folders and `prior_labs` | tests/test_no_direct_data_access.py | itself |
| s00: source hashes must equal the V4-verified hashes, the vault must be outside the project, V5 partitions are cross-checked against the V4 registry by hash | research/s00_bootstrap.py | run log + registry `v4_crosscheck` |
| test_propsim no longer reads V4's prereg file (profile inlined as a fixture) | tests/test_propsim.py | itself |

## Not copied

* `config/prereg_v4.yaml` and V4 reports -> `docs/prior_labs/V4` (reference only).
* V4 research scripts s03..s12 and p01..p09, results, freezes, ledgers, provenance and partition files.
  V5 re-partitioned from the original source files.
* One-off V4 tools tied to V4 result files (bench_*, profile_world, verify_world, dump_world_hashes,
  copy_v3_engine).
