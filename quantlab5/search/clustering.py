"""Clustering skeleton: group candidates whose daily P&L streams are near-duplicates.

Greedy, deterministic: candidates are visited in the given order; each joins the
first existing cluster whose representative it correlates with at >= threshold,
else starts a new cluster. Order is part of the input, so results are reproducible.

V5 rule (added): clustering only ANNOTATES behavioural duplicates. `duplicate_annotations` turns clusters
into a {member: representative} map for the discovery freeze's `duplicate_of` section; every member stays
a candidate and advances to later testing. Nothing here removes a candidate.
"""
from __future__ import annotations

import numpy as np


def correlation_clusters(streams: dict[str, np.ndarray], threshold: float = 0.9) -> dict[str, list[str]]:
    reps: list[tuple[str, np.ndarray]] = []
    clusters: dict[str, list[str]] = {}
    for cid, x in streams.items():
        x = np.asarray(x, dtype=np.float64)
        placed = False
        for rid, rx in reps:
            if x.std() > 0 and rx.std() > 0 and np.corrcoef(x, rx)[0, 1] >= threshold:
                clusters[rid].append(cid)
                placed = True
                break
        if not placed:
            reps.append((cid, x))
            clusters[cid] = [cid]
    return clusters


def duplicate_annotations(clusters: dict[str, list[str]]) -> dict[str, str]:
    """{member: representative} for every non-representative member. Annotation only -- nobody is dropped."""
    return {m: rep for rep, members in clusters.items() for m in members if m != rep}
