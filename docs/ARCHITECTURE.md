# QuantLabV5 architecture (bootstrap)

Ported from QuantLabV4 (`docs/ARCHITECTURE.md` there). The behaviour of the ported engine is unchanged.
`tests/test_v4_equivalence.py` compares it bit for bit against the V4 code on disk. What changed is listed
in `docs/INHERITED_FROM_V4.md`.

## Data flow

```
raw NQ/ES parquet (Desktop\Quant\data, never modified; same files and SHA-256 as V4)
   |  research/s00_bootstrap.py -> quantlab5/bootstrap/partitioner.py   [privileged, once]
   |  streams row groups, reads timestamps only, copies rows unchanged
   v
data/discovery/{NQ,ES}_DISCOVERY.parquet     C:\QuantLabV5_Vault\{VALIDATION,HISTORICAL_AUDIT_1,HISTORICAL_AUDIT_2}\
   |                                         C:\QuantLabV5_Vault\LIVE_FORWARD\{inbox,accepted}\  (empty)
   |  quantlab5.isolation.load_view(instrument, partition, start, end, columns)
   |    1 validate arguments (refuse paths / unknown names / bad dates)
   |    2 stage gate: verify STAGE_STATE hash, ledger chain, ledger<->state agreement,
   |      registry pin, every pinned freeze (hash AND the V5 no-cap content rule); partition readable now?
   |    3 registry lookup; resolved path must sit inside its partition directory; never a raw file,
   |      never a file inside an earlier lab's data store (config/paths.yaml prior_lab_data)
   |    4 requested sessions must lie inside the partition
   |    5 SHA-256 of the partition file == registry
   |    6 read only requested sessions/columns; integrity check (incl. volume)
   |    7 append ALLOWED record to the hash-chained ledger, THEN return a copy
   |    (any refusal -> REFUSED record, then AccessRefused)
   v
MarketData.frame (pandas copy) -> .bars() -> Bars (read-only numpy, volume included)
   |                               data.market.load_market -> Market (NQ traded + ES aligned same-minute)
   v
search.pipeline.evaluate_candidates / search.world.run_world      <- null worlds enter HERE too
   -> engine.execution.run_signals -> engine.backtest kernel (reference)
   -> engine.outcomes + search.kernel (fast, proven equal to the reference engine) -> costs -> results
```

## Package layout

| Package | Contents (all ported from V4) |
|---|---|
| `isolation/` | load_view, stage_gate (V5 stages, no-cap rule), ledger, manifests, freezes, forward (LIVE_FORWARD) |
| `bootstrap/` | privileged one-time partitioner |
| `data/` | schema (volume first-class), sessions/DST, rolls, resample, align, cleaning, volume QC, `market` (NQ+ES world) |
| `engine/` | next-bar-fill reference kernel, execution windows, costs, metrics, `outcomes` (precomputed exit tables) |
| `features/` | causal feature interface (`base`), group-aware causal primitives (`ops`), inherited feature library (`library`) |
| `search/` | content-derived candidate IDs, generic grammar/generator, THE evaluation pipeline, numba search `kernel`, world runner, ML walk-forward, analysis, clustering (annotation only), `reference_grammar`/`reference_screen` (V4 reference, NOT a V5 catalog) |
| `nulls/` | null generators (sign flips, session permutation, time-of-day block resampling), runner, `inference` (search-adjusted p-values) |
| `validation/` | purging, embargo, chronological splits (walk-forward, CSCV) |
| `risk/` | fixed-dollar and fixed-contract sizing |
| `prop/` | generic prop-account simulator, `propsim` (MNQ fixed-dollar cohort simulation) |
| `diagnostics/` | lookahead detector (future-rewrite test) |
| `synthetic/` | synthetic markets with known properties (tests only) |

## Stages (config/stage_policy.yaml)

```
BOOTSTRAP -> DISCOVERY -> DISCOVERY_FROZEN -> VALIDATION -> VALIDATION_FROZEN
  -> FINAL_COHORT_FROZEN -> HISTORICAL_AUDIT_1 -> HISTORICAL_AUDIT_2 -> LIVE_FORWARD
```

| Stage | Readable | Entry precondition |
|---|---|---|
| DISCOVERY | DISCOVERY | every registered partition file verifies; registry pinned |
| DISCOVERY_FROZEN | DISCOVERY | DISCOVERY_FREEZE: candidates, qualifying, validation_rules, selection_process |
| VALIDATION | + VALIDATION | discovery freeze still verifies |
| VALIDATION_FROZEN | same | VALIDATION_FREEZE: evaluated (= all frozen candidates), survivors |
| FINAL_COHORT_FROZEN | same | FINAL_COHORT_FREEZE: cohort (= ALL survivors), parameters, prop_selection_rules, risk_rules, portfolio_rules, sizing_rules, selection_process |
| HISTORICAL_AUDIT_1 | + HISTORICAL_AUDIT_1 | all three freezes verify |
| HISTORICAL_AUDIT_2 | + HISTORICAL_AUDIT_2 | + AUDIT_1_REPORT_FREEZE |
| LIVE_FORWARD | + LIVE_FORWARD | + AUDIT_2_REPORT_FREEZE |

Only one step forward at a time, and there is no way back. The stage file is hashed and cross-checked
against the ledger's STAGE_ENTERED records.

## V5 no-candidate-cap rule

`stage_gate.check_no_cap` runs when a freeze is written and again every time it is re-verified, which
happens before every read:

* discovery: every `qualifying` ID is in `candidates`. `duplicate_of` may map advanced candidates to a
  representative. That is an annotation only, and every annotated duplicate still advances.
* validation: `evaluated` equals the frozen discovery `candidates` exactly, and `survivors` is a subset of it.
  Zero survivors can be recorded, but then no final cohort can be frozen and the audits never open.
* final cohort: `cohort` equals the frozen validation `survivors` exactly. If 7 survive, all 7 advance.
  If 70 survive, all 70 advance.

## Time conventions (unchanged from V4)

* Timestamps: UTC ns, bar START. Sessions: 18:00-17:00 America/New_York, labelled by END date.
* A signal at bar t is known at the close of bar t. The earliest fill is the open of bar t+1, in the same
  session and contract. Pessimistic same-bar stop/target. A target fills only if price trades 1 tick through it.
  Positions are flat at session end and at each roll.
* Higher-timeframe bars become available only after their last minute closes.
* Cross-market: only the SAME-minute bar of the other instrument is visible. There is no forward fill.

## Isolation layers

| Layer | Mechanism | Status |
|---|---|---|
| Software | load_view + stage gate + registry/freeze pins + hash-chained ledger | ACTIVE |
| Physical placement | sealed partitions outside the project tree (`C:\QuantLabV5_Vault`) | ACTIVE |
| NTFS ACL | vault restricted to Administrators + SYSTEM | ACTIVE (does not restrict administrators) |
| Separate non-admin research account | `tools/harden_isolation.ps1` | NOT ACTIVE; needs a manual run by the user (docs/OS_ISOLATION.md) |

## Determinism

* Candidate ID = `Q5-` + SHA-256(canonical_json({namespace: "quantlab5", spec}))[:24]. It depends on content
  only, and V5 IDs never equal V2/V3/V4 IDs.
* Enumeration order is either lexicographic or a seeded PCG64 permutation. Null generators are seeded by
  (seed, generator name, params).
* Resume: `research/run_worlds.py` skips a job only when its output exists and its embedded SHA-256
  verifies. `quantlab5.research_log` keeps the hash-chained decision log and
  `provenance/AUTONOMOUS_RESUME_STATE.json`, which holds completed steps and output hashes.
