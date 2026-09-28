"""System tests: what the downloaded PDFs actually contain, checked
against the results page they are meant to match."""

import pytest

from .helpers import (
    FakeGemini,
    auth_headers,
    completed_assessment,
    download_report,
    pdf_text,
    squash,
)

AREA = "report_content"

# Wording every report shares, then what each one must carry. The
# full report lists the entry counts in its cover table, the others in
# a header line, so match the part they have in common.
COMMON = ["Contents", "Opened", "online, 0 paper", "below Leading"]

REPORT_CASES = [
    (
        "ST-RPT-01",
        "Full assessment report",
        "report",
        [
            "Domain results",
            "Question results",
            "How scores and tiers are calculated",
            "High Override",
            "Hidden",
            "Any score",
            "AI analysis",
            "Priority actions",
            "Improvement roadmap",
        ],
    ),
    (
        "ST-RPT-02",
        "Business leader report",
        "report/business-leader",
        [
            "Maturity by domain",
            "Top strengths and priority areas",
            "Hidden combined means (High Override)",
            "AI analysis",
            "Next 90 days",
        ],
    ),
    (
        "ST-RPT-03",
        "Board report",
        "report/board",
        [
            "Governance view of maturity by domain",
            "Where workers and managers disagree",
            "High Override",
            "Executive summary",
            "Health and Safety at Work Act",
        ],
    ),
    (
        "ST-RPT-04",
        "Operational manager report",
        "report/operational-manager",
        [
            "Maturity by domain",
            "Question results",
            "Opinion gap and tiers",
            "High Override",
            "Hidden",
            "Prioritised action list",
            "Re-assessment readiness",
        ],
    ),
]


@pytest.fixture(scope="function")
def completed_with_ai(client, monkeypatch):
    headers = auth_headers(client)
    assessment, _code, _questions = completed_assessment(client, headers)
    FakeGemini(monkeypatch)
    response = client.post(
        f"/api/assessments/{assessment['id']}/ai-analysis/generate",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return headers, assessment


@pytest.mark.qa(area=AREA)
@pytest.mark.parametrize(
    "case",
    [
        pytest.param(
            {
                "id": case_id,
                "title": f"{name} content",
                "input": f"GET {path}?include_ai=true for a completed assessment",
                "expected": "Contents page, header line, ladders and every section present",
                "path": path,
                "sections": sections,
            },
            id=case_id,
        )
        for case_id, name, path, sections in REPORT_CASES
    ],
)
def test_report_content(client, completed_with_ai, case, evidence):
    headers, assessment = completed_with_ai
    response = download_report(
        client,
        headers,
        assessment["id"],
        case["path"],
        True,
    )
    assert response.status_code == 200, response.text

    text, pages = pdf_text(response.content)
    squashed = squash(text)

    missing = [
        wording
        for wording in COMMON + case["sections"]
        if squash(wording) not in squashed
    ]

    # A section listed in the contents and used as a heading appears
    # at least twice, which is how the contents page is verified.
    listed_twice = [
        section
        for section in case["sections"]
        if squashed.count(squash(section)) >= 2
    ]

    evidence(
        "actual",
        f"{pages} pages; missing wording: {missing or 'none'}; "
        f"{len(listed_twice)}/{len(case['sections'])} sections appear in both "
        "the contents and the body",
    )
    assert not missing
    assert listed_twice, "no section appeared in both the contents and the body"


@pytest.mark.qa(
    area=AREA,
    id="ST-RPT-05",
    title="Maturity is never shown as colour alone",
    input="All four reports, downloaded without AI analysis",
    expected="Every report names the maturity level in text and shows the distance to the next level",
)
def test_maturity_named_in_text(client, evidence):
    headers = auth_headers(client)
    assessment, _code, _questions = completed_assessment(client, headers)
    results = {}

    for name, path in (
        ("Full", "report"),
        ("Business leader", "report/business-leader"),
        ("Board", "report/board"),
        ("Operational manager", "report/operational-manager"),
    ):
        text = pdf_text(
            download_report(
                client,
                headers,
                assessment["id"],
                path,
                False,
            ).content
        )[0]
        squashed = squash(text)
        results[name] = all(
            squash(wording) in squashed
            for wording in ("Performing", "Developing", "Leading", "below Leading")
        )

    evidence("actual", ", ".join(f"{k}: {'yes' if v else 'no'}" for k, v in results.items()))
    assert all(results.values())


@pytest.mark.qa(
    area=AREA,
    id="ST-RPT-06",
    title="AI wording appears only when AI analysis is included",
    input="Each report downloaded as Review only, then With AI analysis",
    expected="The AI banner is absent from Review only and present with AI analysis",
)
def test_ai_banner_only_with_ai(client, completed_with_ai, evidence):
    headers, assessment = completed_with_ai
    banner = "WorkSafe-grounded improvement analysis"
    outcomes = {}

    for name, path in (
        ("Full", "report"),
        ("Business leader", "report/business-leader"),
        ("Board", "report/board"),
        ("Operational manager", "report/operational-manager"),
    ):
        without = squash(
            pdf_text(
                download_report(client, headers, assessment["id"], path, False).content
            )[0]
        )
        with_ai = squash(
            pdf_text(
                download_report(client, headers, assessment["id"], path, True).content
            )[0]
        )
        outcomes[name] = (
            squash(banner) not in without,
            squash(banner) in with_ai,
        )

    evidence(
        "actual",
        ", ".join(
            f"{name}: review only {'clean' if clean else 'HAS AI'}, "
            f"with AI {'present' if present else 'MISSING'}"
            for name, (clean, present) in outcomes.items()
        ),
    )
    assert all(clean and present for clean, present in outcomes.values())
