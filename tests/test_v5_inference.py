from __future__ import annotations

import numpy as np

from quantlab5.v5.inference import (clopper_pearson, fixed_family_inference,
                                    hac_t, sequential_decision, stationary_indices)


def test_stationary_bootstrap_keeps_common_blocks_and_serial_dependence():
    rng = np.random.default_rng(9)
    ix = stationary_indices(1000, 20, rng)
    assert (ix >= 0).all() and (ix < 1000).all()
    assert np.mean(ix[1:] == (ix[:-1] + 1) % 1000) > 0.90
    x = np.arange(1000, dtype=float)
    panel = np.column_stack((x, x * 2))
    assert np.array_equal(panel[ix, 1], 2 * panel[ix, 0])


def test_joint_stepdown_detects_plant_and_controls_fixed_family():
    rng = np.random.default_rng(13)
    n = 360
    common = rng.normal(0, 0.5, n)
    x = np.column_stack([common + rng.normal(0, 1, n) for _ in range(4)])
    planted = x.copy()
    planted[:, 2] += 0.45
    a = fixed_family_inference(planted, reps=199, block=20, seed=3)
    assert a.global_p <= 0.05
    assert a.adjusted_p[2] <= 0.05
    assert all(a.adjusted_p[j] >= a.adjusted_p[2] for j in (0, 1, 3))
    assert np.max(np.abs(hac_t(x))) < np.max(a.t)


def test_sequential_rule_requires_confident_boundary_and_spends_error():
    assert sequential_decision(np.zeros(500, bool)).n >= 100
    assert sequential_decision(np.zeros(500, bool)).status == "SIGNIFICANT"
    assert sequential_decision(np.ones(50, bool)).status == "NONSIGNIFICANT"
    mixed = np.r_[np.ones(25, bool), np.zeros(25, bool)]
    assert sequential_decision(mixed).status == "NONSIGNIFICANT"
    lo, hi = clopper_pearson(0, 50)
    assert lo == 0 and hi > 0.05


def test_zero_edge_sequential_false_declaration_is_rare():
    # A genuine p=0.05 null-world exceedance rate should almost never be
    # declared below 0.05 by the confidence-sequence stopping rule.
    rng = np.random.default_rng(20260925)
    n_false = sum(sequential_decision(rng.random(500) < 0.05).status == "SIGNIFICANT"
                  for _ in range(300))
    assert n_false <= 6
