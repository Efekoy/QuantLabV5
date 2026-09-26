"""Synthetic-only timing of the actual V5.4 sparse management evaluator."""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

import numpy as np

from quantlab5.v54.engine import evaluate
from quantlab5.v54.events import Events
from quantlab5.v54.universe import counts, managements


def main():
    n = 6000
    o = np.full(n, 100.)
    h = np.full(n, 100.25)
    l = np.full(n, 99.75)
    c = np.full(n, 100.)
    sm = np.arange(n, dtype=np.int16) % 1440
    bars = SimpleNamespace(n=n, o=o, h=h, l=l, c=c, sm=sm,
                           tmin=np.arange(n, dtype=np.int64))
    years = np.full(n, 2012, np.int32)
    market = SimpleNamespace(nq=bars, years=lambda: years)
    flat = np.zeros(n, bool)
    flat[-1] = True
    entries = np.arange(2, n-65, 50, dtype=np.int32)
    events = Events(entries, np.ones(len(entries), np.int8),
                    np.ones(len(entries)), flat, "E03", {},
                    np.ones(n, np.int8), years)
    management = next(m.as_dict() for m in managements()
                      if m.template == "T10_TIME_EXIT" and m.hold == 60)
    # Warm the JIT outside timed segments.
    reference = evaluate(market, events, management,
                         baseline_cost_points=.1, stress_cost_points=.2)[0]
    checkpoints = (10_000, 100_000, 1_000_000)
    done = 0
    elapsed = 0.0
    rows = []
    for target in checkpoints:
        start = perf_counter()
        for _ in range(target-done):
            result = evaluate(market, events, management,
                              baseline_cost_points=.1, stress_cost_points=.2)[0]
        elapsed += perf_counter()-start
        if not np.array_equal(reference, result, equal_nan=True):
            raise AssertionError("synthetic benchmark changed deterministic metrics")
        rows.append({"specifications": target, "elapsed_seconds": elapsed,
                     "specifications_per_second": target/elapsed})
        print(rows[-1], flush=True)
        done = target
    scale = counts()["total_specs"] / 1_000_000
    doc = {"kind": "V5_4_SYNTHETIC_ENGINE_BENCHMARK",
           "fixture": {"bars": n, "eligible_entry_events": len(entries),
                       "management": management,
                       "note": "Management-kernel timing only; full-world feature, storage and IO costs require separate allowance."},
           "measurements": rows,
           "estimated_10m_seconds_at_1m_rate": 10_000_000/rows[-1]["specifications_per_second"],
           "estimated_full_universe_seconds_at_1m_rate": elapsed*scale}
    out = Path("reports/V5_4_ENGINE_BENCHMARK.json")
    out.write_text(json.dumps(doc, indent=2, sort_keys=True)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
