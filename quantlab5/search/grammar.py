"""A generic, deterministic specification grammar (NO V4 strategy grammar yet).

A Grammar is an ordered list of named dimensions, each with an ordered list of
admissible values, plus optional named constraints. The space is the Cartesian
product, indexed in mixed radix (last dimension fastest), so:

  * `size` is exact without enumerating;
  * `spec_at(i)` builds the i-th specification directly (random access -> sharding);
  * enumeration order is fully determined by the grammar definition.

Constraints are predicates over a spec; an invalid spec is skipped, never silently
replaced. Dimension values must be canonical-JSON-serialisable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from quantlab5.util.hashing import canonical_json, sha256_text


@dataclass(frozen=True)
class Dimension:
    name: str
    values: tuple

    def __post_init__(self):
        if not self.values:
            raise ValueError(f"dimension {self.name} has no values")
        keys = [canonical_json(v) for v in self.values]
        if len(set(keys)) != len(keys):
            raise ValueError(f"dimension {self.name} has duplicate values")


@dataclass
class Grammar:
    name: str
    version: str
    dimensions: list[Dimension]
    constants: dict = field(default_factory=dict)
    constraints: dict[str, Callable[[dict], bool]] = field(default_factory=dict)

    def __post_init__(self):
        names = [d.name for d in self.dimensions]
        if len(set(names)) != len(names):
            raise ValueError("duplicate dimension names")
        overlap = set(names) & set(self.constants)
        if overlap:
            raise ValueError(f"constants overlap dimensions: {overlap}")

    @property
    def size(self) -> int:
        n = 1
        for d in self.dimensions:
            n *= len(d.values)
        return n

    def spec_at(self, index: int) -> dict:
        if not 0 <= index < self.size:
            raise IndexError(index)
        spec = {"grammar": self.name, "grammar_version": self.version, **self.constants}
        rem = index
        picks = []
        for d in reversed(self.dimensions):
            rem, r = divmod(rem, len(d.values))
            picks.append((d.name, d.values[r]))
        for name, val in reversed(picks):
            spec[name] = val
        return spec

    def is_valid(self, spec: dict) -> bool:
        return all(pred(spec) for _name, pred in sorted(self.constraints.items()))

    def definition_hash(self) -> str:
        """Hash of the grammar definition (constraint NAMES only; code is hashed by the freeze)."""
        return sha256_text(canonical_json({"name": self.name, "version": self.version,
                                           "dimensions": [[d.name, list(d.values)] for d in self.dimensions],
                                           "constants": self.constants,
                                           "constraints": sorted(self.constraints)}))
