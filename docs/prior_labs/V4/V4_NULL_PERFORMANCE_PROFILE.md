# V4 null-world performance audit (2026-09-24)

This change is an implementation-only optimisation. No research methodology, null count, seed, candidate,
grammar, filter, statistic, selection rule, cost or period was changed. The implementation that
produced the first 65 null worlds is tagged `v4-pre-optimization` (commit `0a3e42ca`).

## Machine

* 2 logical CPUs and 8.0 GB RAM.
* About 4.4 GB is free with no research process running, because other resident processes (Claude
  sessions, Defender, Chrome) hold the rest.
* numba runs with 2 threads.

## 1. Where the time went (old implementation)

Stage times are the means over the **65 completed worlds** (`timing_s` in each stored summary). The wall
time is the mean runner-log time per world (min 224 s, max 296 s).

| stage | old s/world | share |
|---|---|---|
| feature generation (all 14 families, triggers, filters, symbols; 15 session chunks with 125-session warm-up) | 86.6 | 34% |
| outcome tables (14 exits × 2 directions × 779k decision bars, numba) | 2.8 | 1% |
| RULE candidate evaluation (223 triggers × 721 filter combos × 6 variants × 14 exits, numba, 2 threads) | 125.9 | 49% |
| SYM candidate evaluation | 0.3 | 0% |
| ML walk-forward (3 folds × 3 feature sets × 5 targets; sklearn) | 37.4 | 15% |
| market cache, null generation, JSON summary write, overhead | ~2 | 1% |
| **wall per world** | **255.2** | |

### cProfile findings (null A seed 1000022; profiling overhead inflates absolute numbers)

* ~27 s of **numba compilation per world**. The Aroon kernel was defined *inside* a function, so it was
  recompiled on every one of the 15 feature chunks.
* Rolling max/min used an O(n·H) window scan (H up to 240): about 21 s under the profiler.
* `group_start` was recomputed on ~5,000 calls (≈ 10 s under the profiler), and `lag` compared
  full group-id arrays.
* The RULE kernel is dominated by the greedy one-position-at-a-time pass. It re-walked every
  selected event for each of the 721 × 6 × 14 candidates, including events skipped because a trade
  was already open.
* No pandas is used in the candidate hot loops. The inner engine is contiguous NumPy/numba.
  Pandas appears only in once-per-world grouping (overnight session statistics), not per candidate.

### Checks with no change needed

* **Repeated feature computation.** None. Every feature is computed once per world, and all
  candidates reference the shared trigger events, filter bits and outcome tables.
* **Null output I/O.** Already minimal. A null world writes one ~30 KB summary JSON (per-family counts,
  max t, top-500 t list and the SHA-256), which is exactly what the frozen inference (`quantlab4/v4/inference.py`)
  reads. No candidate-level null rows were ever stored. Nothing was removed.
* **World-invariant data.** Timestamps, sessions, decision bars, the candidate grammar and cost tables
  are cheap to derive per world (< 1 s). Price-dependent data must legitimately differ per world.

## 2. Changes (all verified bit-identical)

| change | file | effect |
|---|---|---|
| Aroon numba kernel moved to module level (`cache=True`) | `v4/featurelib.py` | removes ~15 recompilations per world |
| rolling max/min: O(n) monotonic deque over finite values | `v4/ops.py` | same values as the scan (tested vs brute force, including NaNs and group breaks) |
| `group_start` memoised on array identity; `lag` via position-in-group | `v4/ops.py` | same values (tested) |
| RULE kernel: per-variant contiguous event arrays and per-filter event lists (CSR); a 2-filter combo walks the shorter list | `v4/kernel.py` (`eval_trigger_bits`) | same events in the same order |
| greedy pass: galloping search to the first event at or after the exit bar | `v4/kernel.py` (`_greedy_fast`) | same trades, same order, same arithmetic |
| runner reloads the real market per world instead of caching it next to the null world | `research/run_worlds.py` | −0.4 to −0.6 GB peak for about +6 s/world |

The reference implementations (`eval_trigger_v1`, `eval_codes_v1`, `_greedy`) are kept in the code and are
used by the regression tests (`tests/test_v4_optimizations.py`, 9 tests).

## 3. Equivalence verification (mandatory)

* **Kernel level.** On a full-size DISCOVERY null world (A, seed 1000000), the output arrays of all 223
  triggers (721 × 6 × 14 × 25 stats each) and all 7 symbolic code sets were compared: identical to v1
  (`results/perf/bench_kernels_A_1000000.json`).
* **Input level.** For null world A, seed 1000002, the old code (a git worktree at `v4-pre-optimization`) and
  the new code produced **identical SHA-256** for:
  * every trigger's event positions and signs (223),
  * all ML features (72),
  * both filter-bit arrays,
  * all 7 symbol code arrays,
  * the stop scale,
  * both outcome tables (P&L and exit bars),
  * decision bars and prices.

  See `results/perf/hash_old_A2.json` and `results/perf/hash_new_A2.json`.
* **Output level.** Completed worlds were re-run with the new code, and every preregistered null output
  was compared with the stored result. For each of the 14 families this covers n_specs, n_min_trades,
  n_eligible, n_pass, max_t and the top-500 t list, plus T_G, P_G, the specification total and the
  trigger/filter/combo/decision-bar counts:

| world | result | max abs diff of family max t |
|---|---|---|
| A seed 1000000 | IDENTICAL | 0.0 |
| B seed 2000000 | IDENTICAL | 0.0 |
| C seed 3000000 | IDENTICAL | 0.0 |
| A seed 1000001 | IDENTICAL | 0.0 |

  Because the inputs and the kernel outputs are identical, every candidate's statistics, and therefore
  every eligibility/pass decision and candidate ID, are identical as well.
* **Full test suite:** 209 passed, 0 failed.

## 4. Speed and memory after optimisation

| | old | new |
|---|---|---|
| features | 86.6 s | 59.3 s |
| RULE kernel | 125.9 s | 99.8 s |
| ML | 37.4 s | 36.0 s (unchanged; sklearn, fixed hyperparameters) |
| **wall per world** | **255 s** (65 worlds) | **204 s** (4 worlds: 223, 199, 184, 211 s; includes the ~6 s reload) |
| peak working set | 3,495–3,533 MB | 3,072 MB |

The improvement is about 20%. The remaining time is inherent to the preregistered universe of
14.08M candidates evaluated trade-by-trade.

## 5. Parallelism

A second worker needs roughly 3 GB more on top of the first, while only ~4.4 GB is free with no
research process running. Two workers would push the machine into paging or out of memory, so they
were **not run**, following the rule of benchmarking only when safe. With 2 cores, the numba kernel
already uses both threads during its ~50% share of the runtime.

**Safe workers: 1.**

## 6. Expected completion

* Throughput: 3600 / 204 ≈ **17.6 worlds/hour** (1 worker).
* Completed: 65 null worlds (A 0–21, C 0–21, B 0–20) plus the real world. Remaining: **275**.
* Expected: 275 × 204 s ≈ **15.6 machine-hours = 15.6 h wall-clock** (vs 19.5 h with the old implementation).
