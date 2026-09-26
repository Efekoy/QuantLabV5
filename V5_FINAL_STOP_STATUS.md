# QuantLabV5 final stop status

**CALIBRATION_FAILED**

V5 stopped before real strategy discovery. Its nuisance-calibrated synthetic
market generator failed the frozen fidelity test. This is a failure of the
measurement infrastructure; it is not evidence for or against any of the 30
strategy families. The V5 calibration outcome, thresholds, and scientific
design remain frozen. V5 will not be reopened or tagged `v5-prereg`.

## Frozen evidence

- Precalibration science freeze SHA-256:
  `361821f46c322dc9343a647eaa104487aafd222967525932acf218aac580255c`.
- Nuisance artifact SHA-256:
  `49d67e04ea361a18339d5913826d5865cfc13eb235be9706d4f00e7ff3ee444f`.
- Calendar template SHA-256:
  `73c408ce7a2ae5141ee9405941c0c2b473921228600d677519cb84fcad9c62e2`.
- Diagnostic seeds: 9001, 9002, 9003. All three failed.

| Frozen fidelity metric | Limit | Seed 9001 | Seed 9002 | Seed 9003 |
| --- | ---: | ---: | ---: | ---: |
| NQ/ES log absolute-body correlation error | ≤0.10 | 0.161240 | 0.160556 | 0.159802 |
| ES log volume lag-one correlation error | ≤0.10 | 0.130874 | 0.130671 | 0.131004 |
| ES per-clock volume median/p90 maximum relative error | ≤0.25 | 0.274448 | 0.200000 | 0.300000 |

Other frozen checks remain in `reports/V5_NUISANCE_MODEL_FIT.json`. The
executable campaign checkpoint is `FAIL_NUISANCE_MODEL`, with zero adaptive
all-null worlds and zero planted-edge cells run.

## Data access and tests

The verified V5 access ledger contains 15 records. Sequence 10 records the
science freeze, 11 opens the restricted calibration worker, 12 and 13 record
the only new NQ and ES DISCOVERY reads, and 14 closes calibration with output
hashes. The one-shot state is `COMPLETE`. Earlier structural DISCOVERY reads
at sequences 5–7 predated the science freeze and are disclosed in it.

No V5 candidate P&L, PF, expectancy, t statistic, family ranking, or strategy
ranking was calculated on real DISCOVERY. No real strategy search ran.
VALIDATION, HISTORICAL_AUDIT_1, HISTORICAL_AUDIT_2, and LIVE_FORWARD each have
zero allowed reads. The project remains at DISCOVERY stage; the ordinary real
strategy access guard rejects reads because final preregistration does not
exist.

The full suite had 318 passing tests before the science freeze. Six focused
guard, null, plant, and validation tests passed after the final code edits and
before the freeze. Python compilation succeeded. The detailed twelve-point
record is `V5_CALIBRATION_STOP_REPORT.md`.

The stopped repository state is archived under Git tag
`v5-calibration-failed`.
