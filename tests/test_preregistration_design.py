"""Guard assumption-only planning and superseded review-draft provenance."""
import importlib.util
import json
from pathlib import Path

from quantlab5.util.hashing import canonical_json, sha256_text


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_planning_power_declines_with_frequency_and_grows_with_design_effect():
    p = _load("planning_power", ROOT / "research" / "planning_power.py")
    assert p.mde(500, "discovery", 4.0) < p.mde(100, "discovery", 4.0)
    assert p.mde(500, "audit_2", 1.645) > p.mde(500, "audit_1", 1.645)
    assert p.mde(500, "discovery", 4.0, design_effect=2.0) > p.mde(500, "discovery", 4.0)
    assert 0.089 < p.mde(500, "discovery", 4.0) < 0.091


def test_prereg_freeze_is_self_consistent_during_revision():
    doc = json.loads((ROOT / "V5_PREREGISTRATION_FREEZE.json").read_text())
    body = {k: v for k, v in doc.items() if k != "body_sha256"}
    assert sha256_text(canonical_json(body)) == doc["body_sha256"]
    assert doc["status"] in ("REVIEW_REQUIRED", "FINAL")
    if doc["status"] == "REVIEW_REQUIRED":
        assert doc["discovery_search_authorized"] is False
