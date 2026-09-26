# QuantLabV5.2 engineering stop status

**CALIBRATION_FAILED — NUISANCE_FIDELITY_FAILED.** V5.2 stops before its
generator freeze, executable all-null search, planted-edge power study, final
preregistration, or real strategy discovery. V5 and V5.1 remain archived at
their failure tags. No strategy family, candidate definition, threshold,
advancement rule or validation rule was changed.

## Cause and correction tested

The V5.1 seed-1002 failure was an additive random walk crossing zero after a
large cumulative NQ decline. See `V5_2_POSITIVITY_DIAGNOSIS.md` for initial,
minimum and first-invalid prices, timestamps, OHLC low behavior, and the
independent ES reconstruction.

V5.2 tested one smooth multiplicative reconstruction: it applies the same
strictly increasing exponential map to all latent open, high, low and close
components. There is no clipping, winsorization, seed substitution or
per-seed bound. Seed 1002 now passes the full OHLCV invariant test. Its
minimum NQ low is 1281.776387 points and minimum ES low is 842.307123;
all prices and volumes are finite, prices positive, volume nonnegative,
timestamps monotonic, and OHLC ordering valid.

## Unchanged nuisance and zero-edge gate

The correction was tested against the frozen V5.1 nuisance and zero-edge
diagnostics on the original seeds 9101–9103. Seeds 9101 and 9102 passed.
Seed 9103 **failed**: NQ session-clock range median/p90 maximum relative
error was **0.327393**, above the unchanged **0.25** limit. The general
zero-edge checks passed on all three seeds; their largest diagnostic was
0.001525 against 0.01. The full deterministic result is
`reports/V5_2_NUISANCE_FIDELITY.json` (SHA-256
`2a4f843dc4e1cf05bd3aeeed5e5f6885ba77437191352c5817f9b4a0cb7de33f`).
The tested generator code SHA-256 is
`1a8958a728c0e8ea5442251367cf679edc2b8958968f179d1ebc42ee4f6b4981`.

Per the V5.2 instruction to STOP if fidelity fails after the positivity fix,
there was no parameter tuning using seed 9103, no alternate seed, and no
threshold change. A hundreds-to-thousands-seed structural stress test was
not run because this earlier frozen fidelity gate failed. Therefore broad
structural validity is unproven. The V5.2 generator was not frozen and no
power calibration started.

## Isolation

V5.2 made **no new real-market read**. The diagnostic used only V5.1's
previously permitted unsigned nuisance tape and generated synthetic worlds.
No candidate P&L, PF, expectancy, t statistic or ranking was calculated on
real DISCOVERY. VALIDATION, both historical audits and LIVE_FORWARD remain
unopened. The ordinary preregistration guard stays closed. There is no
`v5.2-prereg` tag.

The full repository suite passed **320 collected tests**, including the
regression test for original failing seed 1002. Both existing access-ledger
chains verify; the V5.1 one-shot access state remains `COMPLETE`.
