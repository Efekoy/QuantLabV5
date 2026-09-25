"""Tamper-evident manifests and canonical hashing."""
import json
import os
import stat

import pytest

from quantlab5.isolation.manifests import ManifestError, build_manifest, verify_manifest, write_manifest
from quantlab5.util.hashing import canonical_json, sha256_obj


def test_manifest_verifies_and_detects_body_and_file_tampering(tmp_path):
    (tmp_path / "a.txt").write_text("alpha")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("beta")
    doc = build_manifest("TEST_FREEZE", {"x": [1, 2]}, tmp_path, ["a.txt", "sub/b.txt"])
    m = tmp_path / "M.json"
    sha = write_manifest(m, doc)
    assert verify_manifest(m, tmp_path, "TEST_FREEZE") == sha
    with pytest.raises(ManifestError):
        write_manifest(m, doc)                                   # write-once
    with pytest.raises(ManifestError, match="kind"):
        verify_manifest(m, tmp_path, "OTHER")
    (tmp_path / "sub" / "b.txt").write_text("beta!")
    with pytest.raises(ManifestError, match="changed"):
        verify_manifest(m, tmp_path)
    (tmp_path / "sub" / "b.txt").write_text("beta")
    os.chmod(m, stat.S_IWRITE | stat.S_IREAD)
    d = json.loads(m.read_text())
    d["sections"]["x"].append(3)
    m.write_text(json.dumps(d))
    with pytest.raises(ManifestError, match="edited"):
        verify_manifest(m, tmp_path)


def test_required_sections_are_enforced(tmp_path):
    doc = build_manifest("F", {"cohort": ["a"], "parameters": {}}, tmp_path)
    m = tmp_path / "F.json"
    write_manifest(m, doc)
    verify_manifest(m, tmp_path, required_sections=["cohort"])
    with pytest.raises(ManifestError, match="parameters"):
        verify_manifest(m, tmp_path, required_sections=["cohort", "parameters"])


def test_canonical_json_is_order_and_type_stable():
    import numpy as np
    assert canonical_json({"b": 1, "a": 2}) == canonical_json({"a": 2, "b": 1})
    assert canonical_json({"x": np.int64(3), "y": np.float64(0.5), "z": np.array([1, 2])}) == \
        '{"x":3,"y":0.5,"z":[1,2]}'
    assert sha256_obj([1, 2]) != sha256_obj([2, 1])
