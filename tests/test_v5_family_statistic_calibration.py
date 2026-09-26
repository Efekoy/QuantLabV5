from research.calibrate_v5_family_statistic import EDGES, METHODS, SHAPES, calibrate


def test_family_statistic_calibration_uses_disjoint_world_sets():
    # Small software test of the full result schema, not an empirical power claim.
    x = calibrate(days=40, frequency=100, calibration_worlds=3,
                  verification_worlds=3, plant_worlds=2, seed=723)
    assert x["status"] == "SYNTHETIC_STREAM_ONLY_NOT_ADAPTIVE_MARKET_REPLAY"
    assert set(x["cutoff"]) == set(METHODS)
    assert set(x["target_family_detection"]) == set(SHAPES)
    for shape in SHAPES:
        assert set(x["target_family_detection"][shape]) == {str(e) for e in EDGES}
        for effect in EDGES:
            for method in METHODS:
                cell = x["target_family_detection"][shape][str(effect)][method]
                assert cell["rate"] == cell["count"] / 2
