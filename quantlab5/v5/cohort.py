"""No-cap scientific cohort transition after independent validation.

This function is a protocol component, not permission to open VALIDATION.
Prop portfolio membership is deliberately absent from its inputs.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScientificCohort:
    candidate_ids: tuple[str, ...]
    audit_1_ids: tuple[str, ...]
    audit_2_ids: tuple[str, ...]


def form_scientific_cohort(validation_rows) -> ScientificCohort:
    """Advance every individually qualified ID, including correlated rules."""
    seen = set()
    accepted = []
    for row in validation_rows:
        cid = str(row["candidate_id"])
        if cid in seen:
            raise ValueError(f"duplicate validation candidate ID: {cid}")
        seen.add(cid)
        if bool(row["qualified"]):
            accepted.append(cid)
    ids = tuple(sorted(accepted))
    return ScientificCohort(ids, ids, ids)
