# V5 controlled DISCOVERY calibration: frozen stop decision

**Decision: STOP.** The pinned nuisance simulator failed its prespecified
fidelity gate on all three diagnostic synthetic worlds. The executable adaptive
all-null and planted-edge campaigns did not start. The science freeze forbids
using this DISCOVERY calibration to change the simulator, strategies, or gates.
Final preregistration, the `v5-prereg` tag, and real DISCOVERY strategy search
are therefore withheld.

1. **Precalibration science freeze:**
   `361821f46c322dc9343a647eaa104487aafd222967525932acf218aac580255c`.
   `science_freeze_ready` verifies its body, pinned files, candidate IDs, and
   ledger anchor. Earlier structural DISCOVERY reads at ledger sequences 5–7
   predated this freeze. This freeze establishes the design before the new
   nuisance access, not before those earlier structural reads.
2. **Worker permission:** NQ and ES only, DISCOVERY only, inclusive sessions
   2010-06-08 through 2018-12-31, columns `open, high, low, close, volume,
   symbol`, purpose/reason `CALIBRATION_NUISANCE_ACCESS`, one-shot pinned worker
   `research/calibrate_v5_discovery_nuisance.py`.
3. **Actual access:** NQ 2,776,632 rows, partition SHA-256
   `fe96495715c37d1fea42c228e0cf9c13f4b5df12682d3ac611701695faa6baa9`;
   ES 2,945,493 rows, partition SHA-256
   `25b0c9f27dc2b662b1be736eeb8b811d757d0fcb9700290627a1e6f81f9a88f2`.
   Both reads used the exact worker permission. No later partition was read.
4. **Exposed to main research:** exact calendar and contract-segment template;
   per-clock unconditional body, range, wick, and volume counts/quantiles/zero
   fractions; absolute gap quantiles; unsigned magnitude and volume lag
   correlations; median price; contemporaneous NQ/ES sign agreement and
   absolute-body dependence. Raw OHLCV and signed return sequences were kept
   inside the worker. Artifact SHA-256:
   `49d67e04ea361a18339d5913826d5865cfc13eb235be9706d4f00e7ff3ee444f`;
   calendar-template SHA-256:
   `73c408ce7a2ae5141ee9405941c0c2b473921228600d677519cb84fcad9c62e2`.
5. **Real DISCOVERY strategy outcomes:** none were calculated by the worker or
   the subsequent synthetic diagnostic. No Stage A/B/C evaluation, candidate
   P&L, PF, t statistic, ranking, or qualification was run on real DISCOVERY.
6. **Calibrated null worlds:** deterministic generator and seeds 9001, 9002,
   9003 ran for nuisance-fit testing. Calendar and roll masks matched, and
   same-minute sign agreement error was below 0.001. The synthetic worlds did
   not satisfy all pinned nuisance tolerances. They are invalid for final
   all-null/power calibration.
7. **Executable all-null:** 0 of 200 test worlds; no false-positive or false
   validation-survivor estimate exists. The runner checkpoint status is
   `FAIL_NUISANCE_MODEL` before any Stage A reference or adaptive search.
8. **Executable planted-edge power:** 0 of 48 grid cells; no end-to-end power
   estimate exists. The 0.05/0.075/0.10/0.15 R × 100/250/500/year × four-shape
   campaign was blocked by the frozen prerequisite.
9. **Tests:** 318 collected and passed in the full suite before the freeze;
   six focused guard/null/plant/validation tests passed after final code edits
   and before the freeze. Compilation succeeded.
10. **Access ledger:** sequence 10 science freeze; 11 calibration open;
   12 NQ read; 13 ES read; 14 calibration closed with output hashes. The
   15-record ledger chain verifies. One-shot calibration state is `COMPLETE`.
11. **Sealed partitions:** zero allowed reads of VALIDATION,
    HISTORICAL_AUDIT_1, HISTORICAL_AUDIT_2, or LIVE_FORWARD. The stage remains
    DISCOVERY. The ordinary real-data preregistration guard still rejects reads.
12. **Final gate:** failed at nuisance fidelity. Across seeds 9001–9003,
    NQ/ES absolute-body correlation error was 0.160–0.161 versus ≤0.10;
    ES volume lag-one correlation error was 0.131 versus ≤0.10; ES per-clock
    volume quantile error reached 0.274 and 0.300 versus ≤0.25. No final
    calibration pass can be claimed.

The outcome-blind nuisance artifact records the worker hash, science-freeze
hash, both partition hashes, seed manifest, preserved/destroyed properties,
and exposed/hidden fields. The worker's close ledger event records both output
hashes. The failure checkpoint and full per-seed diagnostic are in
`reports/V5_EXECUTABLE_CALIBRATION.json` and `reports/V5_NUISANCE_MODEL_FIT.json`.
