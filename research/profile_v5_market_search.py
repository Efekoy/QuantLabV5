"""Profile a seeded synthetic Stage A search without reading real partitions."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
from pathlib import Path
from time import perf_counter

import numpy as np
import yaml

from quantlab5.data.market import build_market
from quantlab5.engine.costs import CostModel
from quantlab5.synthetic.markets import correlated_pair, weekdays
from quantlab5.v5.market_search import adaptive_search, evaluate_spec


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--end", default="2020-03-31")
    args = parser.parse_args()
    nq, es = correlated_pair(weekdays(date(2020, 1, 2), date.fromisoformat(args.end)))
    market = build_market(nq, es, np.full(nq.n, "NQZ0"), np.full(es.n, "ESZ0"))
    cfg = yaml.safe_load((Path(__file__).resolve().parents[1] / "config/costs.yaml").read_text())
    costs = CostModel(cfg, "profile")
    by_family = defaultdict(float)

    def timed_evaluator(world, spec, context, cost_model, *, shadow_baseline):
        start = perf_counter()
        result = evaluate_spec(world, spec, context, cost_model,
                               shadow_baseline=shadow_baseline)
        by_family[spec["family"]] += perf_counter() - start
        return result

    start = perf_counter()
    trace = adaptive_search(market, costs, np.full((19, 30), 100.0),
                            evaluator=timed_evaluator)
    elapsed = perf_counter() - start
    print(f"bars={market.n} records={len(trace.records)} elapsed={elapsed:.3f}s "
          f"evaluate={sum(by_family.values()):.3f}s other={elapsed-sum(by_family.values()):.3f}s")
    for family, seconds in sorted(by_family.items(), key=lambda row: -row[1]):
        print(f"{family} {seconds:.3f}s")


if __name__ == "__main__":
    main()
