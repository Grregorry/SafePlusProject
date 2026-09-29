from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.hswa_references import HSWA_DISCLAIMER, HSWA_REFERENCES
from app.models import (
    AIAnalysis,
    Assessment,
    AssessmentQuestion,
    Domain,
    Organisation,
    Question,
    QuestionScore,
)
from app.services.report_components import (
    distance_text,
    entry_counts,
    is_hidden,
    maturity_chip,
    meta_line,
    tier_chip,
)
from app.services.reports.blocks import (
    ai_section_header,
    contents_block,
    draw_page_header_footer,
    overall_result_card,
    ReportDocTemplate,
    section_heading,
)
from app.services.reports.data import fetch_domain_rows
from app.services.reports.helpers import html_text, score_text
from app.services.reports.styles import build_styles, DARK_CYAN, SLATE_200


def cover_section(
    assessment: Assessment,
    organisation: Organisation,
    online_entries: int,
    paper_entries: int,
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Cover page, contents page and the governance heading."""

    story: list[Any] = [
        Spacer(1, 9 * mm),
        Paragraph(
            "SafePlus Board Report",
            styles["title"],
        ),
        Paragraph(
            (
                f"Assessment "
                f"{assessment.organisation_assessment_number}: "
                f"{html_text(assessment.name)}"
            ),
            styles["subtitle"],
        ),
        Paragraph(
            html_text(organisation.name),
            styles["subtitle"],
        ),
        Paragraph(
            html_text(
                meta_line(
                    assessment,
                    online_entries,
                    paper_entries,
                )
            ),
            styles["small"],
        ),
        Spacer(1, 4 * mm),
        Paragraph(
            html_text(HSWA_DISCLAIMER),
            styles["callout"],
        ),
        Spacer(1, 6 * mm),
        overall_result_card(assessment, styles),
        Spacer(1, 8 * mm),
    ]

    story.extend(contents_block(styles, own_page=False))
    story.append(
        section_heading(
            "Governance view of maturity by domain",
            styles,
        )
    )

    return story


def domain_table_section(
    domain_rows: list[Any],
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Governance view of maturity by domain."""

    story: list[Any] = []

    if domain_rows:
        table_data: list[list[Any]] = [
            [
                Paragraph(
                    "<b>Domain</b>",
                    styles["table_header"],
                ),
                Paragraph(
                    "<b>Combined mean</b>",
                    styles["table_header"],
                ),
                Paragraph(
                    "<b>Maturity level</b>",
                    styles["table_header"],
                ),
                Paragraph(
                    "<b>Governance framing</b>",
                    styles["table_header"],
                ),
            ]
        ]

        for (
            domain_name,
            combined_mean,
            maturity,
        ) in domain_rows:
            if maturity == "Developing":
                framing = (
                    "Material risk exposure — requires board "
                    "attention and a documented improvement plan."
                )
            elif maturity == "Performing":
                framing = (
                    "Acceptable but improvable — monitor progress "
                    "at the next review cycle."
                )
            else:
                framing = (
                    "Leading practice — sustain current governance "
                    "and resourcing."
                )

            table_data.append(
                [
                    Paragraph(
                        html_text(domain_name),
                        styles["table_cell"],
                    ),
                    Paragraph(
                        (
                            f"<b>{score_text(combined_mean)}</b><br/>"
                            f"{html_text(distance_text(combined_mean))}"
                        ),
                        styles["table_cell"],
                    ),
                    maturity_chip(
                        str(maturity),
                        styles,
                        width=26 * mm,
                    ),
                    Paragraph(
                        html_text(framing),
                        styles["table_cell"],
                    ),
                ]
            )

        domain_table = Table(
            table_data,
            colWidths=[
                34 * mm,
                30 * mm,
                30 * mm,
                74 * mm,
            ],
        )

        domain_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        DARK_CYAN,
                    ),
                    ("BOX", (0, 0), (-1, -1), 0.5, SLATE_200),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        SLATE_200,
                    ),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        story.extend([domain_table, Spacer(1, 4 * mm)])

        material_risk_domains = [
            name
            for name, _mean, level in domain_rows
            if level == "Developing"
        ]

        if material_risk_domains:
            plural = (
                "is"
                if len(material_risk_domains) == 1
                else "are"
            )

            story.append(
                Paragraph(
                    (
                        "<b>Material risk exposure:</b> "
                        f"{html_text(', '.join(material_risk_domains))} "
                        f"{plural} in the Developing maturity range and "
                        "flagged as material risk requiring board-level "
                        "attention."
                    ),
                    styles["callout"],
                )
            )
        else:
            story.append(
                Paragraph(
                    (
                        "No domains are currently flagged as material "
                        "risk (Developing range)."
                    ),
                    styles["body"],
                )
            )
    else:
        story.append(
            Paragraph(
                "Domain scores are not available.",
                styles["body"],
            )
        )

    return story


