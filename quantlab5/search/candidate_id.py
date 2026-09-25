"""Content-derived candidate IDs.

A candidate ID is a pure function of the CANONICALISED specification -- never of its
position in a list, the enumeration order, the machine, or the time. Two specs with
the same content get the same ID; any change of content changes the ID.

    id = "<prefix>-" + SHA-256(canonical_json({"namespace": ns, "spec": spec}))[:hex_chars]

`canonical_json` sorts keys, normalises -0.0, rejects NaN/inf/sets/objects, so
logically equal specs always serialise identically.

(Ported from QuantLabV4. V5 change: default prefix Q5 / namespace quantlab5 -- the same spec therefore gets
a different ID in V5 than in V4, by design; regression-tested in tests/test_v5_bootstrap.py.)
"""
from __future__ import annotations

from dataclasses import dataclass

from quantlab5.util.hashing import canonical_json, sha256_text


@dataclass(frozen=True)
class IdScheme:
    prefix: str = "Q5"
    hex_chars: int = 24
    namespace: str = "quantlab5"

    @classmethod
    def from_config(cls, cfg: dict) -> "IdScheme":
        c = cfg.get("candidate_id", {})
        return cls(c.get("prefix", "Q5"), int(c.get("hex_chars", 24)), c.get("namespace", "quantlab5"))


def serialize_spec(spec: dict) -> str:
    if not isinstance(spec, dict):
        raise TypeError("a candidate specification must be a dict")
    return canonical_json(spec)


def candidate_id(spec: dict, scheme: IdScheme = IdScheme()) -> str:
    body = canonical_json({"namespace": scheme.namespace, "spec": spec})
    return f"{scheme.prefix}-{sha256_text(body)[:scheme.hex_chars]}"
