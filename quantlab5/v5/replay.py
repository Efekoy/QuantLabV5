"""Replay a hierarchical search on each market-level surrogate world.

Selection is deliberately called *inside* the world loop. Passing candidates
selected on the real market into this function would invalidate adaptive-search
calibration and is not part of this API.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ReplayResult:
    seed: int
    selected_ids: tuple[str, ...]
    global_statistic: float
    family_statistics: dict[str, float]


def replay_search(market: dict, generator, seeds,
                  search: Callable[[dict], tuple[object, object]]) -> list[ReplayResult]:
    """Run full A→B→C `search(world)` separately on every generated market.

    `search` must return (candidate_records, family_statistics), where each record
    has `candidate_id`, `stage`, and `statistic`. This engine does not prescribe
    the feature library or candidate-selection rule; those must be frozen and
    independently tested before results can be interpreted.
    """
    out = []
    for seed in seeds:
        world = generator.generate(market, int(seed))
        records, fam = search(world)
        ids = [r.candidate_id for r in records]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate candidate ID in replayed search")
        if not all(r.stage in ("A", "B", "C") for r in records):
            raise ValueError("unknown hierarchical stage")
        stats = {str(k): float(v) for k, v in fam.items()}
        out.append(ReplayResult(int(seed), tuple(ids), max(stats.values(), default=float("-inf")), stats))
    return out
