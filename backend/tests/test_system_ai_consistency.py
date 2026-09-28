"""FR19: one AI analysis pass feeds all three role reports, and every
report shows the same AI content."""

import pytest

from app.services.priority_actions import select_priority_action_candidates

from .helpers import (
    OVERALL_SUMMARY,
    REPORTS,
    ROADMAP_OBJECTIVE,
    FakeGemini,
    action_text,
    auth_headers,
    completed_assessment,
    download_report,
    pdf_text,
    squash,
)

ROLE_REPORTS = {
    name: path for name, path in REPORTS.items() if name != "Full assessment report"
}


def positions(text, needles):
    squashed = squash(text)
    return [squashed.find(squash(needle)) for needle in needles]


@pytest.mark.qa(
    area="consistency",
    id="ST-FR19-01",
    title="A single AI analysis pass produces all three reports consistently",
    input="Completed assessment (15 Employee + 5 Senior Manager); AI analysis generated once; "
          "business leader, board and operational manager reports downloaded with AI analysis, twice",
    expected="Gemini called once; each report shows the same summary and priority actions, "
             "in the rule-engine order; downloading again changes nothing",
)
def test_single_pass_consistency(client, monkeypatch, evidence):
    checks = []

    def check(name, expected, actual, ok):
        checks.append({"check": name, "expected": expected, "actual": actual, "result": "Pass" if ok else "Fail"})
        assert ok, f"{name}: {actual}"

    try:
        headers = auth_headers(client)
        assessment, _, _ = completed_assessment(client, headers)
        fake = FakeGemini(monkeypatch)

        generated = client.post(f"/api/assessments/{assessment['id']}/ai-analysis/generate", headers=headers).json()
        check("One AI pass", "Gemini called once", f"{fake.calls} call(s), status {generated['status']}",
              fake.calls == 1 and generated["status"] == "completed")

        rule_order = [c["question_id"] for c in select_priority_action_candidates(fake.captured["questions"])]
        saved_order = [a["question_id"] for a in generated["priority_actions"]]
        check("Priority actions follow the rule engine", f"Order {rule_order}", f"Order {saved_order}",
              saved_order == rule_order)

        actions = [action_text(qid) for qid in saved_order]
        texts = {}

        for name, path in REPORTS.items():
            response = download_report(client, headers, assessment["id"], path, True)
            assert response.status_code == 200, response.text
            texts[name] = pdf_text(response.content)[0]

        expectations = {
            "Business leader report": ("summary and top 3 priority actions", [OVERALL_SUMMARY], actions[:3]),
            "Board report": ("summary", [OVERALL_SUMMARY], []),
            "Operational manager report": ("all 5 priority actions", [], actions),
            "Full assessment report": ("summary, all 5 priority actions and roadmap",
                                       [OVERALL_SUMMARY, ROADMAP_OBJECTIVE], actions),
        }

        for name, (description, fixed, ordered) in expectations.items():
            found_fixed = [p >= 0 for p in positions(texts[name], fixed)]
            found_ordered = positions(texts[name], ordered)
            in_order = all(p >= 0 for p in found_ordered) and found_ordered == sorted(found_ordered)
            check(f"{name} shows the saved AI content", f"Same {description}, in priority order",
                  f"summary/roadmap found {found_fixed}; {sum(p >= 0 for p in found_ordered)}/{len(ordered)} actions found, "
                  f"in order: {in_order}",
                  all(found_fixed) and in_order)

        before = client.get(f"/api/assessments/{assessment['id']}/ai-analysis", headers=headers).json()
        repeat_ok = True

        for name, path in ROLE_REPORTS.items():
            again = pdf_text(download_report(client, headers, assessment["id"], path, True).content)[0]
            repeat_ok = repeat_ok and [p >= 0 for p in positions(again, [OVERALL_SUMMARY, *actions])] == \
                [p >= 0 for p in positions(texts[name], [OVERALL_SUMMARY, *actions])]

        after = client.get(f"/api/assessments/{assessment['id']}/ai-analysis", headers=headers).json()
        check("Downloading again reuses the same analysis",
              "No new Gemini call; same analysis id and time; same AI content",
              f"{fake.calls} call(s); id {before['id']}→{after['id']}; generated_at unchanged "
              f"{before['generated_at'] == after['generated_at']}; content same {repeat_ok}",
              fake.calls == 1 and before["id"] == after["id"]
              and before["generated_at"] == after["generated_at"] and repeat_ok)

        leaks = []

        for name, path in REPORTS.items():
            plain = pdf_text(download_report(client, headers, assessment["id"], path, False).content)[0]

            if any(p >= 0 for p in positions(plain, [OVERALL_SUMMARY, ROADMAP_OBJECTIVE, *actions])):
                leaks.append(name)

        check("Reports without AI contain no AI text", "No AI text in any of the four reports",
              f"AI text found in: {leaks or 'none'}", not leaks)
    finally:
        evidence("checks", checks)
