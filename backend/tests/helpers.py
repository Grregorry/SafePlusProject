"""Helpers that drive the API the same way the frontend and the public
survey do."""

from __future__ import annotations

import io
import json
import re
from types import SimpleNamespace

from pypdf import PdfReader

from app.services import gemini_analysis

PASSWORD = "Correct-Horse-42"

OPTIONS = {
    1: "Strongly Disagree",
    2: "Disagree",
    3: "Neither Agree nor Disagree",
    4: "Agree",
    5: "Strongly Agree",
}

REPORTS = {
    "Full assessment report": "report",
    "Business leader report": "report/business-leader",
    "Board report": "report/board",
    "Operational manager report": "report/operational-manager",
}


# ---------------------------------------------------------------------------
# Accounts


def register(client, email, name="Test Company", category="Construction", password=PASSWORD):
    return client.post(
        "/api/auth/register",
        json={
            "name": name,
            "category": category,
            "email": email,
            "password": password,
        },
    )


def login(client, email, password=PASSWORD):
    return client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )


def auth_headers(client, email="owner@example.com", name="Test Company"):
    response = register(client, email, name=name)
    assert response.status_code == 201, response.text
    token = login(client, email).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Assessments and surveys


def create_assessment(client, headers, name="Test assessment"):
    response = client.post(
        "/api/assessments",
        json={"name": name},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def public_code(client, headers, assessment_id):
    response = client.get(
        f"/api/assessments/{assessment_id}/survey-access",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()["public_code"]


def active_questions(client, headers, assessment_id):
    response = client.get(
        f"/api/assessments/{assessment_id}/questions",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return [question for question in response.json() if question["is_active"]]


def start_submission(client, code, group):
    response = client.post(
        f"/api/public/surveys/{code}/submissions",
        json={"respondent_group": group},
    )
    assert response.status_code == 201, response.text
    return response.json()["submission_token"]


def answer(client, token, question_id, value):
    return client.put(
        f"/api/public/submissions/{token}/answers",
        json={
            "question_id": question_id,
            "response_option": OPTIONS.get(value, value),
        },
    )


def submit_respondent(client, code, group, answers):
    """answers maps question_id to 1-5 (or "N/A")."""

    token = start_submission(client, code, group)

    for question_id, value in answers.items():
        response = answer(client, token, question_id, value)
        assert response.status_code == 200, response.text

    response = client.post(f"/api/public/submissions/{token}/submit")
    assert response.status_code == 200, response.text
    return response.json()


# Each question gets one of these (employee answer, manager answer)
# profiles, so the expected tier of every question is known in advance.
PROFILES = {
    "high override": (1, 5),  # combined 3.00, gap 4.00 -> High (override)
    "high": (1, 3),           # combined 2.00, gap 2.00 -> High
    "medium": (2, 3),         # combined 2.50, gap 1.00 -> Medium
    "low": (3, 4),            # combined 3.50, gap 1.00 -> Low
    "not flagged": (4, 5),    # combined 4.50, gap 1.00 -> Not flagged
}


def profile_for(index):
    return ["high override", "high", "medium", "low"][index % 8] if index % 8 < 4 else "not flagged"


def scenario_answers(question_ids):
    employee = {}
    manager = {}

    for index, question_id in enumerate(question_ids):
        employee[question_id], manager[question_id] = PROFILES[profile_for(index)]

    return employee, manager


def run_scenario(client, code, question_ids, employees=15, managers=5):
    employee, manager = scenario_answers(question_ids)

    for _ in range(employees):
        submit_respondent(client, code, "Employee", employee)

    for _ in range(managers):
        submit_respondent(client, code, "Senior Manager", manager)


def completed_assessment(client, headers, employees=15, managers=5, name="Test assessment"):
    """Creates an assessment, runs the standard scenario and completes it."""

    assessment = create_assessment(client, headers, name=name)
    code = public_code(client, headers, assessment["id"])
    question_ids = [q["question_id"] for q in active_questions(client, headers, assessment["id"])]
    run_scenario(client, code, question_ids, employees, managers)

    response = client.post(
        f"/api/assessments/{assessment['id']}/complete",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return assessment, code, question_ids


def download_report(client, headers, assessment_id, path, include_ai):
    return client.get(
        f"/api/assessments/{assessment_id}/{path}",
        params={"include_ai": str(include_ai).lower()},
        headers=headers,
    )


def pdf_text(content):
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages), len(reader.pages)


def squash(text):
    """PDF text wraps lines, so compare with all whitespace removed."""

    return re.sub(r"\s+", "", text)


# ---------------------------------------------------------------------------
# Gemini test double

OVERALL_SUMMARY = "FR19 summary marker. Leadership is visible but worker voice on hazards is limited."
ROADMAP_OBJECTIVE = "FR19 roadmap marker objective"


def action_text(question_id):
    return f"FR19 action marker {question_id} hold a toolbox talk"


class FakeAPIError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class FakeGemini:
    """Stands in for google.genai.Client so tests can control what the
    AI returns (or how it fails) without calling Google."""

    def __init__(self, monkeypatch, *, error=None, text=None, mutate=None):
        self.calls = 0
        self.captured: dict = {}
        self.error = error
        self.text = text
        self.mutate = mutate

        monkeypatch.setattr(gemini_analysis.settings, "gemini_api_key", "test-key")

        original = gemini_analysis.build_assessment_data

        def capture(assessment, database):
            self.captured = original(assessment, database)
            return self.captured

        monkeypatch.setattr(gemini_analysis, "build_assessment_data", capture)

        fake = self

        class _Models:
            def generate_content(self, **kwargs):
                fake.calls += 1

                if fake.error is not None:
                    raise fake.error

                if fake.text is not None:
                    return SimpleNamespace(text=fake.text)

                payload = fake.payload()

                if fake.mutate is not None:
                    fake.mutate(payload)

                return SimpleNamespace(text=json.dumps(payload))

        class _Client:
            def __init__(self, api_key):
                self.models = _Models()

        monkeypatch.setattr(gemini_analysis.genai, "Client", _Client)

    def payload(self):
        data = self.captured

        return {
            "overall_summary": OVERALL_SUMMARY,
            "key_strengths": ["Managers report strong commitment to safety."],
            "key_risks": ["Workers and managers disagree on hazard reporting."],
            "domain_summaries": [
                {
                    "domain_name": domain["domain_name"],
                    "score": domain["combined_mean"],
                    "maturity_level": domain["maturity_level"],
                    "summary": f"Summary for {domain['domain_name']}.",
                    "strengths": [],
                    "improvement_areas": [],
                    "source_ids": ["WS-SP-METHODOLOGY"],
                }
                for domain in data["domains"]
            ],
            "priority_actions": [
                {
                    "question_id": candidate["question_id"],
                    "reason": f"Reason for question {candidate['question_id']}.",
                    "recommended_action": action_text(candidate["question_id"]),
                    "source_ids": ["WS-SP-RESOURCES"],
                    "source_relevance": "SafePlus improvement resources.",
                }
                for candidate in data["priority_action_candidates"]
            ],
            "roadmap": [
                {
                    "timeframe": "0-3 months",
                    "objective": ROADMAP_OBJECTIVE,
                    "actions": ["Run worker engagement sessions."],
                    "success_indicator": "Opinion gaps below 1.50 at reassessment.",
                    "source_ids": ["WS-SP-OVERVIEW"],
                }
            ],
            "limitations": ["Based on survey responses only."],
        }
