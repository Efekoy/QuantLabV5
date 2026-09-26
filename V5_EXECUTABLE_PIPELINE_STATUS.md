# V5 executable-pipeline checkpoint — synthetic only

**Status: implementation and calibration incomplete.** The data stage remains
`DISCOVERY`; the final preregistration, discovery freeze and `v5-prereg` tag do
not exist. This checkpoint does not authorize a real market search.

## Executable inventory

All 30 directional Stage A families now have causal signal builders on
`Market` bars. The code-generated grammar has 60 Stage A IDs, 214 possible
Stage B IDs, at most 57 conditional Stage C evaluations in one run, and at
most 331 evaluated records in one adaptive run. The conditional Stage C union
has 436 distinct IDs; the full ID universe has 710. Stage B/C are generated
only after the applicable Stage A/B advancement. The inventory is in
`reports/V5_CANDIDATE_INVENTORY.json`.

The adaptive runner evaluates Stage A, expands every family satisfying its
prespecified gate, evaluates applicable B rules, chooses the B parent for C,
and retains all evaluated records. Discovery qualification now records **all**
rules satisfying its economic and stability gate. Neighborhood representative
nomination is a separate annotation and does not cap qualification. Pairwise
annotations include entry and direction overlap, daily P&L correlation and
simultaneous position overlap. Unregistered A/B specifications fail closed.

## Isolation

`load_view` at the actual V5 project root now rejects real market reads until
a final preregistration freeze, pinned file hashes and the `v5-prereg` tag
verify. Synthetic throwaway projects retain their stage-machine tests. The
existing static direct-read test remains active. OS ACL isolation has not
been established in this process; an earlier isolation probe recorded that
vault paths were openable. The probe recorded one DISCOVERY-day read for an
access check before this runtime preregistration guard was added. No sealed
VALIDATION, historical-audit or LIVE_FORWARD market rows were read for this
checkpoint. See the data-access ledger for the complete access history.

## Remaining launch gates

- The executable synthetic planted-edge and independent-validation campaign
  has not been run. No actual 0.10R or 0.15R recovery estimate exists.
- Sufficient **complete market search** all-null worlds have not been run. The
  old fixed-stream proxy is planning evidence only.
- The variable A/B/C neighborhood validation procedure and blind two-audit
  stage architecture have not been made executable and frozen.
- The V5 catalog and research preregistration are still review drafts; their
  per-family implementation details and the revised grammar need reconciliation
  before a final hash pin.
- The final preregistration JSON currently has status `REVIEW_REQUIRED`; it is
  only a review-draft byte pin. It cannot unlock real data.

An executable one-year synthetic benchmark (360,180 bars, 60 Stage A rules)
took roughly 2.5 minutes before same-clock quantile optimization. A three-month
benchmark after that optimization took 5.5 seconds for 89,700 bars. These are
throughput measurements, **not** power or false-positive results.

The subsequent seeded synthetic profile identified E24's repeated window
histograms as the largest Stage A family cost. Precomputed rolling bin counts
reduced its measured family evaluation from 1.224 to 0.312 seconds on an
approximately 88,000-bar market. Daily session indices and calendar years are
now shared across candidate evaluations. A reference-formulation test checks
E24 signal arrays exactly for three lookbacks and two thresholds, including
forced eligibility at every bar. The complete test suite passed after these
changes with a workspace-local pytest temporary directory and Numba cache.
This optimization does not establish an end-to-end calibration runtime or
authorize any real partition read.

The complete test suite passed on this checkpoint: 308 tests, using a writable
workspace `NUMBA_CACHE_DIR` because the read-only V4 comparison checkout cannot
hold its own Numba cache. These tests establish implementation checks only;
they do not substitute for the missing full-search synthetic calibration.

The protocol requires stopping before real discovery until the missing
calibration, end-to-end validation, audit blindness, full tests, final freeze
and hash/tag verification are complete. No rule may be tuned using later real
market outcomes.
