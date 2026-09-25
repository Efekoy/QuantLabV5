"""Screening skeleton: declarative, pre-registered filters over CandidateResult summaries.

No thresholds are defined here or in config yet -- they will be pre-registered with
the V4 grammar. A Screen is an ordered list of (name, metric, op, threshold) rules;
every rule's pass/fail is recorded for every candidate (no silent drops).
"""
from __future__ import annotations

import operator
from dataclasses import dataclass

_OPS = {">=": operator.ge, ">": operator.gt, "<=": operator.le, "<": operator.lt, "==": operator.eq}


@dataclass(frozen=True)
class Rule:
    name: str
    metric: str
    op: str
    threshold: float

    def __post_init__(self):
        if self.op not in _OPS:
            raise ValueError(f"unknown operator {self.op}")


def apply_screen(rows: list[dict], rules: list[Rule]) -> list[dict]:
    out = []
    for r in rows:
        verdicts = {}
        for rule in rules:
            v = r.get(rule.metric)
            verdicts[rule.name] = v is not None and bool(_OPS[rule.op](v, rule.threshold))
        out.append({**r, "screen": verdicts, "passed": all(verdicts.values())})
    return out
