"""Research decision log is hash-chained; resume state records output hashes."""
import json

from quantlab5 import research_log as RL
from quantlab5.isolation import ledger


def test_decision_log_is_chained_and_tamper_evident(fresh_project):
    p = fresh_project
    RL.log(p, "DECISION", "use per-minute sign-flip null", null="A")
    RL.log(p, "POST_HOC", "exploratory plot", note="does not change cohort")
    path = RL.log_path(p)
    recs = ledger.read(path)
    assert [r["event"] for r in recs] == ["DECISION", "POST_HOC"] and recs[0]["stage"] == "DISCOVERY"
    assert ledger.verify(path)[0]
    lines = path.read_text().splitlines()
    r = json.loads(lines[0])
    r["reason"] = "rewritten"
    lines[0] = json.dumps(r)
    path.write_text("\n".join(lines) + "\n")
    assert not ledger.verify(path)[0]


def test_resume_state_tracks_outputs(fresh_project):
    p = fresh_project
    (p.root / "results").mkdir(exist_ok=True)
    f = p.root / "results" / "x.json"
    f.write_text("{}")
    st = RL.mark_done(p, "step1", {"results/x.json": ""}, next_action="step2")
    assert st["completed"] == ["step1"] and st["next_action"] == "step2" and st["stage"] == "DISCOVERY"
    assert RL.verify_outputs(p) == {"results/x.json": True}
    f.write_text("{changed}")
    assert RL.verify_outputs(p) == {"results/x.json": False}
