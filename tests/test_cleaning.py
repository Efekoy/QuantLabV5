"""Cleaning v1: causal roll-window flag."""
import numpy as np

from quantlab5.data.cleaning import contract_month, roll_window_mask


def _days(*iso):
    return np.array([np.datetime64(x, "D").astype(np.int64) for x in iso])


def test_contract_month_codes():
    assert contract_month(["NQZ8", "ESH1", "NQM0", "NQU9", "XX"]).tolist() == [12, 3, 6, 9, 0]


def test_roll_window_only_while_holding_expiring_contract():
    sd = _days("2018-12-07", "2018-12-10", "2018-12-13", "2018-12-14", "2018-12-14", "2018-11-20", "2019-01-10")
    sym = ["NQZ8", "NQZ8", "NQZ8", "NQZ8", "NQH9", "NQZ8", "NQH9"]
    assert roll_window_mask(sd, sym).tolist() == [False, True, True, True, False, False, False]


def test_roll_window_is_causal_depends_only_on_same_bar_date_and_symbol():
    sd = _days("2018-12-10", "2018-12-11", "2018-12-12")
    a = roll_window_mask(sd, ["NQZ8"] * 3)
    b = roll_window_mask(sd, ["NQZ8", "NQZ8", "NQH9"])          # future roll changes only its own bar
    assert a[:2].tolist() == b[:2].tolist()
