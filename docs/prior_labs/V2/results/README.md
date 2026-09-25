# results/

One folder per experiment (the `experiment:` name in the config):

```
results/<experiment>/
  discovery/
    RUN_MANIFEST.json        what ran, under which code / costs / data
    DISCOVERY_STATUS.json    counts
    parts/specs/*.parquet    EVERY tested specification (one row each)
    parts/trades/*.parquet   trades of baseline-profitable specs
    parts/yearly/*.parquet   year matrix of baseline-profitable specs
  frozen/                    immutable once written (read-only files)
    FREEZE_MANIFEST.json + .sha256
    candidates.parquet       the official cohort (one row per unique trade list)
    aliases.parquet          every equivalent profitable spec -> canonical candidate
    yearly_discovery.parquet
  robustness/neighborhood.parquet
  stages/<year>/             one folder per opened unseen year
    STAGE_MANIFEST.json, results.parquet (incl. failures), trades.parquet
  postmortem/<year>/         NOT official
  reports/index.html         dashboard; reports/candidates/<id>.html
```

`main` is the official experiment. `smoke` and `smoke_synthetic` come from the
smoke test and mean nothing.
