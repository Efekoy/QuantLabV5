"""Canonical serialisation and hashing (adapted from quantlab3.config).

`canonical_json` is the single serialisation used for every hash in V4: ledger
records, freeze manifests, candidate IDs and configuration fingerprints. It is
deliberately strict so that the same logical content always produces the same
bytes:

  * keys sorted, no whitespace, UTF-8, ASCII-escaped
  * tuples -> lists; numpy scalars/arrays -> Python values/lists
  * -0.0 -> 0.0; NaN / +-inf are REJECTED (they have no stable JSON form)
  * sets, bytes and arbitrary objects are REJECTED rather than str()-ed
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime
from pathlib import Path

import numpy as np


class CanonicalError(TypeError):
    """A value has no canonical JSON form."""


def _norm(o):
    if o is None or isinstance(o, (bool, str)):
        return o
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        f = float(o)
        if not math.isfinite(f):
            raise CanonicalError(f"non-finite float {f!r} cannot be canonicalised")
        return 0.0 if f == 0.0 else f
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if not isinstance(k, str):
                raise CanonicalError(f"dict key {k!r} is not a string")
            out[k] = _norm(v)
        return out
    if isinstance(o, (list, tuple)):
        return [_norm(x) for x in o]
    if isinstance(o, np.ndarray):
        return [_norm(x) for x in o.tolist()]
    if isinstance(o, datetime):
        return o.isoformat()
    if isinstance(o, date):
        return o.isoformat()
    if isinstance(o, Path):
        return str(o)
    raise CanonicalError(f"type {type(o).__name__} has no canonical JSON form")


def canonical_json(obj) -> str:
    return json.dumps(_norm(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_obj(obj) -> str:
    return sha256_text(canonical_json(obj))


def file_sha256(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()
