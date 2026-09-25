"""Deterministic candidate enumeration.

Same grammar + same seed + same configuration  ->  identical candidate IDs in
identical order, on any machine, in any number of shards.

  order "lexicographic":       grammar index order 0..size-1
  order "seeded_permutation":  a permutation of 0..size-1 from numpy's PCG64 seeded
                               with (seed, grammar definition hash) -- reproducible,
                               and independent of how the work is sharded.

Shards are contiguous slices of the ordered index list, so the union of all shards
is exactly the full enumeration. Duplicate IDs raise immediately.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterator

import numpy as np

from quantlab5.search.candidate_id import IdScheme, candidate_id
from quantlab5.search.grammar import Grammar
from quantlab5.util.hashing import canonical_json, sha256_text


class DuplicateCandidateError(Exception):
    pass


@dataclass(frozen=True)
class Candidate:
    ordinal: int          # position in this enumeration (after constraint filtering)
    grammar_index: int    # mixed-radix index in the grammar
    candidate_id: str
    spec: dict


def enumeration_order(grammar: Grammar, order: str = "lexicographic", seed: int = 0) -> np.ndarray:
    n = grammar.size
    if order == "lexicographic":
        return np.arange(n, dtype=np.int64)
    if order == "seeded_permutation":
        mix = int(sha256_text(canonical_json([int(seed), grammar.definition_hash()]))[:16], 16)
        return np.random.Generator(np.random.PCG64(mix)).permutation(n).astype(np.int64)
    raise ValueError(f"unknown order {order!r}")


def enumerate_candidates(grammar: Grammar, order: str = "lexicographic", seed: int = 0,
                         scheme: IdScheme = IdScheme(), shard: tuple[int, int] = (0, 1),
                         check_duplicates: bool = True) -> Iterator[Candidate]:
    k, n_shards = shard
    if not 0 <= k < n_shards:
        raise ValueError("bad shard")
    idx = enumeration_order(grammar, order, seed)
    bounds = np.linspace(0, len(idx), n_shards + 1).astype(np.int64)
    seen: set[str] = set()
    ordinal = 0
    for pos in range(len(idx)):
        gi = int(idx[pos])
        spec = grammar.spec_at(gi)
        if not grammar.is_valid(spec):
            continue
        in_shard = bounds[k] <= pos < bounds[k + 1]
        if in_shard:
            cid = candidate_id(spec, scheme)
            if check_duplicates:
                if cid in seen:
                    raise DuplicateCandidateError(f"duplicate candidate id {cid} at grammar index {gi}")
                seen.add(cid)
            yield Candidate(ordinal, gi, cid, spec)
        ordinal += 1


def enumeration_fingerprint(cands) -> str:
    """Hash of the ordered ID list -- two runs are identical iff fingerprints match."""
    h = hashlib.sha256()
    for c in cands:
        h.update(c.candidate_id.encode())
        h.update(b"\n")
    return h.hexdigest()
