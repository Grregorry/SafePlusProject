"""Unit tests: SafePlus scoring engine for controlled inputs.

Expected values are hand-calculated with the SafePlus method (Likert
1-5, N/A left out, means to 2 d.p. rounding half up, combined mean =
average of the Employee and Senior Manager means, maturity bands
Developing <= 2.50 < Performing < 4.50 <= Leading). The testing document
has a column for the WorkSafe calculator result for the same inputs.
"""

from decimal import ROUND_HALF_UP, Decimal
from types import SimpleNamespace

import pytest

from app.services.scoring import (
    calculate_group_mean,
    calculate_mean,
    combine_counts_by_option,
    get_maturity_level,
)

from .helpers import (
    OPTIONS,
    active_questions,
    auth_headers,
    create_assessment,
    public_code,
    submit_respondent,
)

AREA = "scoring"

SA, A, N, D, SD = (OPTIONS[v] for v in (5, 4, 3, 2, 1))


def case(case_id, title, value, working, expected, **extra):
    return pytest.param(
        {"id": case_id, "title": title, "input": value, "working": working, "expected": expected, **extra},
        id=case_id,
    )


GROUP_MEAN_CASES = [
    case("UT-SC-01", "All respondents strongly agree", {SA: 10}, "(10×5) ÷ 10", "5.00"),
    case("UT-SC-02", "All respondents strongly disagree", {SD: 10}, "(10×1) ÷ 10", "1.00"),
    case("UT-SC-03", "Mixed agreement", {SA: 2, A: 5, N: 3}, "(2×5 + 5×4 + 3×3) ÷ 10 = 39 ÷ 10", "3.90"),
    case("UT-SC-04", "One answer of each option", {SA: 1, A: 1, N: 1, D: 1, SD: 1}, "(5+4+3+2+1) ÷ 5 = 15 ÷ 5", "3.00"),
    case("UT-SC-05", "N/A answers are left out of the mean", {A: 4, "N/A": 3}, "(4×4) ÷ 4; the 3 N/A are not counted", "4.00"),
    case("UT-SC-06", "Recurring decimal is rounded to 2 d.p.", {SA: 1, A: 1, D: 1}, "(5+4+2) ÷ 3 = 3.666…", "3.67"),
    case("UT-SC-07", "An exact half rounds up", {SA: 1, A: 2, N: 2, D: 3}, "(5 + 2×4 + 2×3 + 3×2) ÷ 8 = 25 ÷ 8 = 3.125", "3.13"),
    case("UT-SC-08", "Only N/A answers give no score", {"N/A": 5}, "No scorable answers", "No score"),
    case("UT-SC-09", "No answers give no score", {}, "No answers", "No score"),
]


@pytest.mark.qa(area=AREA)
@pytest.mark.parametrize("case", GROUP_MEAN_CASES)
def test_group_mean(case, evidence):
    result = calculate_group_mean(case["input"])
    actual = "No score" if result is None else str(result)
    evidence("actual", actual)
    assert actual == case["expected"]


@pytest.mark.qa(
    area=AREA,
    id="UT-SC-10",
    title="Online and paper answers are combined before averaging",
    input="Online: Agree ×3, Disagree ×1. Paper: Agree ×1, Strongly Agree ×1",
    working="Agree ×4, Disagree ×1, Strongly Agree ×1 → (16 + 2 + 5) ÷ 6 = 3.833…",
    expected="3.83",
)
def test_online_and_paper_combined(evidence):
    online = [SimpleNamespace(response_option=A, count=3), SimpleNamespace(response_option=D, count=1)]
    paper = [SimpleNamespace(response_option=A, count=1), SimpleNamespace(response_option=SA, count=1)]
    actual = str(calculate_group_mean(combine_counts_by_option(online, paper)))
    evidence("actual", actual)
    assert actual == "3.83"


