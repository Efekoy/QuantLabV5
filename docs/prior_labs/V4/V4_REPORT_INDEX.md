# QuantLabV4 report and naming index

| Campaign term (research brief) | Implemented name |
|---|---|
| DISCOVERY 2010-06-01..2018-12-31 | partition/stage `DISCOVERY` |
| VALIDATION 2019-01-01..2022-12-31 | partition `CONFIRMATION`, stage `CONFIRMATION` |
| VALIDATION_FREEZE / FINAL_SELECTION_FREEZE | `freezes/CONFIRMATION_FREEZE.json` (stage `CONFIRMATION_FROZEN`) + `freezes/FINAL_COHORT_FREEZE.json` (stage `FINAL_COHORT_FROZEN`), mirrored as `V4_FINAL_COHORT_FREEZE.json` |
| FINAL HISTORICAL HOLDOUT 2023-2025 | partition `FINAL_HISTORICAL_HOLDOUT`, stage `HISTORICAL_HOLDOUT` |
| SEALED_2026_FORWARD (official V4 forward test) | partition `SEALED_2026_AUDIT`, stage `AUDIT_2026` |
| LIVE_FORWARD / PROSPECTIVE_FORWARD | partition/stage `TRUE_FORWARD` (forward inbox in the vault) |

Reports are listed in the order they are produced; see each file.

## Reports (campaign 1)

| required report | file |
|---|---|
| bootstrap | V4_BOOTSTRAP_REPORT.md |
| data audit | V4_DATA_AUDIT.md |
| feature catalog | V4_FEATURE_CATALOG.md |
| preregistration | V4_RESEARCH_PREREGISTRATION.md (+ config/prereg_v4.yaml) |
| discovery | V4_DISCOVERY_REPORT.md |
| null validation | V4_NULL_VALIDATION_REPORT.md + V4_NULL_VALIDATION_ADDENDUM.md |
| discovery null | V4_DISCOVERY_NULL_REPORT.md |
| cluster | V4_CLUSTER_REPORT.md |
| validation | V4_VALIDATION_REPORT.md |
| validation null | V4_VALIDATION_NULL_REPORT.md |
| prop research | V4_PROP_RESEARCH_REPORT.md |
| final selection | V4_FINAL_SELECTION_REPORT.md (+ V4_FINAL_COHORT_FREEZE.json) |
| historical holdout | V4_HISTORICAL_HOLDOUT_REPORT.md |
| 2026 forward | V4_2026_FORWARD_REPORT.md |
| live forward protocol / status | V4_LIVE_FORWARD_PROTOCOL.md / V4_LIVE_FORWARD_STATUS.md |
| performance audit | V4_NULL_PERFORMANCE_PROFILE.md |
| master record | V4_MASTER_RESEARCH_RECORD.md |
