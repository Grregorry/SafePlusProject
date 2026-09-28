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
from app.services.reassessment_guidance import build_reassessment_guidance
from app.services.report_components import (
    combined_display,
    entry_counts,
    is_hidden,
    LOWEST,
    meta_line,
    source_chips,
    tier_chip,
    tier_label,
    tier_rules_table,
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
    source_titles,
)
from app.services.reports.data import fetch_domain_rows
from app.services.reports.helpers import (
    as_dict,
    as_list,
    html_text,
    score_text,
)
from app.services.reports.styles import (
    build_styles,
    DARK_CYAN,
    SLATE_100,
    SLATE_200,
    SLATE_300,
    SLATE_50,
    VIOLET_100,
)


def cover_section(
    assessment: Assessment,
    organisation: Organisation,
    online_entries: int,
    paper_entries: int,
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Cover page, contents page and the domain heading."""

    story: list[Any] = [
        Spacer(1, 9 * mm),
        Paragraph(
            "SafePlus Operational Manager Report",
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
        Spacer(1, 6 * mm),
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
                combined_index=4,
                gap_index=5,
                lowest_mean=lowest_mean,
                styles=styles,
            )
        )

    return story


def question_results_section(
    lowest_mean: Decimal | None,
    question_rows: list[Any],
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Question results table."""

    story: list[Any] = []

    story.extend(
        [
            PageBreak(),
            section_heading("Question results", styles),
            Paragraph(
                (
                    "Each question's Employee and Senior Manager scores, "
                    "side by side. “Hidden” means the two groups "
                    "differ by 3.00 or more, so an average would mask "
                    "their opposing views."
                ),
                styles["body"],
            ),
            Spacer(1, 3 * mm),
        ]
    )

    question_table_data: list[list[Any]] = [
        [
            Paragraph("Question", styles["table_header"]),
            Paragraph("Domain", styles["table_header"]),
            Paragraph("Tier", styles["table_header"]),
            Paragraph("Employee", styles["table_header"]),
            Paragraph(
                "Senior Manager",
                styles["table_header"],
            ),
            Paragraph("Combined", styles["table_header"]),
            Paragraph("Maturity", styles["table_header"]),
            Paragraph(
                "Opinion gap",
                styles["table_header"],
            ),
        ]
    ]

    for row in question_rows:
        (
            number,
            domain_name,
            employee_mean,
            manager_mean,
            combined_mean,
            opinion_gap,
            question_maturity,
            intervention_tier,
        ) = row

        number_text = f"<b>{html_text(number)}</b>"

        if (
            lowest_mean is not None
            and combined_mean is not None
            and not is_hidden(opinion_gap)
            and Decimal(str(combined_mean)) == lowest_mean
        ):
            number_text += (
                f'<br/><font color="{LOWEST.hexval()}" size="6">'
                "<b>lowest</b></font>"
            )

        question_table_data.append(
            [
                Paragraph(
                    number_text,
                    styles["table_cell"],
                ),
                Paragraph(
                    html_text(domain_name),
                    styles["table_cell"],
                ),
                tier_chip(
                    tier_label(
                        intervention_tier,
                        opinion_gap,
                    ),
                    styles,
                    width=21 * mm,
                ),
                Paragraph(
                    score_text(employee_mean),
                    styles["table_cell"],
                ),
                Paragraph(
                    score_text(manager_mean),
                    styles["table_cell"],
                ),
                Paragraph(
                    combined_display(
                        combined_mean,
                        opinion_gap,
                    ),
                    styles["table_cell"],
                ),
                Paragraph(
                    html_text(
                        "Hidden"
                        if is_hidden(opinion_gap)
                        else question_maturity
                    ),
                    styles["table_cell"],
                ),
                Paragraph(
                    f"<b>{score_text(opinion_gap)}</b>",
                    styles["table_cell"],
                ),
            ]
        )

    question_table = Table(
        question_table_data,
        colWidths=[
            16 * mm,
            27 * mm,
            24 * mm,
            19 * mm,
            24 * mm,
            21 * mm,
            22 * mm,
            19 * mm,
        ],
        repeatRows=1,
    )

    question_style: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), DARK_CYAN),
        ("BOX", (0, 0), (-1, -1), 0.5, SLATE_300),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, SLATE_200),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    for row_index in range(1, len(question_table_data)):
        if row_index % 2 == 0:
            question_style.append(
                (
                    "BACKGROUND",
                    (0, row_index),
                    (-1, row_index),
                    SLATE_50,
                )
            )

    question_table.setStyle(TableStyle(question_style))

    story.extend([question_table, Spacer(1, 7 * mm)])

    return story