MATURITY_CASES = [
    case("UT-SC-11", "Maturity band at the minimum", "1.00", "1.00 ≤ 2.50", "Developing"),
    case("UT-SC-12", "Maturity band at the Developing limit", "2.50", "2.50 ≤ 2.50", "Developing"),
    case("UT-SC-13", "Maturity band just above Developing", "2.51", "2.50 < 2.51 < 4.50", "Performing"),
    case("UT-SC-14", "Maturity band mid-range", "3.50", "2.50 < 3.50 < 4.50", "Performing"),
    case("UT-SC-15", "Maturity band just below Leading", "4.49", "4.49 < 4.50", "Performing"),
    case("UT-SC-16", "Maturity band at the Leading limit", "4.50", "4.50 ≥ 4.50", "Leading"),
    case("UT-SC-17", "Maturity band at the maximum", "5.00", "5.00 ≥ 4.50", "Leading"),
]


@pytest.mark.qa(area=AREA)
@pytest.mark.parametrize("case", MATURITY_CASES)
def test_maturity_level(case, evidence):
    actual = get_maturity_level(Decimal(case["input"]))
    evidence("actual", actual)
    assert actual == case["expected"]


DOMAIN_CASES = [
    case("UT-SC-18", "Domain mean is the average of its question combined means",
         "Question combined means 3.40, 2.50, 4.00", "(3.40 + 2.50 + 4.00) ÷ 3 = 9.90 ÷ 3", "3.30",
         values=["3.40", "2.50", "4.00"]),
    case("UT-SC-19", "Domain mean is rounded to 2 d.p.",
         "Question combined means 3.97, 3.07, 3.00", "(3.97 + 3.07 + 3.00) ÷ 3 = 10.04 ÷ 3 = 3.346…", "3.35",
         values=["3.97", "3.07", "3.00"]),
]


@pytest.mark.qa(area=AREA)
@pytest.mark.parametrize("case", DOMAIN_CASES)
def test_domain_mean(case, evidence):
    actual = str(calculate_mean([Decimal(v) for v in case["values"]]))
    evidence("actual", actual)
    assert actual == case["expected"]


