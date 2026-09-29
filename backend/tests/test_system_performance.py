"""NFR02: an assessment's results are available within 10 seconds of
completing it."""

import random
from time import perf_counter

import pytest

from .helpers import (
    REPORTS,
    active_questions,
    auth_headers,
    create_assessment,
    download_report,
    public_code,
    submit_respondent,
)

LIMIT_SECONDS = 10.0


def perf_case(case_id, employees, managers, run):
    return pytest.param(
        {
            "id": case_id,
            "title": f"{employees + managers} respondents ({employees} Employee, {managers} Senior Manager), run {run}",
            "employees": employees,
            "managers": managers,
            "expected": f"Results within {LIMIT_SECONDS:.0f} s",
        },
        id=case_id,
    )


CASES = [
    perf_case("ST-PERF-01", 15, 5, 1),
    perf_case("ST-PERF-02", 15, 5, 2),
    perf_case("ST-PERF-03", 15, 5, 3),
    perf_case("ST-PERF-04", 75, 25, 1),
]


@pytest.mark.qa(area="performance")
@pytest.mark.parametrize("case", CASES)
def test_complete_to_results(client, case, evidence):
    headers = auth_headers(client)
    assessment = create_assessment(client, headers)
    code = public_code(client, headers, assessment["id"])
    question_ids = [q["question_id"] for q in active_questions(client, headers, assessment["id"])]
    rng = random.Random(case["id"])

    for group, count in (("Employee", case["employees"]), ("Senior Manager", case["managers"])):
        for _ in range(count):
            submit_respondent(client, code, group, {qid: rng.randint(1, 5) for qid in question_ids})

    base = f"/api/assessments/{assessment['id']}"
    timings = {}

    start = perf_counter()

    t = perf_counter()
    completed = client.post(f"{base}/complete", headers=headers)
    timings["Complete assessment (scores calculated)"] = perf_counter() - t

    t = perf_counter()
    summary = client.get(base, headers=headers)
    timings["Load overall result"] = perf_counter() - t

    t = perf_counter()
    scores = client.post(f"{base}/calculate-scores", headers=headers)
    timings["Load question and domain scores"] = perf_counter() - t

    t = perf_counter()
    progress = client.get(f"{base}/submission-summary", headers=headers)
    timings["Load response totals"] = perf_counter() - t

    total = perf_counter() - start

    report_timings = {}

    for name, path in REPORTS.items():
        t = perf_counter()
        report = download_report(client, headers, assessment["id"], path, False)
        report_timings[name] = perf_counter() - t
        assert report.status_code == 200

    evidence("respondents", case["employees"] + case["managers"])
    evidence("timings", {k: round(v, 3) for k, v in timings.items()})
    evidence("report_timings", {k: round(v, 3) for k, v in report_timings.items()})
    evidence("total_seconds", round(total, 3))
    evidence("actual", f"{total:.3f} s ({len(scores.json()['question_scores'])} questions scored)")

    assert completed.status_code == summary.status_code == scores.status_code == progress.status_code == 200
    assert total < LIMIT_SECONDS
