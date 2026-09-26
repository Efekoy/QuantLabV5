import json
import subprocess

from quantlab5.isolation.prereg_gate import prereg_ready
from quantlab5.project import ROOT
from quantlab5.util.hashing import canonical_json, file_sha256, sha256_text


def test_actual_research_data_access_fails_closed_before_final_tag():
    ok, reason = prereg_ready(ROOT)
    import subprocess
    tag = subprocess.run(["git", "tag", "--list", "v5-prereg"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    if tag:
        assert ok, reason
    else:
        assert not ok
        assert "FINAL" in reason or "tag" in reason or "missing" in reason


def test_tag_must_contain_exact_final_freeze_and_pinned_bytes(tmp_path):
    required = ["quantlab5/v5/signals.py", "quantlab5/v5/market_search.py",
                "quantlab5/v5/candidate_inventory.py", "config/stage_policy.yaml",
                "config/costs.yaml", "V5_RESEARCH_PREREGISTRATION.md"]
    for name in required:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name, encoding="utf-8")
    body = {"kind": "V5_FINAL_PREREGISTRATION", "status": "FINAL",
            "files_sha256": {name: file_sha256(tmp_path / name) for name in required}}
    doc = {**body, "body_sha256": sha256_text(canonical_json(body))}
    (tmp_path / "V5_PREREGISTRATION_FREEZE.json").write_text(
        json.dumps(doc, sort_keys=True) + "\n", encoding="utf-8")
    run = lambda *args: subprocess.run(["git", *args], cwd=tmp_path, check=True,
                                       capture_output=True)
    run("init", "-q")
    run("add", ".")
    run("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
        "commit", "-q", "-m", "synthetic prereg test")
    run("tag", "v5-prereg")
    assert prereg_ready(tmp_path)[0]
    (tmp_path / required[0]).write_text("tampered", encoding="utf-8")
    assert not prereg_ready(tmp_path)[0]
