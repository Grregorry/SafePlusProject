from __future__ import annotations


TIER_SEVERITY: dict[str, int] = {
    "High": 0,
    "Medium": 1,
    "Low": 2,
}

MAX_PRIORITY_ACTIONS = 5


def select_priority_action_candidates(
    questions: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Rule-based FR14/FR15 selection.

    Eligibility and ordering follow the intervention tier decision
    table (Scoring and Maturity Framework V1, section 6.2/6.4):
    every High/Medium/Low tier question is a candidate, ordered by
    tier severity first, then Combined mean ascending, then Opinion
    Gap descending as the within-tier tie-break. The AI layer only
    narrates these pre-selected, pre-ranked candidates; it does not
    choose or reorder them.
    """

    eligible = [
        question
        for question in questions
        if question.get("intervention_tier") in TIER_SEVERITY
    ]

    def sort_key(
        question: dict[str, object],
    ) -> tuple[int, float, float]:
        tier = str(question.get("intervention_tier"))
        combined_mean = float(question.get("combined_mean") or 0)
        opinion_gap = float(question.get("opinion_gap") or 0)

        return (
            TIER_SEVERITY[tier],
            combined_mean,
            -opinion_gap,
        )

    ranked = sorted(eligible, key=sort_key)[
        :MAX_PRIORITY_ACTIONS
    ]

    candidates: list[dict[str, object]] = []

    for index, question in enumerate(ranked, start=1):
        employee_mean = float(question.get("employee_mean") or 0)
        manager_mean = float(question.get("manager_mean") or 0)
        combined_mean = float(question.get("combined_mean") or 0)
        opinion_gap = float(question.get("opinion_gap") or 0)
        domain_name = question.get("domain_name")
        question_number = question.get("question_number")
        intervention_tier = question.get("intervention_tier")

        candidates.append(
            {
                "question_id": question.get("question_id"),
                "priority": index,
                "title": (
                    f"{domain_name}: Question {question_number}"
                ),
                "related_domain": domain_name,
                "urgency": intervention_tier,
                "assessment_evidence": [
                    (
                        f"Employee mean {employee_mean:.2f}, "
                        f"Senior Manager mean {manager_mean:.2f} "
                        f"(opinion gap {opinion_gap:.2f})"
                    ),
                    (
                        f"Combined mean {combined_mean:.2f} "
                        f"— {intervention_tier} leverage"
                    ),
                ],
            }
        )

    return candidates