def disagreement_section(
    question_rows: list[Any],
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Questions where workers and managers disagree."""

    story: list[Any] = []

    override_rows = [
        row for row in question_rows if is_hidden(row[4])
    ]

    story.extend(
        [
            Spacer(1, 8 * mm),
            section_heading(
                "Where workers and managers disagree",
                styles,
            ),
            Paragraph(
                (
                    "A combined mean is hidden where the Employee and "
                    "Senior Manager means differ by 3.00 or more, because "
                    "an average would mask their opposing views. These "
                    "questions are treated as High Override: the "
                    "disagreement itself is the finding."
                ),
                styles["body"],
            ),
        ]
    )

    if override_rows:
        override_data: list[list[Any]] = [
            [
                Paragraph(
                    "<b>Question</b>",
                    styles["table_header"],
                ),
                Paragraph(
                    "<b>Domain</b>",
                    styles["table_header"],
                ),
                Paragraph(
                    "<b>Tier</b>",
                    styles["table_header"],
                ),
                Paragraph(
                    "<b>Employee</b>",
                    styles["table_header"],
                ),
                Paragraph(
                    "<b>Senior Manager</b>",
                    styles["table_header"],
                ),
                Paragraph(
                    "<b>Opinion gap</b>",
                    styles["table_header"],
                ),
            ]
        ]

        for row in override_rows:
            override_data.append(
                [
                    Paragraph(
                        f"<b>{html_text(row[0])}</b>",
                        styles["table_cell"],
                    ),
                    Paragraph(
                        html_text(row[1]),
                        styles["table_cell"],
                    ),
                    tier_chip(
                        "High Override",
                        styles,
                        width=24 * mm,
                    ),
                    Paragraph(
                        score_text(row[2]),
                        styles["table_cell"],
                    ),
                    Paragraph(
                        score_text(row[3]),
                        styles["table_cell"],
                    ),
                    Paragraph(
                        f"<b>{score_text(row[4])}</b>",
                        styles["table_cell"],
                    ),
                ]
            )

        override_table = Table(
            override_data,
            colWidths=[
                22 * mm,
                36 * mm,
                29 * mm,
                25 * mm,
                30 * mm,
                26 * mm,
            ],
            repeatRows=1,
        )

        override_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), DARK_CYAN),
                    ("BOX", (0, 0), (-1, -1), 0.5, SLATE_200),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        SLATE_200,
                    ),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        story.extend([Spacer(1, 2 * mm), override_table])
    else:
        story.append(
            Paragraph(
                (
                    "No question reached a 3.00 opinion gap in this "
                    "assessment."
                ),
                styles["body"],
            )
        )

    return story


def ai_section(
    analysis: AIAnalysis | None,
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """AI analysis header and overall summary."""

    story: list[Any] = []

    story.extend(
        [
            Spacer(1, 8 * mm),
            ai_section_header(analysis, styles),
            Spacer(1, 6 * mm),
            section_heading("Executive summary", styles),
        ]
    )

    if (
        analysis is not None
        and analysis.status == "completed"
        and analysis.overall_summary
    ):
        story.append(
            Paragraph(
                html_text(analysis.overall_summary),
                styles["body"],
            )
        )
    else:
        story.append(
            Paragraph(
                (
                    "No AI analysis was included in this report. Choose "
                    "“With AI analysis” when downloading to "
                    "include the executive summary. The calculated "
                    "results above do not depend on it."
                ),
                styles["body"],
            )
        )

    return story


def statutory_references_section(
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Relevant statutory references from the Health and Safety at Work Act."""

    story: list[Any] = []

    story.extend(
        [
            PageBreak(),
            section_heading(
                (
                    "Relevant statutory references "
                    "(Health and Safety at Work Act "
                    "2015)"
                ),
                styles,
            ),
        ]
    )

    hswa_table_data: list[list[Any]] = [
        [
            Paragraph(
                "<b>Section</b>",
                styles["table_header"],
            ),
            Paragraph(
                "<b>Title</b>",
                styles["table_header"],
            ),
            Paragraph(
                "<b>Summary</b>",
                styles["table_header"],
            ),
        ]
    ]

    for reference in HSWA_REFERENCES:
        hswa_table_data.append(
            [
                Paragraph(
                    html_text(reference["section"]),
                    styles["table_cell"],
                ),
                Paragraph(
                    html_text(reference["title"]),
                    styles["table_cell"],
                ),
                Paragraph(
                    html_text(reference["summary"]),
                    styles["table_cell"],
                ),
            ]
        )

    hswa_table = Table(
        hswa_table_data,
        colWidths=[26 * mm, 46 * mm, 96 * mm],
    )

    hswa_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    DARK_CYAN,
                ),
                ("BOX", (0, 0), (-1, -1), 0.5, SLATE_200),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    SLATE_200,
                ),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.extend([hswa_table, Spacer(1, 6 * mm)])

    story.append(
        Paragraph(
            html_text(HSWA_DISCLAIMER),
            styles["callout"],
        )
    )

    return story


