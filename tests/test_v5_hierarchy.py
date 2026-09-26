import numpy as np

from quantlab5.v5.hierarchy import (cluster_support, deterministic_medoid,
                                   evaluate_hierarchy, evaluate_shape_effects,
                                   event_cluster_t, holm_adjust)
from quantlab5.v5.inference import hac_t
from quantlab5.v5.inference import fixed_family_inference
from quantlab5.v5.synthetic_streams import structured_panel


def test_holm_and_medoid_are_deterministic():
    assert np.allclose(holm_adjust(np.array([0.01, 0.03, 0.5])), [0.03, 0.06, 0.5])
    x = np.array([[1, 1, 4, 4], [2, 2, 5, 5]], float)
    assert deterministic_medoid(x) == 0
    assert cluster_support(np.ones((20, 4)))


def test_holm_uses_continuous_hac_marginals_with_120_hypotheses():
    # A 99-draw bootstrap marginal has p >= 0.01 and therefore can never
    # survive a 120-way Holm correction, regardless of the observed t.
    panel = structured_panel(160, 150, 24)
    x, events = panel.planted("needle", 10.0)
    r = evaluate_hierarchy(x, target_events=events, reps=19, seed=3)
    assert r.holm_p <= 0.05


def test_event_cluster_t_uses_sessions_not_independent_trades():
    rng = np.random.default_rng(1)
    count = rng.poisson(3, 200)
    daily = count * rng.normal(size=200)
    assert event_cluster_t(daily, count) == float(hac_t(daily)[0])


def test_plateau_can_support_family_without_exact_spec_fwer_claim():
    panel = structured_panel(420, 500, 7)
    x, events = panel.planted("plateau", 0.45)
    r = evaluate_hierarchy(x, target_events=events, reps=99, seed=4)
    assert r.family_supported and r.neighborhood_supported
    assert r.family_adjusted_p <= 0.05
    assert 0 <= r.representative_spec < 4


def test_reused_bootstrap_matches_full_recomputation():
    panel = structured_panel(160, 150, 21)
    x, events = panel.planted("family", 0.1)
    full = evaluate_hierarchy(x, target_events=events, reps=39, seed=11)
    reused = evaluate_shape_effects(panel, "family", [0.1], reps=39, seed=11)[0]
    for field in ("single_bootstrap_p", "holm_p", "stepdown_p", "global_p", "family_adjusted_p"):
        assert abs(getattr(full, field) - getattr(reused, field)) < 1e-12


def test_reused_bootstrap_matches_regime_gated_recomputation():
    panel = structured_panel(160, 150, 22)
    x, events = panel.planted("regime", 0.1)
    full = evaluate_hierarchy(x, target_events=events, reps=39, seed=12)
    reused = evaluate_shape_effects(panel, "regime", [0.1], reps=39, seed=12)[0]
    for field in ("single_bootstrap_p", "holm_p", "stepdown_p", "global_p", "family_adjusted_p"):
        assert abs(getattr(full, field) - getattr(reused, field)) < 1e-12


def test_iid_single_candidate_matches_normal_size_and_mde80():
    from scipy.stats import norm
    rng = np.random.default_rng(333)
    n, worlds = 500, 4000
    noise = rng.normal(size=(n, worlds))
    cutoff = norm.isf(0.05)
    mde80 = (cutoff + norm.ppf(0.8)) / np.sqrt(n)
    null_rate = float(np.mean(hac_t(noise, lags=0) > cutoff))
    power = float(np.mean(hac_t(noise + mde80, lags=0) > cutoff))
    assert 0.035 < null_rate < 0.065
    assert 0.77 < power < 0.83


def test_iid_bootstrap_single_candidate_is_not_grossly_miscalibrated():
    from scipy.stats import norm
    rng = np.random.default_rng(334)
    n, worlds = 252, 120
    edge80 = (norm.isf(0.05) + norm.ppf(0.8)) / np.sqrt(n)
    null_hits = planted_hits = 0
    for i in range(worlds):
        noise = rng.normal(size=(n, 1))
        null_hits += fixed_family_inference(noise, reps=99, block=20, lags=0, seed=i).global_p <= 0.05
        planted_hits += fixed_family_inference(noise + edge80, reps=99, block=20,
                                                lags=0, seed=i).global_p <= 0.05
    assert null_hits <= 12  # nominal 5%, wide finite-simulation tolerance
    assert 78 <= planted_hits <= 112
