from quantlab5.v5.cohort import form_scientific_cohort


def test_every_validation_qualifier_reaches_both_audits_without_cap_or_correlation_filter():
    rows = [{"candidate_id": f"Q5-{i:03d}", "qualified": i % 3 != 0,
             "behavioral_duplicate_of": "Q5-001"}
            for i in range(150)]
    cohort = form_scientific_cohort(rows)
    assert len(cohort.candidate_ids) == 100
    assert cohort.audit_1_ids == cohort.audit_2_ids == cohort.candidate_ids
    assert "Q5-149" in cohort.candidate_ids
