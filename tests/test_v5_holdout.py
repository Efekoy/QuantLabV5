import numpy as np

from quantlab5.v5.holdout import (Nomination, discovery_screen, empirical_p,
                                 family_statistic, fdr_adjust, stepdown_p,
                                 validate)
from quantlab5.v5.synthetic_streams import structured_panel


def test_discovery_screen_has_no_numerical_cap():
    rng = np.random.default_rng(61)
    x = .2 + rng.normal(0, .1, size=(100, 73 * 4))
    c = np.ones_like(x)
    n = discovery_screen(x, c, min_events=50)
    assert len(n.families) == 73


def test_correlated_qualified_families_are_annotated_and_all_advance():
    rng = np.random.default_rng(62)
    base = .4 + rng.normal(0, .01, size=(100, 4))
    x = np.column_stack((base, base.copy(), base + rng.normal(0, .001, size=(100, 4))))
    n = discovery_screen(x, np.ones_like(x), min_events=50)
    assert n.families == (0, 1, 2)
    assert n.behavioral_duplicate_of == (0, 0, 0)


def test_discovery_screen_uses_halves_and_stress():
    x = np.ones((100, 8)) * .1
    c = np.ones_like(x)
    x[50:, 4:] = -.01
    n = discovery_screen(x, c, min_events=50)
    assert n.families == (0,)


def test_stepdown_and_fdr_adjustments_are_monotone_and_bounded():
    p = np.array([.001, .02, .2])
    assert np.all(fdr_adjust(p) <= fdr_adjust(p, conservative=True))
    z = np.random.default_rng(1).normal(size=(199, 3))
    adj = stepdown_p(np.array([4., 2., 0.]), z)
    assert np.all(np.diff(adj) >= 0)
    assert np.all((adj >= 0) & (adj <= 1))
    assert np.all((empirical_p(np.array([4., 2., 0.]), z) >= 0))


def test_independent_validation_uses_only_frozen_family_and_rule():
    panel = structured_panel(160, 150, 11)
    x, _ = panel.planted("plateau", .8)
    nom = Nomination((0,), (3,), (0,))
    null = np.random.default_rng(2).normal(size=(199, 120))
    famnull = np.random.default_rng(3).normal(size=(199, 30))
    before = validate(nom, x, null, famnull)
    changed = x.copy()
    changed[:, 4:] += 100
    after = validate(nom, changed, null, famnull)
    # Selected IDs are fixed; changing an unselected family cannot change the
    # tested columns or the null reference for the frozen hypotheses.
    assert before == after


def test_family_statistic_does_not_count_four_rules_as_extra_sessions():
    x = np.random.default_rng(4).normal(size=(100, 4))
    t = family_statistic(x, "daily_mean")
    from quantlab5.v5.inference import hac_t
    assert np.allclose(t, hac_t(x.mean(axis=1)))


def test_family_evidence_alone_cannot_confirm_null_representative():
    x = np.zeros((120, 120))
    x[:, 0] = 10.0  # a needle in another member of the same family
    nom = Nomination((0,), (1,), (0,))
    rng = np.random.default_rng(42)
    exact_null = rng.normal(size=(199, 120))
    family_null = rng.normal(size=(199, 30))
    out = validate(nom, x, exact_null, family_null)
    assert out["family_first"] == ()