def generate_board_report(
    assessment: Assessment,
    organisation: Organisation,
    analysis: AIAnalysis | None,
    database: Session,
) -> bytes:
    """FR23: governance/liability framing, material risk exposure
    by domain, plain-language executive summary, and hardcoded
    HSWA 2015 references with a not-legal-advice disclaimer."""

    styles = build_styles()
    buffer = BytesIO()

    document = ReportDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=29 * mm,
        bottomMargin=23 * mm,
        title=(
            f"SafePlus Board Report "
            f"{assessment.organisation_assessment_number}"
        ),
        author="SafePlus",
        subject="SafePlus board-level governance summary",
    )

    document.report_name = "SafePlus Board Report"

    domain_rows = fetch_domain_rows(
        assessment,
        database,
    )

    question_rows = list(
        database.execute(
            select(
                Question.question_number,
                Domain.name,
                QuestionScore.employee_mean,
                QuestionScore.manager_mean,
                QuestionScore.opinion_gap,
            )
            .join(
                AssessmentQuestion,
                AssessmentQuestion.question_id
                == Question.id,
            )
            .join(
                QuestionScore,
                QuestionScore.assessment_question_id
                == AssessmentQuestion.id,
            )
            .join(
                Domain,
                Question.domain_id == Domain.id,
            )
            .where(
                AssessmentQuestion.assessment_id
                == assessment.id,
                AssessmentQuestion.is_active.is_(True),
            )
            .order_by(
                Domain.display_order,
                Question.id,
            )
        ).all()
    )

    online_entries, paper_entries = entry_counts(
        assessment,
        database,
    )

    story: list[Any] = []
    story.extend(
        cover_section(
            assessment,
            organisation,
            online_entries,
            paper_entries,
            styles,
        )
    )

    story.extend(domain_table_section(domain_rows, styles))

    # Questions where the two groups differ by 3.00 or more are a
    # board-level signal in their own right: workers and managers do
    # not agree on what is happening.
    story.extend(disagreement_section(question_rows, styles))

    story.extend(ai_section(analysis, styles))

    story.extend(statutory_references_section(styles))

    # Two passes: the first records which page each heading landed on,
    # the second fills in the contents page.
    document.multiBuild(
        story,
        onFirstPage=draw_page_header_footer,
        onLaterPages=draw_page_header_footer,
    )

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
