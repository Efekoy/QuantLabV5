"""Dependent daily net-R panels for *conditional* inference calibration.

These panels are not substitutes for market-level feature generation/replay.
They contain clustered opportunity counts, shared candidate shocks, persistent
volatility, serial dependence, and Student-t tails. No market partition is read.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def dependent_panel(days: int, frequency: int, candidates: int, seed: int,
                    *, serial: float = 0.4, shared: float = 0.35) -> tuple[np.ndarray, np.ndarray]:
    if days < 30 or frequency < 1 or candidates < 1 or not 0 <= serial < 1 or not 0 <= shared < 1:
        raise ValueError("invalid panel configuration")
    rng = np.random.default_rng(seed)
    latent = np.empty(days)
    common = np.empty(days)
    logvol = np.empty(days)
    latent[0] = common[0] = logvol[0] = 0
    for t in range(1, days):
        latent[t] = 0.55 * latent[t - 1] + 0.5 * rng.standard_normal()
        common[t] = serial * common[t - 1] + rng.standard_t(5) / np.sqrt(5 / 3)
        logvol[t] = 0.85 * logvol[t - 1] + 0.18 * rng.standard_normal()
    intensity = np.exp(latent - 0.5 * np.var(latent))
    count = rng.poisson((frequency / 252) * intensity)
    volume_scale = np.exp(logvol - 0.5 * np.var(logvol))
    idio = rng.standard_t(5, size=(days, candidates)) / np.sqrt(5 / 3)
    shared_noise = shared * common[:, None] + np.sqrt(1 - shared**2) * idio
    # All candidates share opportunity times imperfectly; the target count is
    # recorded exactly. A common factor is multiplied by count, inducing day
    # clustering, while idiosyncratic noise scales with sqrt(count).
    counts = rng.poisson(np.maximum(count[:, None] * rng.lognormal(0, 0.2, size=(days, candidates)), 0))
    counts[:, 0] = count
    daily = volume_scale[:, None] * (shared * common[:, None] * counts +
                                     np.sqrt(1 - shared**2) * idio * np.sqrt(counts))
    return daily.astype(float), counts.astype(int)


def plant(panel: np.ndarray, counts: np.ndarray, edge_r: float, target: int = 0) -> np.ndarray:
    if panel.shape != counts.shape or not 0 <= target < panel.shape[1] or edge_r < 0:
        raise ValueError("bad plant")
    out = panel.copy()
    out[:, target] += edge_r * counts[:, target]
    return out


SHAPES = {
    "needle": (1.0, 0.0, 0.0, 0.0),
    "plateau": (1.0, 0.9, 0.8, 0.7),
    "family": (1.0, 0.75, 0.5, 0.25),
    "regime": (1.0, 0.9, 0.8, 0.7),
}


@dataclass(frozen=True)
class StructuredPanel:
    daily: np.ndarray             # day x 120 candidate net R
    counts: np.ndarray            # matching event counts
    regime: np.ndarray            # causal low-volatility state by day
    target_event_r: np.ndarray    # individual returns for candidate 0
    target_event_day: np.ndarray  # session index for each event

    def planted(self, shape: str, edge_r: float) -> tuple[np.ndarray, np.ndarray]:
        if shape not in SHAPES or edge_r < 0:
            raise ValueError("unknown shape or negative edge")
        x = self.daily.copy()
        if shape == "regime":
            # Candidate 0 is a causal state-gated rule: it does not trade on
            # off-state days. Neighbors 1–3 are broader variants.
            x[~self.regime, 0] = 0.0
        active = self.regime if shape == "regime" else np.ones(len(x), bool)
        for spec, strength in enumerate(SHAPES[shape]):
            x[:, spec] += edge_r * strength * self.counts[:, spec] * active
        take = active[self.target_event_day]
        ev = self.target_event_r[take] + edge_r if shape == "regime" else self.target_event_r + edge_r
        return x, ev


def structured_panel(days: int, frequency: int, seed: int, *, families: int = 30,
                     specs_per_family: int = 4, serial: float = 0.4) -> StructuredPanel:
    """Market-like shared events and neighboring specifications, never independent trades.

    One latent daily volatility state, persistent common/family shocks, heavy-tailed
    event noise, clustered opportunities, and ~88% shared event eligibility among
    four nearby specifications. Frequency is approximate per candidate per 252 days.
    """
    if days < 30 or frequency < 1 or families < 1 or specs_per_family != 4:
        raise ValueError("invalid structured-panel dimensions")
    rng = np.random.default_rng(seed)
    logvol = np.zeros(days)
    intensity = np.zeros(days)
    common = np.zeros(days)
    for t in range(1, days):
        logvol[t] = 0.85 * logvol[t - 1] + 0.16 * rng.standard_normal()
        intensity[t] = 0.55 * intensity[t - 1] + 0.35 * rng.standard_normal()
        common[t] = serial * common[t - 1] + rng.standard_t(5) / np.sqrt(5 / 3)
    regime = logvol < -0.15  # fixed causal latent-state threshold, never a future quantile
    vol = np.exp(logvol - 0.5 * np.var(logvol))
    lam = frequency / (252 * 0.88) * np.exp(intensity - 0.5 * np.var(intensity))[:, None]
    lam = lam * rng.lognormal(0, 0.10, size=(days, families))
    event_count = rng.poisson(lam)
    max_events = max(1, int(event_count.max()))
    alive = np.arange(max_events)[None, None, :] < event_count[:, :, None]
    family_shock = rng.normal(size=(days, families))
    tail = rng.standard_t(5, size=(days, families, max_events)) / np.sqrt(5 / 3)
    base = vol[:, None, None] * (0.30 * common[:, None, None] +
                                 0.20 * family_shock[:, :, None] + 0.88 * tail)
    eligible = (rng.random((days, families, specs_per_family, max_events)) < 0.88) & alive[:, :, None, :]
    idio = 0.15 * rng.standard_t(5, size=eligible.shape) / np.sqrt(5 / 3)
    event_r = (base[:, :, None, :] + idio) * eligible
    daily = event_r.sum(axis=-1).reshape(days, families * specs_per_family)
    counts = eligible.sum(axis=-1).reshape(days, families * specs_per_family)
    target_mask = eligible[:, 0, 0, :]
    target_values = event_r[:, 0, 0, :][target_mask]
    target_days = np.broadcast_to(np.arange(days)[:, None], target_mask.shape)[target_mask]
    return StructuredPanel(daily, counts, regime, target_values, target_days)
