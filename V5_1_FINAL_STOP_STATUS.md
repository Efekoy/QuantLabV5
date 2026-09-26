# QuantLabV5_1 final engineering stop status

**CALIBRATION_FAILED.** V5.1 remains closed to real strategy discovery.
The stopped V5 result remains archived unchanged at `v5-calibration-failed`.
V5.1 changed only the null-engine and nuisance-fidelity infrastructure;
the 30-family strategy grammar, candidate IDs, no-cap advancement,
validation rules, power gates and later-stage sequence stayed unchanged.

## Frozen protocol and controlled access

- V5.1 nuisance protocol freeze SHA-256:
  `cbb10197004ca1c60128ab7a23917e5c454b232a67f40635a5d9c80f0fb8cd64`.
- One-shot worker read only NQ/ES DISCOVERY, 2010-06-08 through 2018-12-31,
  and the six canonical OHLCV/symbol columns. It emitted an unsigned paired
  nuisance tape, sign-agreement parameters, hashes, and a seed manifest.
- Nuisance artifact SHA-256:
  `23f1b9f2ec77fb346149a27baf8f4d353edf1fad58b4e71e426ef24bc373b8ea`.
  Tape SHA-256:
  `8a93507f1622ee9012552ca00c00bc13ee786828bb7b0af96198be82b05f9e02`.
  Raw prices and absolute historical return-sign sequences were not emitted.
- The fresh V5.1 ledger verifies with six records: genesis 0, freeze 1,
  worker open 2, NQ read 3, ES read 4, and worker close 5. The one-shot
  state is `COMPLETE`. The inherited stage ledger also verifies with 17
  records, including the two V5.1 worker reads; the V5 archive tag retains
  the earlier 15-record V5 state.

## Empirical null-engine result

The frozen fidelity checker tested all three architectures on seeds
9101–9103. `paired_sign` and `state_conditioned_sign` passed all nuisance and
general zero-direction checks on all three worlds. `paired_day_resample`
failed the frozen per-clock zero-fraction tolerance on seeds 9102 and 9103.
The predeclared priority selected `paired_sign`. Its maximum zero-direction
diagnostic across the three worlds was 0.001525 against the 0.01 limit.
The fit report SHA-256 is
`7939a91eef962b50adf77f6d00790d4c2778fc6335f3408f98a02258d1368d22`.

The executable calibration then failed **before completion of the 19-world
Stage A reference**. Seed 999 and reference seeds 1000–1001 generated;
reference seed 1002 raised `ValueError: V5.1 zero-edge price path crossed
zero`. The frozen generator cannot produce the required positive-price
market for this seed. No seed was substituted and no generator, metric, or
threshold was changed after nuisance access. There are no complete Stage A
reference statistics, no 500-world adaptive null reference, no 200-world
all-null test, and no planted-edge power result. The frozen executable
calibration gate is therefore **not passed**.

No candidate P&L, PF, expectancy, t statistic, family ranking, or strategy
ranking was computed on real DISCOVERY. The synthetic Stage A evaluations
that completed before the seed failure do not constitute real strategy
discovery. VALIDATION, both historical audits, and LIVE_FORWARD still have
zero allowed reads. The stage remains DISCOVERY and the ordinary prereg
guard rejects real strategy access. There is no `v5.1-prereg` tag.

The failure is a null-world path-validity failure, not evidence about the
strategy families. V5.1 stops here under its frozen calibration protocol.
The complete successor test suite passed: 319 collected tests, with the
existing numerical-runtime warnings confined to the preexisting feature
library test.
