"""Guard the assumption-only planning report and review-draft byte pin."""
import importlib.util
from pathlib import Path


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


def test_review_draft_freeze_verifies_without_stage_transition():
    f = _load("freeze_prereg_design", ROOT / "research" / "freeze_prereg_design.py")
    assert f.verify()
    assert f.build()["status"] == "REVIEW_REQUIRED"
    assert f.build()["discovery_search_authorized"] is False