def opinion_gap_section(
    analysis: AIAnalysis | None,
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Opinion gap and tiers."""

    story: list[Any] = []

    story.extend(
        [
            section_heading("Opinion gap and tiers", styles),
            Paragraph(
                (
                    "The opinion gap is the absolute difference between "
                    "the Employee mean and the Senior Manager mean for a "
                    "question — how differently the two groups "
                    "perceive the same practice. A higher gap is not "
                    "automatically a problem, but it is a signal worth "
                    "investigating. A gap of 3.00 or more is always "
                    "treated as High Override, whatever the score, and "
                    "the combined mean is hidden."
                ),
                styles["body"],
            ),
            Spacer(1, 2 * mm),
            tier_rules_table(styles),
            Spacer(1, 8 * mm),
            ai_section_header(analysis, styles),
            Spacer(1, 6 * mm),
            section_heading("Prioritised action list", styles),
            Paragraph(
                (
                    "Questions are selected and ranked by the scoring "
                    "rules — tier first, then the lowest combined "
                    "mean, then the largest opinion gap. The AI writes "
                    "only the wording for each one."
                ),
                styles["body"],
            ),
            Spacer(1, 2 * mm),
        ]
    )

    return story


def priority_actions_section(
    analysis: AIAnalysis | None,
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Priority actions with guidance sources."""

    story: list[Any] = []

    priority_actions = (
        as_list(analysis.priority_actions)
        if analysis is not None
        else []
    )

    guidance_sources = (
        as_list(
            as_dict(analysis.domain_summaries).get(
                "guidance_sources"
            )
        )
        if analysis is not None
        else []
    )

    if priority_actions:
        for action in priority_actions:
            action_data = as_dict(action)

            if not action_data:
                continue

            priority = action_data.get("priority")
            title = action_data.get("title", "")
            urgency = str(action_data.get("urgency", ""))
            reason = action_data.get("reason", "")
            recommended_action = action_data.get(
                "recommended_action",
                "",
            )
            evidence = as_list(
                action_data.get("assessment_evidence")
            )

            action_flowables: list[Any] = [
                Table(
                    [
                        [
                            Paragraph(
                                (
                                    f"<b>Priority {html_text(priority)}: "
                                    f"{html_text(title)}</b>"
                                ),
                                styles["subsection"],
                            ),
                            tier_chip(
                                urgency,
                                styles,
                                width=28 * mm,
                            ),
                        ]
                    ],
                    colWidths=[133 * mm, 35 * mm],
                    style=TableStyle(
                        [
                            (
                                "BACKGROUND",
                                (0, 0),
                                (0, 0),
                                VIOLET_100,
                            ),
                            ("BOX", (0, 0), (-1, -1), 0.5, SLATE_200),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ]
                    ),
                ),
            ]

            if evidence:
                action_flowables.append(
                    Paragraph(
                        "<b>Assessment evidence</b>",
                        styles["body"],
                    )
                )
                action_flowables.extend(
                    bullet_items(evidence, styles)
                )

            action_flowables.extend(
                [
                    Paragraph(
                        "<b>Why this matters</b>",
                        styles["body"],
                    ),
                    Paragraph(
                        html_text(reason),
                        styles["body"],
                    ),
                    Table(
                        [
                            [
                                Paragraph(
                                    (
                                        "<b>Recommended action</b><br/>"
                                        f"{html_text(recommended_action)}"
                                    ),
                                    styles["body"],
                                )
                            ]
                        ],
                        colWidths=[168 * mm],
                        style=TableStyle(
                            [
                                (
                                    "BACKGROUND",
                                    (0, 0),
                                    (-1, -1),
                                    SLATE_100,
                                ),
                                ("BOX", (0, 0), (-1, -1), 0.5, SLATE_200),
                                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                                ("TOPPADDING", (0, 0), (-1, -1), 7),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                            ]
                        ),
                    ),
                ]
            )

            action_sources = source_chips(
                source_titles(
                    action_data.get("source_ids"),
                    guidance_sources,
                ),
                styles,
            )

            if action_sources is not None:
                action_flowables.extend(
                    [
                        Spacer(1, 1.5 * mm),
                        action_sources,
                    ]
                )

            story.extend(
                [
                    KeepTogether(action_flowables),
                    Spacer(1, 6 * mm),
                ]
            )
    else:
        story.append(
            Paragraph(
                (
                    "No AI analysis was included in this report. Choose "
                    "“With AI analysis” when downloading to "
                    "include the prioritised action list. The question "
                    "results above do not depend on it."
                ),
                styles["body"],
            )
        )

    return story


def reassessment_section(
    assessment: Assessment,
    domain_rows: list[Any],
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Re-assessment readiness and recommended timeframe."""

    story: list[Any] = []

    story.extend(
        [
            Spacer(1, 4 * mm),
            section_heading("Re-assessment readiness", styles),
        ]
    )

    guidance = build_reassessment_guidance(
        assessment.overall_maturity_label,
        [
            (name, mean, level)
            for name, mean, level in domain_rows
        ],
    )

    story.extend(
        [
            Paragraph(
                (
                    "<b>Recommended re-assessment timeframe:</b> "
                    f"{html_text(guidance['recommended_timeframe'])}"
                ),
                styles["body"],
            ),
            Paragraph(
                (
                    "<b>Largest improvement opportunity:</b> "
                    f"{html_text(guidance['largest_opportunity_domain'] or 'Not available')}"
                ),
                styles["body"],
            ),
            Paragraph(
                html_text(guidance["improvement_description"]),
                styles["body"],
            ),
        ]
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
                    "supports day-to-day action planning "
                    "for operational managers and health "
                    "and safety teams. It should be "
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


def generate_operational_manager_report(
    assessment: Assessment,
    organisation: Organisation,
    analysis: AIAnalysis | None,
    database: Session,
) -> bytes:
    """FR24: per-question scores/labels, opinion gap explained per
    question, prioritised action list, and FR25 re-assessment
    readiness guidance."""

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
            f"SafePlus Operational Manager Report "
            f"{assessment.organisation_assessment_number}"
        ),
        author="SafePlus",
        subject="SafePlus operational manager action report",
    )

    document.report_name = "SafePlus Operational Manager Report"

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
                QuestionScore.combined_mean,
                QuestionScore.opinion_gap,
                QuestionScore.maturity_level,
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
        if row[4] is not None and not is_hidden(row[5])
    ]

    lowest_mean = (
        min(Decimal(str(row[4])) for row in visible_questions)
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

    story.extend(question_results_section(lowest_mean, question_rows, styles))

    story.extend(opinion_gap_section(analysis, styles))

    story.extend(priority_actions_section(analysis, styles))

    story.extend(reassessment_section(assessment, domain_rows, styles))

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
