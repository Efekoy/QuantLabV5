# Freezes (written once, read-only, re-verified before every data read)

- `DISCOVERY_FREEZE.json` -- `quantlab3.freeze.freezes.freeze_discovery(...)`, only in state DISCOVERY.
- `FINAL_COHORT_FREEZE.json` -- `freeze_final_cohort(...)`, only in state CONFIRMATION, before 2023+ can open.
  Members are byte-identical copies of discovery-freeze specs.
