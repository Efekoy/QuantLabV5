"""Tamper-evident manifests (freezes, partition registry, provenance).

(Adapted from quantlab3/freeze/hashing.py; the V3 freeze *contents* were not copied.)

A manifest is a JSON document:

    {"kind": ..., "created_utc": ..., "sections": {...}, "files": {relpath: sha256},
     "ledger_anchor": {"seq", "record_hash"} | null, "git_commit": ... | null,
     "body_sha256": SHA-256 of canonical_json(everything except body_sha256)}

`verify_manifest` recomputes the body hash AND the hash of every listed file, so
changing either the manifest or anything it pins is detected. Manifests are written
once (never overwritten) and set read-only.
"""
from __future__ import annotations

import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path

from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text


class ManifestError(Exception):
    """A manifest is missing, malformed or does not verify."""


def body_hash(doc: dict) -> str:
    return sha256_text(canonical_json({k: v for k, v in doc.items() if k != "body_sha256"}))


def make_read_only(path: Path) -> None:
    try:
        os.chmod(path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
    except OSError:
        pass


def make_writable(path: Path) -> None:
    try:
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
    except OSError:
        pass


def hash_files(root: Path, rel_paths) -> dict[str, str]:
    out = {}
    for rel in sorted(set(str(r).replace("\\", "/") for r in rel_paths)):
        p = root / rel
        if not p.is_file():
            raise ManifestError(f"cannot hash {rel}: not a file")
        out[rel] = file_sha256(p)
    return out


def build_manifest(kind: str, sections: dict, root: Path, files=(), ledger_anchor: dict | None = None,
                   git_commit: str | None = None, created_utc: str | None = None) -> dict:
    doc = {"kind": kind, "created_utc": created_utc or datetime.now(timezone.utc).isoformat(),
           "sections": sections, "files": hash_files(root, files), "ledger_anchor": ledger_anchor,
           "git_commit": git_commit}
    doc["body_sha256"] = body_hash(doc)
    return doc


def write_manifest(path: Path, doc: dict, overwrite: bool = False) -> str:
    path = Path(path)
    if path.exists() and not overwrite:
        raise ManifestError(f"{path} already exists; manifests are written once")
    if path.exists():
        make_writable(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1, sort_keys=True), encoding="utf-8")
    make_read_only(path)
    return doc["body_sha256"]


def verify_manifest(path: Path, root: Path, kind: str | None = None,
                    required_sections=()) -> str:
    """Return the manifest's body hash if it verifies, else raise ManifestError."""
    path = Path(path)
    if not path.is_file():
        raise ManifestError(f"{path.name} does not exist")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ManifestError(f"{path.name} is not valid JSON: {e}") from e
    if kind is not None and doc.get("kind") != kind:
        raise ManifestError(f"{path.name}: kind {doc.get('kind')!r}, expected {kind!r}")
    if body_hash(doc) != doc.get("body_sha256"):
        raise ManifestError(f"{path.name}: body hash mismatch -- the manifest was edited")
    for rel, sha in (doc.get("files") or {}).items():
        p = Path(root) / rel
        if not p.is_file():
            raise ManifestError(f"{path.name}: pinned file {rel} is missing")
        if file_sha256(p) != sha:
            raise ManifestError(f"{path.name}: pinned file {rel} changed since the manifest was written")
    for sec in required_sections:
        val = (doc.get("sections") or {}).get(sec)
        if val in (None, "", [], {}):
            raise ManifestError(f"{path.name}: required section {sec!r} is missing or empty")
    return doc["body_sha256"]


def read_manifest(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
