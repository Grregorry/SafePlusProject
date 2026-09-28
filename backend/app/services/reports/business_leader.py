from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

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
    entry_counts,
    is_hidden,
    meta_line,
    profile_legend,
    question_profile,
    tier_chip,
)
from app.services.reports.blocks import (
    ai_section_header,
    bullet_items,
    contents_block,
    domain_cards,
    draw_page_header_footer,
    overall_result_card,
    ReportDocTemplate,
    section_heading,
)
from app.services.reports.data import fetch_domain_rows, profile_from_rows
from app.services.reports.helpers import (
    as_dict,
    as_list,
    html_text,
    score_text,
)
from app.services.reports.styles import build_styles, SLATE_100, SLATE_200


def cover_section(
    assessment: Assessment,
    organisation: Organisation,
    online_entries: int,
    paper_entries: int,
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Cover page, contents page and the heading for the domain section."""

    story: list[Any] = [
        Spacer(1, 9 * mm),
        Paragraph(
            "SafePlus Business Leader Report",
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
        Spacer(1, 6 * mm),
        overall_result_card(assessment, styles),
        Spacer(1, 8 * mm),
    ]

    story.extend(contents_block(styles, own_page=False))
    story.append(section_heading("Maturity by domain", styles))

    return story


def domain_section(
    domain_rows: list[Any],
    lowest_mean: Decimal | None,
    question_rows: list[Any],
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Maturity by domain."""

    story: list[Any] = []

    if domain_rows:
        story.extend(
            domain_cards(
                domain_rows,
                question_rows,
                domain_index=1,
                number_index=0,
                combined_index=2,
                gap_index=3,
                lowest_mean=lowest_mean,
                styles=styles,
            )
        )

        profile_points, domain_ranges = profile_from_rows(
            question_rows,
            number_index=0,
            domain_index=1,
            combined_index=2,
            gap_index=3,
            lowest_mean=lowest_mean,
        )

        if profile_points:
            story.append(
                KeepTogether(
                    [
                        Spacer(1, 2 * mm),
                        Paragraph(
                            "SafePlus question profile",
                            styles["subsection"],
                        ),
                        question_profile(
                            profile_points,
                            width=380,
                            height=380,
                        ),
                        *profile_legend(
                            domain_ranges,
                            styles,
                        ),
                    ]
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


def strengths_priorities_section(
    question_rows: list[Any],
    styles: dict[str, ParagraphStyle],
    visible_questions: list[Any],
) -> list[Any]:
    """Top strengths and priority areas, with any hidden questions noted."""

    story: list[Any] = []

    top_strengths = sorted(
        visible_questions,
        key=lambda row: Decimal(str(row[2])),
        reverse=True,
    )[:3]

    top_priorities = sorted(
        visible_questions,
        key=lambda row: Decimal(str(row[2])),
    )[:3]

    hidden_questions = [
        row for row in question_rows if is_hidden(row[3])
    ]

    story.extend(
        [
            PageBreak(),
            section_heading(
                "Top strengths and priority areas",
                styles,
            ),
            Paragraph(
                (
                    "Ranked by combined mean. Questions where the two "
                    "groups differ by 3.00 or more are listed separately, "
                    "because an average would mask their opposing views."
                ),
                styles["body"],
            ),
            Spacer(1, 2 * mm),
        ]
    )

    def _question_lines(rows: list[Any]) -> list[Any]:
        return bullet_items(
            [
                (
                    f"{row[1]}, Question {row[0]} "
                    f"(combined mean {score_text(row[2])})"
                )
                for row in rows
            ],
            styles,
        ) or [
            Paragraph(
                "Not available.",
                styles["body"],
            )
        ]

    strengths_priorities = Table(
        [
            [
                Paragraph(
                    "<b>Top strengths</b>",
                    styles["subsection"],
                ),
                Paragraph(
                    "<b>Top priority areas</b>",
                    styles["subsection"],
                ),
            ],
            [
                _question_lines(top_strengths),
                _question_lines(top_priorities),
            ],
        ],
        colWidths=[84 * mm, 84 * mm],
    )

    strengths_priorities.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), SLATE_100),
                ("BOX", (0, 0), (-1, -1), 0.5, SLATE_200),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    SLATE_200,
                ),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.append(strengths_priorities)

    if hidden_questions:
        hidden_list = ", ".join(
            (
                f"Question {row[0]} (the two groups differ by "
                f"{score_text(row[3])})"
            )
            for row in hidden_questions
        )

        story.extend(
            [
                Spacer(1, 4 * mm),
                Paragraph(
                    (
                        "<b>Hidden combined means (High Override):</b> "
                        f"{html_text(hidden_list)}. These need a "
                        "conversation with both groups before any average "
                        "is used."
                    ),
                    styles["body"],
                ),
            ]
        )

    return story


