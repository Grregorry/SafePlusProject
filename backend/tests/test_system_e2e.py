"""System test: registration through to report generation, driven
entirely through the API in the order a real organisation uses it."""

from collections import Counter

import pytest

from .helpers import (
    REPORTS,
    FakeGemini,
    active_questions,
    create_assessment,
    download_report,
    login,
    pdf_text,
    public_code,
    register,
    run_scenario,
)


@pytest.mark.qa(
    area="e2e",
    id="ST-E2E-01",
    title="Registration through to report generation",
    input="New organisation; 15 Employee + 5 Senior Manager online surveys, 32 questions each",
    expected="Every step succeeds and all four reports download as valid PDFs, with and without AI analysis",
)
def test_registration_to_report(client, monkeypatch, evidence):
    steps = []

    def step(action, expected, actual, ok):
        steps.append(
            {
                "step": len(steps) + 1,
                "action": action,
                "expected": expected,
                "actual": actual,
                "result": "Pass" if ok else "Fail",
            }
        )
        assert ok, f"{action}: {actual}"

    try:
        email = "e2e@example.com"
        company = "E2E Test Company"

        r = register(client, email, name=company)
        step("Register the organisation", "201, account created unverified",
             f"{r.status_code}, is_verified={r.json().get('is_verified')}",
             r.status_code == 201 and r.json()["is_verified"] is False)

        r = login(client, email)
        headers = {"Authorization": f"Bearer {r.json().get('access_token')}"}
        step("Log in", "200 with a bearer token", f"{r.status_code}, token_type={r.json().get('token_type')}",
             r.status_code == 200)

        r = client.post("/api/auth/resend-verification", headers=headers)
        token = r.json().get("verification_token")
        step("Request the verification link", "200 with a link token", f"{r.status_code}, token issued={bool(token)}",
             r.status_code == 200 and bool(token))

        r = client.get("/api/auth/verify", params={"token": token})
        me = client.get("/api/auth/me", headers=headers).json()
        step("Open the verification link", "Account verified", f"{r.status_code}, is_verified={me['is_verified']}",
             r.status_code == 200 and me["is_verified"] is True)

        assessment = create_assessment(client, headers, name="E2E assessment")
        questions = active_questions(client, headers, assessment["id"])
        step("Create an assessment", "Draft with the 32 compulsory questions active",
             f"status={assessment['status']}, {len(questions)} active questions",
             assessment["status"] == "draft" and len(questions) == 32)

        code = public_code(client, headers, assessment["id"])
        overview = client.get(f"/api/public/surveys/{code}").json()
        step("Open the public survey link", "Survey shows the organisation and 32 questions",
             f"code {code}, {overview['organisation_name']}, {overview['active_question_count']} questions",
             overview["organisation_name"] == company and overview["active_question_count"] == 32)

        question_ids = [q["question_id"] for q in questions]
        run_scenario(client, code, question_ids, employees=15, managers=5)
        summary = client.get(f"/api/assessments/{assessment['id']}/submission-summary", headers=headers).json()
        step("15 employees and 5 senior managers complete the survey", "20 submitted",
             f"{summary.get('submitted_total')} submitted", summary.get("submitted_total") == 20)

        open_assessment = client.get(f"/api/assessments/{assessment['id']}", headers=headers).json()
        scores = client.post(f"/api/assessments/{assessment['id']}/calculate-scores", headers=headers)
        report = download_report(client, headers, assessment["id"], "report", False)
        step("Results stay locked while the survey is open", "No overall score; scores and reports 409",
             f"status={open_assessment['status']}, overall={open_assessment['overall_combined_mean']}, "
             f"scores {scores.status_code}, report {report.status_code}",
             open_assessment["overall_combined_mean"] is None and scores.status_code == 409 and report.status_code == 409)

        r = client.post(f"/api/assessments/{assessment['id']}/complete", headers=headers)
        body = r.json()
        step("Complete the assessment", "200, completed, 32 questions scored",
             f"{r.status_code}, status={body.get('status')}, {body.get('questions_scored')} scored, "
             f"overall {body.get('overall_combined_mean')} {body.get('overall_maturity_label')}",
             r.status_code == 200 and body["status"] == "completed" and body["questions_scored"] == 32)

        scores = client.post(f"/api/assessments/{assessment['id']}/calculate-scores", headers=headers).json()
        tiers = Counter(q["intervention_tier"] for q in scores["question_scores"])
        step("View results", "32 question scores, 3 domain scores; tiers High 8, Medium 4, Low 4, Not flagged 16",
             f"{len(scores['question_scores'])} questions, {len(scores['domain_scores'])} domains, tiers {dict(tiers)}",
             len(scores["question_scores"]) == 32 and len(scores["domain_scores"]) == 3
             and tiers == Counter({"High": 8, "Medium": 4, "Low": 4, "Not flagged": 16}))

        fake = FakeGemini(monkeypatch)
        r = client.post(f"/api/assessments/{assessment['id']}/ai-analysis/generate", headers=headers)
        step("Generate the AI analysis (Gemini test double)", "200, completed, 5 priority actions",
             f"{r.status_code}, status={r.json().get('status')}, {len(r.json().get('priority_actions') or [])} priority actions",
             r.status_code == 200 and r.json()["status"] == "completed" and len(r.json()["priority_actions"]) == 5)

        for include_ai in (False, True):
            outcomes = []
            ok = True

            for name, path in REPORTS.items():
                r = download_report(client, headers, assessment["id"], path, include_ai)
                is_pdf = r.status_code == 200 and r.headers["content-type"] == "application/pdf" and r.content.startswith(b"%PDF")
                text, pages = pdf_text(r.content) if is_pdf else ("", 0)
                has_company = company in text
                filename_ok = ("-with-ai" in r.headers.get("content-disposition", "")) == include_ai
                ok = ok and is_pdf and has_company and filename_ok
                outcomes.append(f"{name}: {r.status_code}, {pages} pages, {len(r.content) // 1024} KB")

            step(f"Download all four reports {'with' if include_ai else 'without'} AI analysis",
                 "200 PDF for each, organisation named, correct filename", "; ".join(outcomes), ok)

        r = client.post(f"/api/public/surveys/{code}/submissions", json={"respondent_group": "Employee"})
        step("Survey link closes after completion", "409 'This survey is closed.'", f"{r.status_code} {r.json().get('detail')!r}",
             r.status_code == 409)

        step("Gemini called once for the whole run", "1 call", f"{fake.calls} call(s)", fake.calls == 1)
    finally:
        evidence("steps", steps)
