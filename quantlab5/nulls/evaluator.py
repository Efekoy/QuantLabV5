"""Null-world runner. It has NO evaluator of its own.

Every null world is generated as ordinary Bars and passed to
`quantlab5.search.pipeline.evaluate_candidates` -- the same function, called the same
way, as for real data. (Referenced through the module so tests can prove it.)
"""
from __future__ import annotations

import numpy as np

from quantlab5.nulls.base import NullGenerator
from quantlab5.search import pipeline


def run_null_worlds(market: dict, candidates, build_signals, ctx, generator: NullGenerator, seeds) -> list[dict]:
    cands = list(candidates)
    worlds = []
    for seed in seeds:
        world = generator.generate(market, int(seed))
        for k, b in world.items():
            src = market[k]
            if (b.n != src.n or not np.array_equal(b.ts, src.ts) or not np.array_equal(b.seg, src.seg)
                    or not np.array_equal(b.sday, src.sday)):
                raise AssertionError(f"null generator {generator.name} changed timestamps/sessions/segments")
        results = pipeline.evaluate_candidates(world, cands, build_signals, ctx)
        worlds.append({"seed": int(seed), "generator": generator.name, "params": generator.params(),
                       "results": results})
    return worlds
