"""Unit tests: opinion gap, intervention tier and priority action logic
(Scoring and Maturity Framework V1, sections 6.2 and 6.4; FR14/FR15)."""

from decimal import Decimal

import pytest

from app.services.priority_actions import select_priority_action_candidates
from app.services.scoring import get_intervention_tier, round_score

AREA = "gap_priority"


def tier_case(case_id, combined, gap, expected, rule):
    return pytest.param(
        {
            "id": case_id,
            "title": f"Tier for combined {combined}, gap {gap}",
            "input": f"Combined mean {combined}, opinion gap {gap}",
            "expected": f"{expected} ({rule})",
            "combined": combined,
            "gap": gap,
            "tier": expected,
        },
        id=case_id,
    )


TIER_CASES = [
    tier_case("UT-GP-01", "3.00", "3.00", "High", "gap ≥ 3.00 overrides the mean"),
    tier_case("UT-GP-02", "4.00", "3.00", "High", "gap ≥ 3.00 overrides even a good mean"),
    tier_case("UT-GP-03", "3.00", "2.99", "Medium", "just under the override"),
    tier_case("UT-GP-04", "2.50", "1.51", "High", "combined ≤ 2.50 and gap > 1.50"),
    tier_case("UT-GP-05", "2.50", "1.50", "Medium", "combined ≤ 2.50, gap not > 1.50"),
    tier_case("UT-GP-06", "1.00", "0.00", "Medium", "lowest possible mean, no gap"),
    tier_case("UT-GP-07", "2.51", "1.51", "Medium", "combined ≤ 3.50 and gap > 1.50"),
    tier_case("UT-GP-08", "3.50", "1.50", "Low", "combined ≤ 3.50, gap not > 1.50"),
    tier_case("UT-GP-09", "3.51", "1.51", "Low", "combined < 4.50 and gap > 1.50"),
    tier_case("UT-GP-10", "4.49", "1.51", "Low", "combined < 4.50 and gap > 1.50"),
    tier_case("UT-GP-11", "3.51", "1.50", "Not flagged", "combined > 3.50, gap not > 1.50"),
    tier_case("UT-GP-12", "4.50", "1.60", "Not flagged", "combined ≥ 4.50 is never flagged below the override"),
]


@pytest.mark.qa(area=AREA)
@pytest.mark.parametrize("case", TIER_CASES)
def test_intervention_tier(case, evidence):
    actual = get_intervention_tier(Decimal(case["combined"]), Decimal(case["gap"]))
    evidence("actual", actual)
    assert actual == case["tier"]


@pytest.mark.qa(
    area=AREA,
    id="UT-GP-13",
    title="Opinion gap is the absolute difference and does not depend on which group scored higher",
    input="Employee 4.20 / Manager 2.60, then Employee 2.60 / Manager 4.20",
    expected="1.60 both ways",
)
def test_opinion_gap_is_symmetric(evidence):
    a = round_score(abs(Decimal("4.20") - Decimal("2.60")))
    b = round_score(abs(Decimal("2.60") - Decimal("4.20")))
    evidence("actual", f"{a} and {b}")
    assert a == b == Decimal("1.60")


def question(qid, tier, combined, gap, number=None):
    return {
        "question_id": qid,
        "question_number": number or f"1.{qid}",
        "domain_name": "Leadership",
        "employee_mean": combined - gap / 2,
        "manager_mean": combined + gap / 2,
        "combined_mean": combined,
        "opinion_gap": gap,
        "intervention_tier": tier,
    }


def ids(candidates):
    return [c["question_id"] for c in candidates]


@pytest.mark.qa(
    area=AREA,
    id="UT-GP-14",
    title="Not flagged questions are never priority actions",
    input="Q1 Not flagged, Q2 Low, Q3 Not flagged",
    expected="Only Q2 selected",
)
def test_not_flagged_excluded(evidence):
    result = select_priority_action_candidates(
        [
            question(1, "Not flagged", 4.6, 0.2),
            question(2, "Low", 3.4, 0.5),
            question(3, "Not flagged", 4.8, 0.1),
        ]
    )
    evidence("actual", f"Selected {ids(result)}")
    assert ids(result) == [2]


