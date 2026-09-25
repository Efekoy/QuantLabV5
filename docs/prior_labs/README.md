# Prior labs (V2, V3, V4): reference only

This folder holds the catalogs, preregistrations, freezes and reports of QuantLabV2, V3 and V4. It exists
so that V5 can later tell what has already been tested. **It is not an input to any V5 research
code.**

* Nothing under `quantlab5/` or `research/` may refer to this folder. The static test
  `tests/test_no_direct_data_access.py` enforces that.
* Catalog source code is stored as `*.py.txt`, so it cannot be imported.
* Large JSON catalogs are stored gzipped (`*.json.gz`). Their uncompressed SHA-256 equals the source file's.
* No market data, trade lists, ledgers or null-world files were copied.
* `provenance/PRIOR_LABS_MANIFEST.json` lists every file with its source path, source SHA-256, destination
  SHA-256 and whether it was committed in its source repository. Some V4 post-hoc reports
  (`V4_POSTHOC_*`) were uncommitted in V4 at copy time; the manifest marks them as such.

## Contamination warning

Reading these reports is knowledge of 2019-2026 market behaviour. V4 evaluated strategies on exactly
the V5 VALIDATION (2019-2022, V4 "CONFIRMATION"), HISTORICAL_AUDIT_1 (2023-2025, V4 "holdout") and
HISTORICAL_AUDIT_2 (2026, V4 "sealed 2026") periods. V2 and V3 examined those years too. For V5,
therefore, these partitions are **sealed in software but not unseen by the researcher**. Only
LIVE_FORWARD data, meaning sessions after the V5 final-cohort freeze, is genuinely out-of-sample.
