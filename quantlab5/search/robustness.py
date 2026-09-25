"""Robustness skeleton: parameter neighbourhoods in grammar space.

`neighbours(grammar, index)` returns the grammar indices that differ from `index` in
exactly one dimension by one step -- the basis for later plateau / sensitivity checks.
"""
from __future__ import annotations

from quantlab5.search.grammar import Grammar


def _digits(grammar: Grammar, index: int) -> list[int]:
    out = []
    rem = index
    for d in reversed(grammar.dimensions):
        rem, r = divmod(rem, len(d.values))
        out.append(r)
    return list(reversed(out))


def _index(grammar: Grammar, digits: list[int]) -> int:
    i = 0
    for d, r in zip(grammar.dimensions, digits):
        i = i * len(d.values) + r
    return i


def neighbours(grammar: Grammar, index: int) -> list[int]:
    dig = _digits(grammar, index)
    out = []
    for j, d in enumerate(grammar.dimensions):
        for step in (-1, 1):
            r = dig[j] + step
            if 0 <= r < len(d.values):
                nd = list(dig)
                nd[j] = r
                out.append(_index(grammar, nd))
    return sorted(out)
