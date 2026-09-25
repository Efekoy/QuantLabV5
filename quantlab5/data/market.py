"""A research 'world': NQ bars (traded) + ES bars (information), cleaned and aligned.

Real partitions, null worlds and synthetic worlds all become a `Market` through `build_market`,
and everything downstream (features, triggers, filters, outcomes, search, ML) takes a Market.

Decision bars: bar t is a decision bar when a signal at its CLOSE can be executed at the OPEN of
bar t+1 under the frozen execution rules. t+1 must exist, be in the same session and contract,
and start in [09:30, 15:30) New York (the `rth` entry window). Positions are flat by 16:00.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from quantlab5.data.align import align_other
from quantlab5.data.cleaning import CLEANING_VERSION, roll_window_mask
from quantlab5.data.schema import Bars
from quantlab5.features.ops import group_ids

ENTRY_START_SM, ENTRY_END_SM, FLAT_SM = 930, 1290, 1320     # 09:30, 15:30, 16:00 in session minutes


@dataclass
class Market:
    nq: Bars
    es: Bars
    nq_symbols: np.ndarray
    es_symbols: np.ndarray
    gid: np.ndarray = field(init=False)
    rw: np.ndarray = field(init=False)            # NQ roll-window flag (cleaning v1)
    es_rw: np.ndarray = field(init=False)         # ES roll-window flag aligned to NQ minutes
    eo: np.ndarray = field(init=False)
    eh: np.ndarray = field(init=False)
    el: np.ndarray = field(init=False)
    ec: np.ndarray = field(init=False)
    ev: np.ndarray = field(init=False)
    evalid: np.ndarray = field(init=False)
    es_seg: np.ndarray = field(init=False)
    dec: np.ndarray = field(init=False)           # decision bar indices into NQ arrays
    cleaning_version: str = CLEANING_VERSION

    def __post_init__(self):
        b = self.nq
        self.gid = group_ids(b.sday, b.seg)
        self.rw = roll_window_mask(b.sday, self.nq_symbols)
        al = align_other(b, self.es)
        self.eo, self.eh, self.el, self.ec, self.ev = al.o, al.h, al.l, al.c, al.v
        self.evalid, self.es_seg = al.valid, al.seg
        es_rw_own = roll_window_mask(self.es.sday, self.es_symbols)
        pos = np.searchsorted(self.es.ts, b.ts)
        pos = np.minimum(pos, max(self.es.n - 1, 0))
        self.es_rw = np.where(al.valid, es_rw_own[pos] if self.es.n else False, False)
        n = b.n
        sm = np.asarray(b.sm).astype(np.int64)
        nxt_ok = np.zeros(n, dtype=bool)
        if n > 1:
            nxt_ok[:-1] = ((self.gid[1:] == self.gid[:-1]) & (sm[1:] >= ENTRY_START_SM) & (sm[1:] < ENTRY_END_SM))
        self.dec = np.nonzero(nxt_ok)[0].astype(np.int64)

    @property
    def n(self) -> int:
        return self.nq.n

    def years(self) -> np.ndarray:
        d = np.asarray(self.nq.sday, dtype="int64").astype("datetime64[D]")
        return d.astype("datetime64[Y]").astype(np.int64) + 1970


def build_market(nq: Bars, es: Bars, nq_symbols, es_symbols) -> Market:
    if nq.instrument != "NQ" or es.instrument != "ES":
        raise ValueError("build_market expects NQ then ES")
    return Market(nq, es, np.asarray(nq_symbols).astype(str), np.asarray(es_symbols).astype(str))


def load_market(partition: str, start=None, end=None, project=None, purpose: str = "") -> Market:
    """Load NQ + ES for a partition through load_view (ledgered) and build the Market."""
    from quantlab5.isolation.load_view import load_view
    cols = ["open", "high", "low", "close", "volume", "symbol"]
    mq = load_view("NQ", partition, start, end, cols, project=project, purpose=purpose)
    me = load_view("ES", partition, start, end, cols, project=project, purpose=purpose)
    return build_market(mq.bars(), me.bars(), mq.frame["symbol"].to_numpy(), me.frame["symbol"].to_numpy())


def concat_markets(a: Market, b: Market) -> Market:
    """Chronological concatenation (a entirely before b), e.g. DISCOVERY warm-up tail + VALIDATION."""
    from quantlab5.data.schema import bars_from_arrays

    def cat(x, y, sym_x, sym_y):
        if x.n and y.n and x.ts[-1] >= y.ts[0]:
            raise ValueError("markets overlap or are out of order")
        return bars_from_arrays(x.instrument, np.r_[x.ts, y.ts], np.r_[x.o, y.o], np.r_[x.h, y.h], np.r_[x.l, y.l],
                                np.r_[x.c, y.c], np.r_[x.v, y.v], np.r_[sym_x, sym_y], source=f"{x.source}+{y.source}")
    return build_market(cat(a.nq, b.nq, a.nq_symbols, b.nq_symbols), cat(a.es, b.es, a.es_symbols, b.es_symbols),
                        np.r_[a.nq_symbols, b.nq_symbols], np.r_[a.es_symbols, b.es_symbols])


def tail_sessions(m: Market, n_sessions: int) -> Market:
    days = np.unique(np.asarray(m.nq.sday))
    d0 = days[-n_sessions] if len(days) > n_sessions else days[0]
    a = int(np.searchsorted(np.asarray(m.nq.sday), d0, "left"))
    ea = int(np.searchsorted(np.asarray(m.es.sday), d0, "left"))
    return build_market(m.nq.slice(a, m.nq.n), m.es.slice(ea, m.es.n), m.nq_symbols[a:], m.es_symbols[ea:])