@pytest.mark.qa(
    area=AREA,
    id="UT-GP-15",
    title="Tier severity ranks before the mean",
    input="Q1 Low (combined 3.00), Q2 Medium (combined 3.40, gap 1.60), Q3 High (combined 3.00, gap 3.20)",
    expected="Order Q3, Q2, Q1 (High, Medium, Low)",
)
def test_tier_severity_first(evidence):
    result = select_priority_action_candidates(
        [
            question(1, "Low", 3.00, 0.2),
            question(2, "Medium", 3.40, 1.6),
            question(3, "High", 3.00, 3.2),
        ]
    )
    evidence("actual", f"Order {ids(result)}, urgency {[c['urgency'] for c in result]}")
    assert ids(result) == [3, 2, 1]


@pytest.mark.qa(
    area=AREA,
    id="UT-GP-16",
    title="Within a tier, the lowest combined mean comes first",
    input="Three Medium questions with combined 2.40, 1.80, 2.20",
    expected="Order 1.80, 2.20, 2.40",
)
def test_combined_mean_ascending(evidence):
    result = select_priority_action_candidates(
        [
            question(1, "Medium", 2.40, 0.5),
            question(2, "Medium", 1.80, 0.5),
            question(3, "Medium", 2.20, 0.5),
        ]
    )
    evidence("actual", f"Order {ids(result)}")
    assert ids(result) == [2, 3, 1]


@pytest.mark.qa(
    area=AREA,
    id="UT-GP-17",
    title="Equal tier and mean: the larger opinion gap comes first",
    input="Two High questions, both combined 2.00, gaps 1.60 and 2.40",
    expected="Gap 2.40 first",
)
def test_gap_breaks_ties(evidence):
    result = select_priority_action_candidates(
        [
            question(1, "High", 2.00, 1.6),
            question(2, "High", 2.00, 2.4),
        ]
    )
    evidence("actual", f"Order {ids(result)}")
    assert ids(result) == [2, 1]


@pytest.mark.qa(
    area=AREA,
    id="UT-GP-18",
    title="No more than five priority actions",
    input="Eight Low questions",
    expected="Five selected, the five lowest combined means",
)
def test_maximum_five(evidence):
    questions = [question(i, "Low", 3.0 + i / 100, 0.5) for i in range(1, 9)]
    result = select_priority_action_candidates(questions)
    evidence("actual", f"{len(result)} selected: {ids(result)}")
    assert ids(result) == [1, 2, 3, 4, 5]


@pytest.mark.qa(
    area=AREA,
    id="UT-GP-19",
    title="Each priority action carries its rank, tier and score evidence",
    input="One High question 2.3 (employee 1.40, manager 3.60)",
    expected="Priority 1, urgency High, title and evidence to 2 d.p.",
)
def test_candidate_fields(evidence):
    result = select_priority_action_candidates(
        [
            {
                "question_id": 7,
                "question_number": "2.3",
                "domain_name": "Worker Engagement",
                "employee_mean": 1.4,
                "manager_mean": 3.6,
                "combined_mean": 2.5,
                "opinion_gap": 2.2,
                "intervention_tier": "High",
            }
        ]
    )[0]
    evidence(
        "actual",
        f"priority {result['priority']}, urgency {result['urgency']}, "
        f"title '{result['title']}', evidence {result['assessment_evidence']}",
    )
    assert result["priority"] == 1
    assert result["urgency"] == "High"
    assert result["title"] == "Worker Engagement: Question 2.3"
    assert result["assessment_evidence"][0] == (
        "Employee mean 1.40, Senior Manager mean 3.60 (opinion gap 2.20)"
    )
    assert result["assessment_evidence"][1].startswith("Combined mean 2.50")


@pytest.mark.qa(
    area=AREA,
    id="UT-GP-20",
    title="No flagged questions means no priority actions",
    input="All questions Not flagged",
    expected="Empty list",
)
def test_no_flagged_questions(evidence):
    result = select_priority_action_candidates(
        [question(i, "Not flagged", 4.6, 0.1) for i in range(1, 6)]
    )
    evidence("actual", f"{len(result)} selected")
    assert result == []


@pytest.mark.qa(
    area=AREA,
    id="UT-GP-21",
    title="High Override questions (gap ≥ 3.00) rank inside the High tier by combined mean",
    input="High Override Q1 (combined 3.00, gap 4.00) and High Q2 (combined 2.00, gap 2.00)",
    expected="Q2 first: the override is stored as High and is not ranked separately",
)
def test_override_ranked_within_high(evidence):
    result = select_priority_action_candidates(
        [
            question(1, "High", 3.00, 4.0),
            question(2, "High", 2.00, 2.0),
        ]
    )
    evidence("actual", f"Order {ids(result)}")
    assert ids(result) == [2, 1]
