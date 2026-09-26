from datetime import date

import numpy as np
import yaml

from quantlab5.data.market import build_market
from quantlab5.engine.costs import CostModel
from quantlab5.search.candidate_id import candidate_id
from quantlab5.synthetic.markets import correlated_pair, weekdays
from quantlab5.v5.candidate_inventory import inventory
from quantlab5.v5.market_search import CandidateRecord, SearchTrace
from quantlab5.v5.validation import validate_frozen_cohort


def test_all_qualifying_members_can_survive_independent_family_gate():
    nq, es = correlated_pair(weekdays(date(2020, 1, 2), date(2020, 1, 9)))
    market = build_market(nq, es, np.full(nq.n, "NQZ0"), np.full(es.n, "ESZ0"))
    from pathlib import Path
    cfg = yaml.safe_load((Path(__file__).resolve().parents[1] / "config/costs.yaml").read_text())
    costs = CostModel(cfg, "test")
    specs = [s for s in inventory()["stage_a"] if s["family"] in ("E01", "E02") and s["side"] == "long"]

    def record(spec):
        cid = candidate_id(spec)
        return CandidateRecord(cid, "A", spec["family"], spec["side"], spec,
                               4.0, np.ones(40), np.ones(40, int), 120, 6, 1.0, 1.0,
                               cid, np.array([1], np.int32), np.array([1], np.int8))

    rows = tuple(map(record, specs))
    ids = tuple(r.candidate_id for r in rows)
    discovery = SearchTrace(rows, {}, (), {}, ids[:1], {}, {}, (), 4.0, {}, ids)
    def evaluator(world, spec, context, cost_model, *, shadow_baseline):
        return record(spec)
    result = validate_frozen_cohort(market, discovery, costs, evaluator=evaluator, reps=99)
    assert set(result.survivor_ids) == set(ids)
    assert result.discovery_nominee_ids == ids[:1]
