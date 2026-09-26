"""Assumption-only planning power table. Never opens market data."""
from __future__ import annotations

import math

FREQUENCIES = (25, 50, 100, 250, 500, 1000)
YEARS = {"discovery": 2198 / 252, "validation": 1034 / 252,
         "audit_1": 775 / 252, "audit_2": 157 / 252}
DESIGN_EFFECT = 1.5
SIGMA_R = 1.0
Z80 = 0.8416212335729143
Z90 = 1.2815515655446004


def mde(frequency: float, period: str, critical_z: float, power_z: float = Z80,
        sigma_r: float = SIGMA_R, design_effect: float = DESIGN_EFFECT) -> float:
    if frequency <= 0 or critical_z < 0 or sigma_r <= 0 or design_effect < 1:
        raise ValueError("invalid planning assumption")
    return (critical_z + power_z) * sigma_r * math.sqrt(
        design_effect / (frequency * YEARS[period]))


if __name__ == "__main__":
    print("trades/yr disc80 disc90 val80 audit1_80 audit2_80")
    for f in FREQUENCIES:
        print(f, *(f"{mde(f, p, z, q):.3f}" for p, z, q in (
            ("discovery", 4.0, Z80), ("discovery", 4.0, Z90),
            ("validation", 1.645, Z80), ("audit_1", 1.645, Z80),
            ("audit_2", 1.645, Z80))))
