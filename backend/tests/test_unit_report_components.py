"""Unit tests: the shared report building blocks that make a PDF read
the same way as the results page."""

from decimal import Decimal

import pytest

from app.services.report_components import (
    combined_display,
    distance_text,
    entry_counts,
    format_long_date,
    is_hidden,
    maturity_level,
    meta_line,
    tier_label,
)

from .helpers import (
    active_questions,
    auth_headers,
    create_assessment,
    public_code,
    submit_respondent,
)

AREA = "report_components"


def case(case_id, title, value, expected, **extra):
    return pytest.param(
        {
            "id": case_id,
            "title": title,
            "input": value,
            "expected": expected,
            **extra,
        },
        id=case_id,
    )


MATURITY_CASES = [
    case("UT-RP-01", "Maturity shown on a report follows the scoring bands", "2.50", "Developing"),
    case("UT-RP-02", "Maturity shown on a report follows the scoring bands", "2.51", "Performing"),
    case("UT-RP-03", "Maturity shown on a report follows the scoring bands", "4.49", "Performing"),
    case("UT-RP-04", "Maturity shown on a report follows the scoring bands", "4.50", "Leading"),
]


@pytest.mark.qa(area=AREA)
@pytest.mark.parametrize("case", MATURITY_CASES)
def test_maturity_level(case, evidence):
    actual = maturity_level(Decimal(case["input"]))
    evidence("actual", actual)
    assert actual == case["expected"]


DISTANCE_CASES = [
    case("UT-RP-05", "Ladder caption: distance to the next level", "3.76", "0.74 below Leading"),
    case("UT-RP-06", "Ladder caption: distance to the next level", "2.20", "0.30 below Performing"),
    case("UT-RP-07", "Ladder caption at the top of the scale", "4.60", "At the highest level"),
]


@pytest.mark.qa(area=AREA)
@pytest.mark.parametrize("case", DISTANCE_CASES)
def test_distance_text(case, evidence):
    actual = distance_text(Decimal(case["input"]))
    evidence("actual", actual)
    assert actual == case["expected"]


HIDDEN_CASES = [
    case("UT-RP-08", "A gap of 3.00 or more hides the combined mean", "3.00", ("High Override", "Hidden"), tier="Low"),
    case("UT-RP-09", "Just under the hiding threshold", "2.99", ("Low", "3.40"), tier="Low"),
    case("UT-RP-10", "An ordinary result keeps its tier and mean", "0.40", ("Medium", "3.40"), tier="Medium"),
]


@pytest.mark.qa(area=AREA)
@pytest.mark.parametrize("case", HIDDEN_CASES)
def test_tier_and_combined_display(case, evidence):
    gap = Decimal(case["input"])
    actual = (
        tier_label(case["tier"], gap),
        combined_display(Decimal("3.40"), gap),
    )
    evidence("actual", f"{actual[0]}, combined shown as {actual[1]}")
    assert actual == case["expected"]
    assert is_hidden(gap) is (case["expected"][1] == "Hidden")


@pytest.mark.qa(
    area=AREA,
    id="UT-RP-11",
    title="Report header line matches the results page",
    input="Assessment opened and closed, with 20 online and 0 paper entries",
    expected="Opened <date> · Closed <date> · 20 entries (20 online, 0 paper)",
)
def test_meta_line(client, evidence):
    from datetime import UTC, datetime

    from app.models import Assessment

    assessment = Assessment(
        organisation_id=1,
        organisation_assessment_number=1,
        name="Meta line",
        created_at=datetime(2026, 9, 1, tzinfo=UTC),
        completed_at=datetime(2026, 9, 14, tzinfo=UTC),
    )

    line = meta_line(assessment, 20, 0)
    single = meta_line(assessment, 1, 0)
    evidence("actual", f"{line}  |  one entry: {single}")
    assert line == (
        f"Opened {format_long_date(assessment.created_at)} · "
        f"Closed {format_long_date(assessment.completed_at)} · "
        "20 entries (20 online, 0 paper)"
    )
    assert "1 entry (1 online, 0 paper)" in single


@pytest.mark.qa(
    area=AREA,
    id="UT-RP-12",
    title="Reports count the same entries as the results page",
    input="6 online surveys submitted, no paper entries",
    expected="(6 online, 0 paper)",
)
def test_entry_counts(client, evidence):
    from sqlalchemy import select

    from app.db.session import SessionLocal
    from app.models import Assessment

    headers = auth_headers(client)
    assessment = create_assessment(client, headers)
    code = public_code(client, headers, assessment["id"])
    answers = {
        question["question_id"]: 4
        for question in active_questions(client, headers, assessment["id"])
    }

    for _ in range(5):
        submit_respondent(client, code, "Employee", answers)

    submit_respondent(client, code, "Senior Manager", answers)

    with SessionLocal() as database:
        stored = database.scalar(
            select(Assessment).where(Assessment.id == assessment["id"])
        )
        online, paper = entry_counts(stored, database)

    evidence("actual", f"({online} online, {paper} paper)")
    assert (online, paper) == (6, 0)
