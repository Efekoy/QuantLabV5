from dataclasses import dataclass

from quantlab5.v5.replay import replay_search


@dataclass(frozen=True)
class Row:
    candidate_id: str
    stage: str
    statistic: float


class Generator:
    def generate(self, market, seed):
        return {"seed": seed}


def test_adaptive_selection_is_recomputed_inside_each_world():
    calls = []

    def search(world):
        seed = world["seed"]
        calls.append(seed)
        family = "E01" if seed % 2 else "E02"
        rows = [Row(f"Q5-{family}-A", "A", float(seed))]
        if seed % 2:
            rows += [Row(f"Q5-{family}-B", "B", float(seed) + 1),
                     Row(f"Q5-{family}-C", "C", float(seed) + 2)]
        return rows, {family: max(r.statistic for r in rows)}

    out = replay_search({}, Generator(), [1, 2, 3], search)
    assert calls == [1, 2, 3]
    assert [x.selected_ids for x in out] == [
        ("Q5-E01-A", "Q5-E01-B", "Q5-E01-C"), ("Q5-E02-A",),
        ("Q5-E01-A", "Q5-E01-B", "Q5-E01-C")]
    assert [x.global_statistic for x in out] == [3.0, 2.0, 5.0]
