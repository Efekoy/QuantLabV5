import numpy as np

from quantlab5.v5.synthetic_streams import dependent_panel, plant, structured_panel


def test_dependent_panels_have_counts_shared_shocks_and_exact_plant_shift():
    x, n = dependent_panel(1200, 250, 8, 15)
    y, m = dependent_panel(1200, 250, 8, 15)
    assert np.array_equal(x, y) and np.array_equal(n, m)
    assert abs(n[:, 0].sum() / (1200 / 252) - 250) < 50
    assert np.corrcoef(x[:, 0], x[:, 1])[0, 1] > 0.1
    z = plant(x, n, 0.1)
    assert np.allclose(z[:, 0] - x[:, 0], 0.1 * n[:, 0])
    assert np.array_equal(z[:, 1:], x[:, 1:])


def test_structured_plateau_shares_events_and_regime_is_subset():
    p = structured_panel(260, 250, 17)
    assert p.daily.shape == (260, 120)
    assert np.corrcoef(p.daily[:, 0], p.daily[:, 1])[0, 1] > 0.5
    needle, _ = p.planted("needle", 0.1)
    plateau, events = p.planted("plateau", 0.1)
    regime, _ = p.planted("regime", 0.1)
    assert np.array_equal(needle[:, 1:], p.daily[:, 1:])
    assert (plateau[:, :4] - p.daily[:, :4]).sum() > (needle[:, :4] - p.daily[:, :4]).sum()
    assert np.all(regime[~p.regime, 0] == 0)
    assert np.allclose(regime[~p.regime, 1:], p.daily[~p.regime, 1:])
    assert len(events) == len(p.target_event_day)
