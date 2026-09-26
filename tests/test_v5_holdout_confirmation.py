"""Fixed-candidate validation behavior under the revised inference design."""
import numpy as np
import pytest

from quantlab5.v5.holdout_confirmation import confirm_frozen_candidates, hac_mean_se
from quantlab5.v5.inference import FixedFamilyResult
from quantlab5.v5.market_search import CandidateRecord, SearchTrace


def _record(cid, daily):
    return CandidateRecord(cid, "A", "E01", "long", {"id": cid}, 1.,
                           np.asarray(daily, float), np.ones(len(daily), int),
                           100, 2, 10., 1., cid, np.array([], int),
                           np.array([], int))


def test_confirmation_tests_every_frozen_exact_id_and_keeps_negative_result(monkeypatch):
    import quantlab5.v5.holdout_confirmation as h
    positive = _record("Q5-positive", np.ones(100))
    negative = _record("Q5-negative", -np.ones(100))
    trace = SearchTrace((positive, negative), {}, (), {}, (), {}, {}, (),
                        0., {}, (positive.candidate_id, negative.candidate_id))
    monkeypatch.setattr(h, "SignalContext", lambda market: type("C", (), {"stop": None})())
    monkeypatch.setattr(h, "_shadow_clock_baseline", lambda *args: None)
    monkeypatch.setattr(h, "fixed_family_inference", lambda streams, **kw:
                        FixedFamilyResult(np.array([20., -20.]), 0.01,
                                          np.array([.002, 1.]), np.zeros(kw["reps"])))
    costs = type("Costs", (), {"per_trade_points": lambda self, *args: 1.})()
    result = confirm_frozen_candidates(None, trace, costs,
                                       evaluator=lambda market, spec, context, costs,
                                       shadow_baseline: {"Q5-positive": positive,
                                                         "Q5-negative": negative}[spec["id"]])
    assert result.survivor_ids == ("Q5-positive",)
    assert result.classification["Q5-positive"] == "SUPPORTED"
    assert result.classification["Q5-negative"] == "REJECTED"
    assert set(result.classification) == set(trace.qualifying_ids)


def test_hac_interval_uses_full_day_stream_including_zero_days():
    mean, se = hac_mean_se(np.r_[np.ones(50), np.zeros(50)])
    assert mean == .5
    assert se > 0
    with pytest.raises(ValueError):
        hac_mean_se(np.array([1., np.nan, 0.]))


def test_stage_a_stream_reference_uses_all_60_common_day_rules(monkeypatch):
    import quantlab5.v5.market_search as search
    from quantlab5.v5.candidate_inventory import MECHANISMS
    rows = []
    for m in MECHANISMS:
        for side in ("long", "short"):
            r = _record(f"{m.code}-{side}", np.ones(10))
            rows.append(r.__class__(**{**r.__dict__, "family": m.code,
                                      "statistic": 2. if m.code == "E01" else 0.}))
    called = {}

    def fake(streams, **kw):
        called["shape"] = streams.shape
        called.update(kw)
        return FixedFamilyResult(np.zeros(60), 1., np.ones(60), np.array([0., 1., 2.]))

    monkeypatch.setattr(search, "fixed_family_inference", fake)
    p = search._stage_a_stream_family_p(rows)
    assert called == {"shape": (10, 60), "reps": 500, "block": 20,
                      "lags": 20, "seed": 515001}
    assert p["E01"] == .5
    assert p["E02"] == 1.