def half_up(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@pytest.mark.qa(
    area=AREA,
    id="UT-SC-20",
    title="Scoring engine output for a controlled survey, end to end",
    input="5 Employee + 3 Senior Manager online surveys with fixed answers",
    expected="Question, domain and overall results equal the hand calculation",
)
def test_controlled_survey(client, evidence):
    headers = auth_headers(client)
    assessment = create_assessment(client, headers)
    base = f"/api/assessments/{assessment['id']}"

    all_questions = client.get(f"{base}/questions", headers=headers).json()
    situation = next((q for q in all_questions if q["is_active"] and q["is_situation_dependent"]), None)

    if situation is None:
        situation = next(q for q in all_questions if q["is_situation_dependent"])
        response = client.put(f"{base}/question-selection", json={"question_ids": [situation["question_id"]]}, headers=headers)
        assert response.status_code == 200, response.text

    questions = active_questions(client, headers, assessment["id"])
    fixed = [q for q in questions if not q["is_situation_dependent"]]
    q_a, q_b, q_c = fixed[0], fixed[1], situation

    # Fixed answers per person; every other question is answered 3.
    employee_answers = {
        q_a["question_id"]: [5, 4, 4, 3, 2],
        q_b["question_id"]: [1, 2, 2, 1, 3],
        q_c["question_id"]: ["N/A", 4, 4, 5, 3],
    }
    manager_answers = {
        q_a["question_id"]: [4, 4, 5],
        q_b["question_id"]: [4, 5, 4],
        q_c["question_id"]: [3, 3, 4],
    }

    code = public_code(client, headers, assessment["id"])

    for group, table, people in (("Employee", employee_answers, 5), ("Senior Manager", manager_answers, 3)):
        for person in range(people):
            submit_respondent(
                client, code, group,
                {q["question_id"]: table.get(q["question_id"], [3] * people)[person] for q in questions},
            )

    completed = client.post(f"{base}/complete", headers=headers)
    assert completed.status_code == 200, completed.text
    scores = client.post(f"{base}/calculate-scores", headers=headers).json()
    by_question = {q["question_id"]: q for q in scores["question_scores"]}

    expected_questions = [
        ("UT-SC-20a", q_a, "Employee 5,4,4,3,2; Manager 4,4,5",
         "E 18÷5 = 3.60; M 13÷3 = 4.33; combined (3.60+4.33)÷2 = 3.965; gap 0.73",
         {"employee_mean": "3.60", "manager_mean": "4.33", "combined_mean": "3.97", "opinion_gap": "0.73",
          "maturity_level": "Performing", "intervention_tier": "Not flagged"}),
        ("UT-SC-20b", q_b, "Employee 1,2,2,1,3; Manager 4,5,4",
         "E 9÷5 = 1.80; M 13÷3 = 4.33; combined (1.80+4.33)÷2 = 3.065; gap 2.53",
         {"employee_mean": "1.80", "manager_mean": "4.33", "combined_mean": "3.07", "opinion_gap": "2.53",
          "maturity_level": "Performing", "intervention_tier": "Medium"}),
        ("UT-SC-20c", q_c, "Employee N/A,4,4,5,3; Manager 3,3,4",
         "E 16÷4 = 4.00 (N/A left out); M 10÷3 = 3.33; combined (4.00+3.33)÷2 = 3.665; gap 0.67",
         {"employee_mean": "4.00", "manager_mean": "3.33", "combined_mean": "3.67", "opinion_gap": "0.67",
          "maturity_level": "Performing", "intervention_tier": "Not flagged"}),
    ]

    rows = []

    for row_id, question, answers, working, expected in expected_questions:
        result = by_question[question["question_id"]]
        actual = {key: str(result[key]) for key in expected}
        rows.append({
            "id": row_id,
            "title": f"Question {question['question_number']}",
            "input": answers,
            "working": working,
            "expected": ", ".join(expected.values()),
            "actual": ", ".join(actual.values()),
            "result": "Pass" if actual == expected else "Fail",
        })

    # Domain and overall results, calculated by hand from the question results.
    domain_of = {q["question_id"]: q["domain_name"] for q in questions}
    combined_by_domain: dict[str, list[Decimal]] = {}

    for q in scores["question_scores"]:
        combined_by_domain.setdefault(domain_of[q["question_id"]], []).append(Decimal(str(q["combined_mean"])))

    domain_names = list(dict.fromkeys(domain_of.values()))
    expected_domains = {
        name: half_up(sum(values) / len(values)) for name, values in combined_by_domain.items()
    }
    expected_overall = half_up(sum(expected_domains.values()) / 3)
    actual_domains = sorted(str(d["combined_mean"]) for d in scores["domain_scores"])

    rows.append({
        "id": "UT-SC-20d",
        "title": "Domain means",
        "input": "; ".join(f"{name}: {len(combined_by_domain[name])} questions" for name in domain_names),
        "working": "Average of each domain's question combined means: "
                   + "; ".join(f"{sum(combined_by_domain[n])} ÷ {len(combined_by_domain[n])}" for n in domain_names),
        "expected": ", ".join(str(expected_domains[n]) for n in domain_names),
        "actual": ", ".join(actual_domains),
        "result": "Pass" if sorted(str(v) for v in expected_domains.values()) == actual_domains else "Fail",
    })

    rows.append({
        "id": "UT-SC-20e",
        "title": "Overall result",
        "input": "The three domain means",
        "working": f"({' + '.join(str(expected_domains[n]) for n in domain_names)}) ÷ 3",
        "expected": f"{expected_overall} {get_maturity_level(expected_overall)}",
        "actual": f"{scores['overall_combined_mean']} {scores['overall_maturity_label']}",
        "result": "Pass" if (str(scores["overall_combined_mean"]), scores["overall_maturity_label"])
                  == (str(expected_overall), get_maturity_level(expected_overall)) else "Fail",
    })

    evidence("rows", rows)
    evidence("actual", "; ".join(f"{r['id']} {r['result']}" for r in rows))
    assert all(r["result"] == "Pass" for r in rows), rows
