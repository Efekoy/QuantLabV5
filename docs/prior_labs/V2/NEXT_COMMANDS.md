# What to do next, in order

Run everything from the project folder:

```bash
cd ~/Desktop/QuantLabV2
```

## 0. Make the first commit (once)

Git is initialised and every file is staged, but no global git identity is
configured on this machine, so nothing was committed. Official runs record the
commit hash, so commit **before** discovery:

```bash
git config --global user.name "Your Name"
```

```bash
git config --global user.email "you@example.com"
```

```bash
git add -A && git commit -m "QuantLabV2 initial engine"
```

## 1. Confirm the data paths

Open `config/data_paths.yaml`. It currently points, read-only, at:

- `C:/Users/Administrator/Desktop/Quant/data/NQ/nq_continuous_front_1m.parquet`
- `C:/Users/Administrator/Desktop/Quant/data/ES/es_continuous_front_1m.parquet`

## 2. Confirm the costs (important: they are placeholders)

Open `config/costs.yaml`. The defaults are full-size E-minis (NQ $20/pt, ES
$50/pt), **$4.00 commission per round trip and 1 tick of slippage per side**,
which gives a baseline of $14.00 (NQ) and $29.00 (ES) per round trip. Put in your
real numbers, and change `version:` to a label of your own (for example
`costs_v1_my_broker`). **After the freeze, costs cannot change** for the rest of
the official experiment.

## 3. Run the doctor

```bash
python -m quantlab doctor --tests
```

Everything should be `OK`, apart from the placeholder-cost warning until you
rename the cost version.

## 4. Run the test suite on its own (optional, already part of step 3)

```bash
python -m pytest
```

## 5. Run the smoke campaign

It uses NQ 2017–2018 for discovery, with 2019 and 2020 standing in for unseen
years. All of that is **inside** the official discovery period, so no 2021+ year
is spent.

```bash
python -m quantlab smoke
```

## 6. Inspect the smoke report

Open `results/smoke/reports/index.html` in a browser. Click a candidate. Check
the plain-English rules and the year matrix. Then try:

```bash
python -m quantlab --config config/smoke.yaml status
```

## 7. Inspect the search-space size (and trim or extend grids if you want)

```bash
python -m quantlab space
```

It currently shows **5,732 entries**, **150 managed templates + 9 plain exits**,
**Stage A = 87,888 candidates**, and a **Stage B upper bound of 2,926,164**
(reached only if every entry qualified). Entry grids live in
`config/search_space.yaml`. Stops, templates and the two stages live in
`config/management.yaml`. **Change them now or never:** after discovery starts,
a changed configuration refuses to mix with existing results.

## 8. Only then: launch the full 2010–2020 discovery, Stage A

```bash
python -m quantlab discover --stage A --yes
```

This takes roughly 10–20 minutes on this machine and resumes if interrupted
(run the same command again).

## 8b. Stage B (expanded trade management, still 2010–2020 only)

First run it without `--yes`. It applies the pre-declared rule to the Stage A
results and prints how many entries qualify and exactly how many specifications
Stage B will run:

```bash
python -m quantlab discover --stage B
```

Then launch it. This can take a few hours in the worst case, and it resumes if
interrupted:

```bash
python -m quantlab discover --stage B --yes
```

Check the state at any time with:

```bash
python -m quantlab status
```

Optionally, preview the profitable population before freezing:

```bash
python -m quantlab report --details 100
```

## 9. Freeze the profitable cohort

```bash
python -m quantlab freeze
```

This happens once, after Stage A **and** Stage B are complete. It also computes
the entry and management neighbourhoods, the breakeven counterfactuals and the
cross-instrument transfer, all on discovery data. It writes
`results/main/frozen/` and cannot be repeated or overwritten. Consider committing the small frozen manifest:

```bash
git add -f results/main/frozen/FREEZE_MANIFEST.json results/main/frozen/FREEZE_MANIFEST.sha256 && git commit -m "Freeze discovery cohort"
```

## 10. Validate 2021

```bash
python -m quantlab validate --year 2021
```

## 11. Continue sequentially, one year at a time

```bash
python -m quantlab validate --year 2022
```

```bash
python -m quantlab validate --year 2023
```

```bash
python -m quantlab validate --year 2024
```

```bash
python -m quantlab validate --year 2025
```

```bash
python -m quantlab validate --year 2026
```

After each stage:

```bash
python -m quantlab report
```

To read one candidate:

```bash
python -m quantlab describe C0123456789abcdef
```

## 12. Only after the official sequence: postmortems (not official)

```bash
python -m quantlab postmortem --year 2021
```

## After the official experiment (completed 2026-09-22)

```
python -m quantlab audit final          # FINAL_DATA_ACCESS_AUDIT.md from the ledger
python -m quantlab final-report         # results/main/reports/final/index.html + tables/
python tools/check_stage.py 2021        # independent invariant check of one stage
python tools/final_integrity.py "82 passed, 0 failed"   # FINAL_INTEGRITY_CHECK.md
```

## Archive and null funnel (2026-09-22)

```
python tools/archive_official.py                 # results/archive/OFFICIAL_EXPERIMENT_2026-09-22 (written once; refuses to overwrite)
python tools/null_control_real.py                # null evaluator must reproduce the official funnel on real data
python -m quantlab.nullfunnel.run diagnose       # generator diagnostics (STOP if any check fails)
python -m quantlab.nullfunnel.run worlds 2       # all null worlds, checkpointed/resumable
python tools/null_audit.py "87 passed, 0 failed" # null data-access audit + official integrity
python -m quantlab.nullfunnel.analysis           # NULL_FUNNEL_REPORT.md, reports/index.html, tables/
```

## Edge isolation (2026-09-22) -- analysis only, no selection

```
python tools/edge_integrity.py start "<pytest line>"   # snapshot + checks (STOP on failure)
python -m quantlab.edge.nullmap 2                       # regenerate + cluster every null world (exact-reproduction checked)
python -m quantlab.edge.real                            # real survivors: daily P&L / entry overlap clustering
python -m quantlab.edge.analysis                        # EDGE_ISOLATION_REPORT.md, cluster_summary.*, tables/
python tools/edge_integrity.py end "<pytest line>"
```
The final-selection rule (results/edge_isolation/PROPOSED_FINAL_SELECTION_RULE.md) is NOT executed.
