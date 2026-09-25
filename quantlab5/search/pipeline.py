"""THE evaluation pipeline -- one code path for real data and every null world.

`evaluate_candidates(market, candidates, build_signals, ctx)` takes a dict of Bars
(instrument -> Bars). It never looks at where the bars came from: real partitions
(via load_view), synthetic fixtures, and null/surrogate worlds are all `Bars`, built
by the same constructor, and flow through identical signal construction, execution,
costs and metrics. There is deliberately NO separate or simplified null evaluator
(nulls/evaluator.py calls this function; a test asserts it).

`build_signals(spec, market) -> SignalSet` is supplied by the (future) V4 grammar.
At bootstrap only synthetic dummy builders exist, in the tests.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Callable, Iterable

import numpy as np

from quantlab5.data.sessions import load_windows
from quantlab5.engine.costs import SCENARIOS, CostModel
from quantlab5.engine.execution import ExecutionPolicy, run_signals


@dataclass
class SignalSet:
    instrument: str
    sig_long: np.ndarray
    sig_short: np.ndarray
    window: str = "rth"
    direction: str = "both"
    hold: object = "eod"
    stop_dist: object = None
    tgt_dist: object = None
    exit_on_opposite: bool = False


@dataclass
class EvalContext:
    costs: CostModel
    sessions_cfg: dict
    policy: ExecutionPolicy = field(default_factory=ExecutionPolicy)


@dataclass
class CandidateResult:
    candidate_id: str
    instrument: str
    trades: int
    points: np.ndarray                  # per-trade points, one contract
    pnl_usd: dict[str, float]           # scenario -> total net P&L (one contract)
    trades_sha256: str

    def summary(self) -> dict:
        return {"candidate_id": self.candidate_id, "instrument": self.instrument, "trades": self.trades,
                "pnl_usd": self.pnl_usd, "trades_sha256": self.trades_sha256}


def evaluate_candidates(market: dict, candidates: Iterable, build_signals: Callable, ctx: EvalContext) -> list:
    windows = load_windows(ctx.sessions_cfg)
    out = []
    for cand in candidates:
        ss: SignalSet = build_signals(cand.spec, market)
        bars = market[ss.instrument]
        tick = ctx.costs.tick_size(ss.instrument)
        tr = run_signals(bars, ss.sig_long, ss.sig_short, windows[ss.window], ss.direction, ss.hold,
                         ss.stop_dist, ss.tgt_dist, ss.exit_on_opposite, ctx.policy, tick)
        pts = np.asarray(tr.points, dtype=np.float64)
        pv = ctx.costs.point_value(ss.instrument)
        pnl = {s: float((pts * pv - ctx.costs.per_trade(ss.instrument, s)).sum()) for s in SCENARIOS}
        h = hashlib.sha256()
        for a in (tr.entry_idx, tr.exit_idx, tr.side, tr.entry_px, tr.exit_px):
            h.update(np.ascontiguousarray(a).tobytes())
        out.append(CandidateResult(cand.candidate_id, ss.instrument, int(tr.n), pts, pnl, h.hexdigest()))
    return out
