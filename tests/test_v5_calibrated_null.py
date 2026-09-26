"""Protocol guard and nuisance-only synthetic market generator checks."""
from datetime import date
import json
from types import SimpleNamespace

import numpy as np

from quantlab5.isolation.calibration_gate import science_freeze_ready
from quantlab5.data.market import build_market
from quantlab5.engine.costs import CostModel
from quantlab5.synthetic.markets import correlated_pair, weekdays
from quantlab5.util.hashing import file_sha256
from quantlab5.v5.calibrated_null import CalibratedZeroEdgeWorlds
from quantlab5.v5.market_search import adaptive_search
from research.calibrate_v5_discovery_nuisance import _joint_sign_agreement, _summarize
from research.check_v5_nuisance_fit import diagnose


def test_science_gate_fails_closed_without_freeze(tmp_path):
    ok, reason = science_freeze_ready(tmp_path)
    assert not ok and "missing" in reason


def test_calibrated_zero_edge_world_uses_only_nuisance_artifact(tmp_path):
    nq, es = correlated_pair(weekdays(date(2020, 1, 2), date(2020, 2, 13)))

    # _summarize takes a pandas-like symbol Series, as load_view supplies.
    import pandas as pd
    def md(bars):
        return SimpleNamespace(bars=lambda: bars,
                               frame={"symbol": pd.Series(np.full(bars.n, bars.instrument + "Z0"))})

    nq_summary, nq_template = _summarize(md(nq))
    es_summary, es_template = _summarize(md(es))
    template = tmp_path / "template.npz"
    np.savez_compressed(template, nq_ts=nq_template["ts"], nq_segment=nq_template["segment"],
                        es_ts=es_template["ts"], es_segment=es_template["segment"])
    artifact = tmp_path / "calibration.json"
    artifact.write_text(json.dumps({
        "kind": "V5_DISCOVERY_NUISANCE_CALIBRATION", "status": "COMPLETE",
        "calendar_template_sha256": file_sha256(template),
        "NQ": nq_summary, "ES": es_summary,
        "joint": _joint_sign_agreement(md(nq), md(es)),
    }))
    generator = CalibratedZeroEdgeWorlds(artifact, template)
    a = generator.generate_seed(123)
    b = generator.generate_seed(123)
    assert np.array_equal(a["NQ"].c, b["NQ"].c)
    assert np.array_equal(a["ES"].c, b["ES"].c)
    assert np.array_equal(a["NQ"].ts, nq.ts)
    assert np.array_equal(a["ES"].ts, es.ts)
    assert not np.array_equal(a["NQ"].c, nq.c)
    assert np.all(a["NQ"].l > 0) and np.all(a["ES"].l > 0)
    import yaml
    from quantlab5.project import ROOT
    costs = CostModel(yaml.safe_load((ROOT / "config/costs.yaml").read_text()), "test")
    market = build_market(a["NQ"], a["ES"],
                          np.full(a["NQ"].n, "NQS1"), np.full(a["ES"].n, "ESS1"))
    trace = adaptive_search(market, costs, np.full((19, 30), 100.0))
    assert len(trace.records) == 60


def test_frozen_nuisance_fit_thresholds_on_seeded_fixture(tmp_path):
    import pandas as pd
    nq, es = correlated_pair(weekdays(date(2020, 1, 2), date(2020, 12, 31)))
    def md(bars):
        return SimpleNamespace(bars=lambda: bars,
                               frame={"symbol": pd.Series(np.full(bars.n, bars.instrument + "Z0"))})
    nq_summary, nq_template = _summarize(md(nq))
    es_summary, es_template = _summarize(md(es))
    template = tmp_path / "template.npz"
    np.savez_compressed(template, nq_ts=nq_template["ts"], nq_segment=nq_template["segment"],
                        es_ts=es_template["ts"], es_segment=es_template["segment"])
    artifact = tmp_path / "calibration.json"
    artifact.write_text(json.dumps({
        "kind": "V5_DISCOVERY_NUISANCE_CALIBRATION", "status": "COMPLETE",
        "calendar_template_sha256": file_sha256(template),
        "NQ": nq_summary, "ES": es_summary,
        "joint": _joint_sign_agreement(md(nq), md(es)),
    }))
    report = diagnose(CalibratedZeroEdgeWorlds(artifact, template), 9001)
    assert report["pass"], report
