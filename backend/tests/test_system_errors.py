"""NFR11: error and failure states are handled with a clear message,
without losing data, and the rest of the system keeps working."""

import pytest
from sqlalchemy.exc import OperationalError

from app import main as main_module
from app.services import gemini_analysis

from .helpers import (
    FakeAPIError,
    FakeGemini,
    active_questions,
    answer,
    auth_headers,
    completed_assessment,
    create_assessment,
    download_report,
    pdf_text,
    public_code,
    register,
    start_submission,
    submit_respondent,
)

AREA = "errors"


def ai_case(case_id, title, expected_status, message, **fake):
    return pytest.param(
        {
            "id": case_id,
            "title": title,
            "expected": f"{expected_status} '{message}…'; analysis marked failed; scores kept; reports still download without AI",
            "status": expected_status,
            "message": message,
            "fake": fake,
        },
        id=case_id,
    )


def _drop_one_action(payload):
    payload["priority_actions"] = payload["priority_actions"][:-1]


def _bad_source(payload):
    payload["roadmap"][0]["source_ids"] = ["MADE-UP-SOURCE"]


AI_CASES = [
    ai_case("ST-ERR-01", "Gemini overloaded (HTTP 503)", 502, "Gemini is busy right now",
            error=FakeAPIError(503, "UNAVAILABLE")),
    ai_case("ST-ERR-02", "Gemini quota or rate limit reached (HTTP 429)", 502, "Gemini's usage limit has been reached",
            error=FakeAPIError(429, "RESOURCE_EXHAUSTED")),
    ai_case("ST-ERR-03", "No internet / other Gemini failure", 502, "Gemini could not generate the analysis",
            error=ConnectionError("network unreachable")),
    ai_case("ST-ERR-04", "Gemini returns an empty response", 502, "Gemini returned an empty response", text=""),
    ai_case("ST-ERR-05", "Gemini returns malformed JSON", 502, "Gemini returned an invalid analysis format",
            text="{not valid json"),
    ai_case("ST-ERR-06", "Gemini cites a source outside the approved WorkSafe list", 502,
            "Gemini referenced unsupported SafePlus sources", mutate=_bad_source),
    ai_case("ST-ERR-07", "Gemini drops one of the rule-engine priority actions", 502,
            "Gemini's priority actions did not match", mutate=_drop_one_action),
    ai_case("ST-ERR-08", "Gemini API key not configured", 502, "GEMINI_API_KEY is not configured", no_key=True),
    ai_case("ST-ERR-09", "Unexpected internal error while saving the analysis", 500,
            "An unexpected error occurred while generating AI analysis", internal=True),
]


@pytest.mark.qa(area=AREA)
@pytest.mark.parametrize("case", AI_CASES)
def test_ai_failures(client, monkeypatch, case, evidence):
    headers = auth_headers(client)
    assessment, _, _ = completed_assessment(client, headers, employees=4, managers=1)
    before = client.get(f"/api/assessments/{assessment['id']}", headers=headers).json()

    options = dict(case["fake"])
    no_key = options.pop("no_key", False)
    internal = options.pop("internal", False)
    FakeGemini(monkeypatch, **options)

    if no_key:
        monkeypatch.setattr(gemini_analysis.settings, "gemini_api_key", None)

    if internal:
        def broken(*args, **kwargs):
            raise RuntimeError("simulated bug")

        monkeypatch.setattr(gemini_analysis, "validate_priority_action_question_ids", broken)

    response = client.post(f"/api/assessments/{assessment['id']}/ai-analysis/generate", headers=headers)
    detail = response.json().get("detail", "")
    analysis = client.get(f"/api/assessments/{assessment['id']}/ai-analysis", headers=headers).json()
    after = client.get(f"/api/assessments/{assessment['id']}", headers=headers).json()
    report = download_report(client, headers, assessment["id"], "report", True)
    report_text = pdf_text(report.content)[0] if report.status_code == 200 else ""
    fallback = "No AI analysis has been included" in report_text

    evidence(
        "actual",
        f"{response.status_code} {detail!r}; analysis status '{analysis.get('status')}'; "
        f"overall score {before['overall_combined_mean']}→{after['overall_combined_mean']}; "
        f"report with AI → {report.status_code}, shows 'no AI analysis included': {fallback}",
    )
    assert response.status_code == case["status"]
    assert detail.startswith(case["message"])
    assert analysis["status"] == "failed"
    assert after["overall_combined_mean"] == before["overall_combined_mean"]
    assert report.status_code == 200 and fallback


