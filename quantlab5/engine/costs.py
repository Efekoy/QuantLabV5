"""Centralised trading costs. Strategy code never sees a cost number.

(Copied from quantlab3/engine/costs.py. V4 changes: scenario "stressed" renamed
"stress"; per-instrument `validated` flag; `require_validated` guard; micro-contract
mapping; `from_settings` replaced by `from_project`. The arithmetic is unchanged.)
"""
from __future__ import annotations

from dataclasses import dataclass

SCENARIOS = ("gross", "moderate", "baseline", "stress")


@dataclass(frozen=True)
class InstrumentCosts:
    tick_size: float
    point_value: float
    commission_round_trip: float
    slippage_ticks_per_side: float
    extra_cost_round_trip: float
    validated: bool = False

    @property
    def tick_value(self) -> float:
        return self.tick_size * self.point_value


class CostModel:
    def __init__(self, costs_cfg: dict, version: str):
        self.version = version
        self.instruments = {k: InstrumentCosts(float(v["tick_size"]), float(v["point_value"]),
                                               float(v.get("commission_round_trip", 0.0)),
                                               float(v.get("slippage_ticks_per_side", 0.0)),
                                               float(v.get("extra_cost_round_trip", 0.0)),
                                               bool(v.get("validated", False)))
                            for k, v in (costs_cfg.get("instruments") or {}).items()}
        self.scenarios = {k: dict(v) for k, v in (costs_cfg.get("scenarios") or {}).items()}
        self.micro_of = dict(costs_cfg.get("micro_of") or {})
        missing = [s for s in SCENARIOS if s not in self.scenarios]
        if missing:
            raise ValueError(f"cost config lacks scenarios {missing}")

    @classmethod
    def from_project(cls, project) -> "CostModel":
        cfg = project.costs
        return cls(cfg, cfg["version"])

    def require_validated(self, instrument: str) -> None:
        if not self.instruments[instrument].validated:
            raise ValueError(f"{instrument} costs are an unvalidated placeholder (config/costs.yaml)")

    def tick_size(self, instrument: str) -> float:
        return self.instruments[instrument].tick_size

    def point_value(self, instrument: str) -> float:
        return self.instruments[instrument].point_value

    def per_trade(self, instrument: str, scenario: str) -> float:
        """Dollar cost of one round trip of one contract under a scenario."""
        ic = self.instruments[instrument]
        sc = self.scenarios[scenario]
        return (ic.commission_round_trip * float(sc.get("commission_mult", 1.0))
                + 2.0 * ic.slippage_ticks_per_side * ic.tick_value * float(sc.get("slippage_mult", 1.0))
                + ic.extra_cost_round_trip * float(sc.get("extra_mult", 1.0)))

    def trade_cost(self, instrument: str, scenario: str, exit_fractions=(1.0,)) -> float:
        """Execution cost of ONE normalised unit entered once and exited in legs.

        commission: one round trip per unit (per-contract commission is split across the legs
        in proportion, so the total is one round trip);
        slippage: the full unit slips on entry, and EACH exit leg slips on its own fraction.
        Hence sum(fractions) == 1 gives exactly `per_trade` -- partial exits are not charged a
        new full round trip, but every leg pays its proportional exit slippage.
        """
        ic = self.instruments[instrument]
        sc = self.scenarios[scenario]
        fr = [float(f) for f in exit_fractions]
        slip = ic.slippage_ticks_per_side * ic.tick_value * float(sc.get("slippage_mult", 1.0))
        comm = ic.commission_round_trip * float(sc.get("commission_mult", 1.0))
        return comm * sum(fr) + slip * (1.0 + sum(fr)) + ic.extra_cost_round_trip * float(sc.get("extra_mult", 1.0))

    def per_trade_points(self, instrument: str, scenario: str) -> float:
        return self.per_trade(instrument, scenario) / self.point_value(instrument)

    def describe(self, instrument: str) -> str:
        ic = self.instruments[instrument]
        return (f"{instrument}: ${ic.point_value:g}/point, tick {ic.tick_size:g} (${ic.tick_value:g}); "
                f"commission ${ic.commission_round_trip:.2f}/round trip; slippage "
                f"{ic.slippage_ticks_per_side:g} tick/side -> baseline ${self.per_trade(instrument, 'baseline'):.2f}, "
                f"stress ${self.per_trade(instrument, 'stress'):.2f} per round trip")