def priority_actions_section(
    analysis: AIAnalysis | None,
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """The top three AI priority actions."""

    story: list[Any] = []

    story.extend(
        [
            Spacer(1, 8 * mm),
            ai_section_header(analysis, styles),
            Spacer(1, 6 * mm),
            section_heading("Next 90 days", styles),
        ]
    )

    priority_actions = (
        as_list(analysis.priority_actions)
        if analysis is not None
        else []
    )

    top_actions: list[Any] = []

    for action in priority_actions[:3]:
        action_data = as_dict(action)
        recommended = action_data.get("recommended_action")
        title = action_data.get("title")

        if not recommended:
            continue

        top_actions.extend(
            [
                Table(
                    [
                        [
                            tier_chip(
                                str(
                                    action_data.get(
                                        "urgency",
                                        "Not flagged",
                                    )
                                ),
                                styles,
                                width=27 * mm,
                            ),
                            Paragraph(
                                (
                                    f"<b>{html_text(title)}</b><br/>"
                                    f"{html_text(recommended)}"
                                ),
                                styles["body"],
                            ),
                        ]
                    ],
                    colWidths=[33 * mm, 135 * mm],
                    style=TableStyle(
                        [
                            ("BOX", (0, 0), (-1, -1), 0.5, SLATE_200),
                            ("LEFTPADDING", (0, 0), (-1, -1), 7),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                            ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ]
                    ),
                ),
                Spacer(1, 3 * mm),
            ]
        )

    if top_actions:
        story.extend(top_actions)
    else:
        story.append(
            Paragraph(
                (
                    "No AI analysis was included in this report. Choose "
                    "“With AI analysis” when downloading to "
                    "include the priority actions."
                ),
                styles["body"],
            )
        )

    return story


def narrative_section(
    analysis: AIAnalysis | None,
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Narrative summary from the AI analysis."""

    story: list[Any] = []

    story.extend(
        [
            Spacer(1, 5 * mm),
            section_heading("Narrative summary", styles),
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
                    "No saved AI analysis was "
                    "available when this report was "
                    "generated."
                ),
                styles["body"],
            )
        )

    return story


def notice_section(styles: dict[str, ParagraphStyle]) -> list[Any]:
    """Closing notice about how the report should be read."""

    story: list[Any] = []

    story.extend(
        [
            Spacer(1, 8 * mm),
            Paragraph(
                (
                    "<b>Report notice:</b> This report "
                    "supports organisational reflection "
                    "and improvement planning for "
                    "business leaders. It should be "
                    "interpreted alongside worker "
                    "engagement, operational context, "
                    "and professional health and safety "
                    "judgement."
                ),
                styles["small"],
            ),
        ]
    )

    return story


def generate_business_leader_report(
    assessment: Assessment,
    organisation: Organisation,
    analysis: AIAnalysis | None,
    database: Session,
) -> bytes:
    """FR22: overall maturity, top strengths/priorities, 90-day
    action summary, and a high-level organisational narrative."""

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
            f"SafePlus Business Leader Report "
            f"{assessment.organisation_assessment_number}"
        ),
        author="SafePlus",
        subject="SafePlus business leader summary",
    )

    document.report_name = "SafePlus Business Leader Report"

    domain_rows = fetch_domain_rows(
        assessment,
        database,
    )

    question_rows = list(
        database.execute(
            select(
                Question.question_number,
                Domain.name,
                QuestionScore.combined_mean,
                QuestionScore.opinion_gap,
                QuestionScore.intervention_tier,
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

    visible_questions = [
        row
        for row in question_rows
        if row[2] is not None and not is_hidden(row[3])
    ]

    lowest_mean = (
        min(Decimal(str(row[2])) for row in visible_questions)
        if visible_questions
        else None
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

    story.extend(
        domain_section(
            domain_rows,
            lowest_mean,
            question_rows,
            styles,
        )
    )

    story.extend(
        strengths_priorities_section(
            question_rows,
            styles,
            visible_questions,
        )
    )

    story.extend(priority_actions_section(analysis, styles))

    story.extend(narrative_section(analysis, styles))

    story.extend(notice_section(styles))

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