@pytest.mark.qa(
    area=AREA,
    id="ST-ERR-10",
    title="Retry after an AI failure",
    input="Generate while Gemini is overloaded, then generate again once it recovers",
    expected="First 502 and 'failed'; retry 200 and 'completed'",
)
def test_ai_retry_after_failure(client, monkeypatch, evidence):
    headers = auth_headers(client)
    assessment, _, _ = completed_assessment(client, headers, employees=4, managers=1)
    fake = FakeGemini(monkeypatch, error=FakeAPIError(503, "UNAVAILABLE"))
    first = client.post(f"/api/assessments/{assessment['id']}/ai-analysis/generate", headers=headers)
    fake.error = None
    second = client.post(f"/api/assessments/{assessment['id']}/ai-analysis/generate", headers=headers)
    evidence("actual", f"first {first.status_code}; retry {second.status_code} status '{second.json().get('status')}'")
    assert first.status_code == 502
    assert second.status_code == 200 and second.json()["status"] == "completed"


@pytest.mark.qa(
    area=AREA,
    id="ST-ERR-11",
    title="Survey answer and submission errors",
    input="Senior Manager picks N/A; Employee picks N/A on a question that doesn't allow it; "
          "submit with 1 of 32 answered; change an answer after submitting",
    expected="400, 400, 400 with the count, 409",
)
def test_survey_answer_errors(client, evidence):
    headers = auth_headers(client)
    assessment = create_assessment(client, headers)
    code = public_code(client, headers, assessment["id"])
    questions = active_questions(client, headers, assessment["id"])
    fixed_question = next(q for q in questions if not q["is_situation_dependent"])

    manager = start_submission(client, code, "Senior Manager")
    manager_na = answer(client, manager, questions[0]["question_id"], "N/A")

    employee = start_submission(client, code, "Employee")
    employee_na = answer(client, employee, fixed_question["question_id"], "N/A")
    answer(client, employee, questions[0]["question_id"], 4)
    early = client.post(f"/api/public/submissions/{employee}/submit")

    token = submit_respondent(client, code, "Employee", {q["question_id"]: 3 for q in questions})["submission_token"]
    edit = answer(client, token, questions[0]["question_id"], 5)

    evidence(
        "actual",
        f"manager N/A {manager_na.status_code}; employee N/A {employee_na.status_code}; "
        f"early submit {early.status_code} {early.json()['detail']!r}; edit after submit {edit.status_code}",
    )
    assert manager_na.status_code == 400 and employee_na.status_code == 400
    assert early.status_code == 400 and "1 of 32" in early.json()["detail"]
    assert edit.status_code == 409


@pytest.mark.qa(
    area=AREA,
    id="ST-ERR-12",
    title="Unknown or closed survey links",
    input="Made-up survey code; made-up submission token; survey link after the assessment is completed",
    expected="404, 404, 409 'This survey is closed.'",
)
def test_survey_link_errors(client, evidence):
    headers = auth_headers(client)
    _, code, _ = completed_assessment(client, headers, employees=4, managers=1)
    unknown_code = client.get("/api/public/surveys/SP-NOTREAL")
    unknown_token = client.get("/api/public/submissions/not-a-real-token")
    closed = client.post(f"/api/public/surveys/{code}/submissions", json={"respondent_group": "Employee"})
    evidence("actual", f"{unknown_code.status_code}, {unknown_token.status_code}, {closed.status_code} {closed.json()['detail']!r}")
    assert unknown_code.status_code == 404 and unknown_token.status_code == 404
    assert closed.status_code == 409


@pytest.mark.qa(
    area=AREA,
    id="ST-ERR-13",
    title="Completing an assessment without enough responses",
    input="4 responses in total; then 5 responses but all from employees",
    expected="400 'At least 5 responses… It has 4 so far.'; 400 listing questions missing Senior Manager answers",
)
def test_completion_errors(client, evidence):
    headers = auth_headers(client)
    assessment = create_assessment(client, headers)
    code = public_code(client, headers, assessment["id"])
    answers = {q["question_id"]: 4 for q in active_questions(client, headers, assessment["id"])}

    for _ in range(4):
        submit_respondent(client, code, "Employee", answers)

    too_few = client.post(f"/api/assessments/{assessment['id']}/complete", headers=headers)
    submit_respondent(client, code, "Employee", answers)
    one_group = client.post(f"/api/assessments/{assessment['id']}/complete", headers=headers)
    missing = one_group.json()["detail"]["incomplete_questions"]
    status = client.get(f"/api/assessments/{assessment['id']}", headers=headers).json()["status"]

    evidence(
        "actual",
        f"{too_few.status_code} {too_few.json()['detail']!r}; {one_group.status_code} "
        f"{len(missing)} questions missing {missing[0]['missing_groups']}; assessment still '{status}'",
    )
    assert too_few.status_code == 400 and "It has 4 so far" in too_few.json()["detail"]
    assert one_group.status_code == 400 and len(missing) == 32
    assert missing[0]["missing_groups"] == ["Senior Manager"]
    assert status == "in_progress"


@pytest.mark.qa(
    area=AREA,
    id="ST-ERR-14",
    title="Results are locked while the assessment is open",
    input="Calculate scores, download a report and generate AI analysis before completion",
    expected="409 for each; no scores returned",
)
def test_results_locked(client, evidence):
    headers = auth_headers(client)
    assessment = create_assessment(client, headers)
    base = f"/api/assessments/{assessment['id']}"
    scores = client.post(f"{base}/calculate-scores", headers=headers)
    report = download_report(client, headers, assessment["id"], "report/board", False)
    ai = client.post(f"{base}/ai-analysis/generate", headers=headers)
    evidence("actual", f"scores {scores.status_code}, report {report.status_code}, AI {ai.status_code}")
    assert scores.status_code == report.status_code == ai.status_code == 409


@pytest.mark.qa(
    area=AREA,
    id="ST-ERR-15",
    title="Email provider unavailable",
    input="Request a verification link when no email provider is configured",
    expected="The link is returned on screen instead of being emailed, and it works",
)
def test_email_fallback(client, evidence):
    headers = auth_headers(client)
    response = client.post("/api/auth/resend-verification", headers=headers)
    verified = client.get("/api/auth/verify", params={"token": response.json()["verification_token"]})
    evidence("actual", f"{response.status_code} {response.json()['message'][:70]!r}…; link → {verified.status_code}")
    assert response.status_code == 200 and verified.status_code == 200


@pytest.mark.qa(
    area=AREA,
    id="ST-ERR-16",
    title="Database unavailable",
    input="Health check while the database connection fails",
    expected="503 'Database connection failed' (no crash, no internal details)",
)
def test_database_unavailable(client, monkeypatch, evidence):
    def fail():
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    monkeypatch.setattr(main_module.engine, "connect", fail)
    response = client.get("/database/health")
    evidence("actual", f"{response.status_code} {response.json()}")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database connection failed"}


@pytest.mark.qa(
    area=AREA,
    id="ST-ERR-17",
    title="Invalid input is rejected with a validation error",
    input="Register with a 3-character password; create an assessment with an empty name",
    expected="422 for both",
)
def test_validation_errors(client, evidence):
    registration = register(client, "x@example.com", password="abc")
    headers = auth_headers(client)
    empty_name = client.post("/api/assessments", json={"name": ""}, headers=headers)
    evidence("actual", f"registration {registration.status_code}, assessment {empty_name.status_code}")
    assert registration.status_code == 422 and empty_name.status_code == 422
