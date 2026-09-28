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
    DomainScore,
    Organisation,
    Question,
    QuestionScore,
)
from app.services.report_components import (
    combined_display,
    entry_counts,
    format_long_date,
    how_scores_are_calculated,
    is_hidden,
    LOWEST,
    profile_legend,
    ProfilePoint,
    question_profile,
    tier_chip,
    tier_label,
)
from app.services.reports.ai_actions import (
    priority_actions_section,
    roadmap_section,
)
from app.services.reports.ai_sources import (
    ai_disclaimer_section,
    sources_limitations_section,
)
from app.services.reports.ai_summary import (
    domain_summaries_section,
    overall_summary_section,
    strengths_risks_section,
)
from app.services.reports.blocks import (
    ai_section_header,
    contents_block,
    domain_cards,
    draw_page_header_footer,
    overall_result_card,
    ReportDocTemplate,
    section_heading,
    summary_card,
    tag_contents_entry,
)
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
)


def cover_section(
    assessment: Assessment,
    organisation: Organisation,
    online_entries: int,
    paper_entries: int,
    question_rows: list[Any],
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Cover page, organisation details and contents page."""

    story: list[Any] = []

    story.extend(
        [
            Spacer(1, 9 * mm),
            Paragraph(
                "SafePlus Assessment Report",
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
            Spacer(1, 6 * mm),
        ]
    )

    organisation_table = Table(
        [
            [
                Paragraph(
                    "<b>Organisation</b>",
                    styles["small"],
                ),
                Paragraph(
                    html_text(organisation.name),
                    styles["body"],
                ),
            ],
            [
                Paragraph(
                    "<b>Category</b>",
                    styles["small"],
                ),
                Paragraph(
                    html_text(organisation.category),
                    styles["body"],
                ),
            ],
            [
                Paragraph(
                    "<b>Account email</b>",
                    styles["small"],
                ),
                Paragraph(
                    html_text(organisation.email),
                    styles["body"],
                ),
            ],
            [
                Paragraph(
                    "<b>Assessment status</b>",
                    styles["small"],
                ),
                Paragraph(
                    html_text(
                        assessment.status
                        .replace("_", " ")
                        .title()
                    ),
                    styles["body"],
                ),
            ],
            [
                Paragraph(
                    "<b>Opened</b>",
                    styles["small"],
                ),
                Paragraph(
                    format_long_date(assessment.created_at),
                    styles["body"],
                ),
            ],
            [
                Paragraph(
                    "<b>Closed</b>",
                    styles["small"],
                ),
                Paragraph(
                    format_long_date(assessment.completed_at),
                    styles["body"],
                ),
            ],
            [
                Paragraph(
                    "<b>Entries</b>",
                    styles["small"],
                ),
                Paragraph(
                    (
                        f"{online_entries + paper_entries} "
                        f"({online_entries} online, "
                        f"{paper_entries} paper)"
                    ),
                    styles["body"],
                ),
            ],
        ],
        colWidths=[40 * mm, 132 * mm],
    )

    organisation_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), SLATE_100),
                ("BOX", (0, 0), (-1, -1), 0.5, SLATE_200),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, SLATE_200),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.extend(
        [
            organisation_table,
            Spacer(1, 7 * mm),
            Paragraph(
                (
                    "This report summarises the calculated SafePlus "
                    "results for the organisation. A question's combined "
                    "mean is hidden where the Employee and Senior Manager "
                    "means differ by 3.00 or more, because an average "
                    "would mask their opposing views."
                ),
                styles["body"],
            ),
            Spacer(1, 4 * mm),
            overall_result_card(assessment, styles),
            Spacer(1, 5 * mm),
        ]
    )

    summary_cards = Table(
        [
            [
                summary_card(
                    "Questions scored",
                    str(len(question_rows)),
                    styles,
                ),
                summary_card(
                    "Entries",
                    str(online_entries + paper_entries),
                    styles,
                ),
                summary_card(
                    "Online / paper",
                    f"{online_entries} / {paper_entries}",
                    styles,
                ),
            ]
        ],
        colWidths=[56 * mm, 56 * mm, 56 * mm],
    )

    summary_cards.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    story.extend(
        [
            summary_cards,
            Spacer(1, 8 * mm),
        ]
    )

    story.extend(
        contents_block(styles, own_page=True)
    )

    return story


def domain_results_section(
    _is_lowest: Any,
    domain_rows: list[Any],
    lowest_mean: Decimal | None,
    question_rows: list[Any],
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Domain results with the summary cards."""

    story: list[Any] = []

    if domain_rows:
        domain_flowables = domain_cards(
            domain_rows,
            question_rows,
            domain_index=3,
            number_index=0,
            combined_index=6,
            gap_index=7,
            lowest_mean=lowest_mean,
            styles=styles,
        )

        # Keep the heading with the first card, so it never sits alone
        # at the foot of a page.
        story.append(
            tag_contents_entry(
                KeepTogether(
                    [
                        section_heading("Domain results", styles),
                        *domain_flowables[:2],
                    ]
                ),
                "Domain results",
            )
        )
        story.extend(domain_flowables[2:])

        profile_points: list[ProfilePoint] = []
        domain_ranges: list[list[str]] = []
        previous_domain: str | None = None

        for question_row in question_rows:
            domain_name = question_row[3]
            question_number = str(question_row[0])
            starts_domain = domain_name != previous_domain

            profile_points.append(
                ProfilePoint(
                    label=question_number,
                    value=question_row[6],
                    hidden=is_hidden(question_row[7]),
                    lowest=_is_lowest(question_row),
                    domain_start=starts_domain,
                )
            )

            if starts_domain:
                domain_ranges.append(
                    [
                        domain_name,
                        question_number,
                        question_number,
                    ]
                )
            else:
                domain_ranges[-1][2] = question_number

            previous_domain = domain_name

        if profile_points:
            story.extend(
                [
                    Spacer(1, 2 * mm),
                    KeepTogether(
                        [
                            Paragraph(
                                "SafePlus question profile",
                                styles["subsection"],
                            ),
                            Paragraph(
                                (
                                    "Each spoke is one scored question, "
                                    "grouped by domain, so differences "
                                    "between questions are shown at their "
                                    "true size."
                                ),
                                styles["body"],
                            ),
                            question_profile(profile_points),
                            *profile_legend(
                                [
                                    (
                                        item[0],
                                        item[1],
                                        item[2],
                                    )
                                    for item in domain_ranges
                                ],
                                styles,
                            ),
                        ]
                    ),
                ]
            )
    else:
        story.extend(
            [
                section_heading("Domain results", styles),
                Paragraph(
                    "No domain scores were available.",
                    styles["body"],
                ),
            ]
        )

    return story


def question_results_section(
    assessment: Assessment,
    _is_lowest: Any,
    domain_rows: list[Any],
    question_rows: list[Any],
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Question results, with the lowest scoring question marked."""

    story: list[Any] = []

    story.extend(
        [
            PageBreak(),
            section_heading("Question results", styles),
            Paragraph(
                (
                    "Each question's Employee and Senior Manager scores, "
                    "side by side. \u201cHidden\u201d means the two groups "
                    "differ by 3.00 or more, so an average would mask "
                    "their opposing views."
                ),
                styles["body"],
            ),
            Spacer(1, 3 * mm),
        ]
    )

    if question_rows:
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
                Paragraph(
                    "Opinion gap",
                    styles["table_header"],
                ),
            ]
        ]

        for question_row in question_rows:
            (
                question_number,
                _employee_text,
                _manager_text,
                domain_name,
                employee_mean,
                manager_mean,
                combined_mean,
                opinion_gap,
                intervention_tier,
            ) = question_row

            number_text = f"<b>{html_text(question_number)}</b>"

            if _is_lowest(question_row):
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
                        width=23 * mm,
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
                        score_text(opinion_gap),
                        styles["table_cell_bold"],
                    ),
                ]
            )

        question_table = Table(
            question_table_data,
            colWidths=[
                18 * mm,
                29 * mm,
                26 * mm,
                21 * mm,
                26 * mm,
                24 * mm,
                24 * mm,
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

        question_table.setStyle(
            TableStyle(question_style)
        )

        domain_workings: list[
            tuple[str, Decimal, int, Decimal]
        ] = []

        for (
            domain_name,
            domain_mean,
            _domain_maturity,
        ) in domain_rows:
            rows_for_domain = [
                row
                for row in question_rows
                if row[3] == domain_name
            ]

            total = sum(
                (
                    Decimal(str(row[6]))
                    for row in rows_for_domain
                    if row[6] is not None
                ),
                Decimal("0"),
            )

            domain_workings.append(
                (
                    domain_name,
                    total,
                    len(rows_for_domain),
                    Decimal(str(domain_mean)),
                )
            )

        story.extend(
            [
                question_table,
                Spacer(1, 7 * mm),
                *how_scores_are_calculated(
                    domain_workings,
                    assessment.overall_combined_mean,
                    styles,
                ),
            ]
        )
    else:
        story.append(
            Paragraph(
                "No question scores were available.",
                styles["body"],
            )
        )

    return story


def ai_analysis_section(
    analysis: AIAnalysis | None,
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """AI analysis pages, or a notice when none exists."""

    story: list[Any] = []

    story.extend(
        [
            PageBreak(),
            ai_section_header(analysis, styles),
            Spacer(1, 6 * mm),
        ]
    )

    if analysis is None:
        story.append(
            Paragraph(
                (
                    "No AI analysis has been included in this report. "
                    "The calculated assessment results remain valid; "
                    "AI suggestions are only added once someone has "
                    "reviewed them and chosen to include them from "
                    "the results page."
                ),
                styles["body"],
            )
        )
    elif analysis.status != "completed":
        story.append(
            Paragraph(
                (
                    "The saved AI analysis is not complete. Current "
                    f"status: {html_text(analysis.status)}."
                ),
                styles["body"],
            )
        )
    else:
        story.extend(overall_summary_section(analysis, styles))

        domain_data = as_dict(
            analysis.domain_summaries
        )
        key_strengths = as_list(
            domain_data.get("key_strengths")
        )
        key_risks = as_list(
            domain_data.get("key_risks")
        )
        ai_domains = as_list(
            domain_data.get("domains")
        )
        limitations = as_list(
            domain_data.get("limitations")
        )
        guidance_sources = as_list(
            domain_data.get("guidance_sources")
        )

        story.extend(strengths_risks_section(styles, key_risks, key_strengths))

        story.extend(domain_summaries_section(styles, ai_domains))

        story.extend(
            priority_actions_section(
                analysis,
                styles,
                guidance_sources,
            )
        )

        story.extend(roadmap_section(analysis, styles, guidance_sources))

        story.extend(
            sources_limitations_section(
                styles,
                guidance_sources,
                limitations,
            )
        )

        story.extend(ai_disclaimer_section(analysis, styles))

    return story


def notice_section(styles: dict[str, ParagraphStyle]) -> list[Any]:
    """Closing notice about how the report should be read."""

    story: list[Any] = []

    story.extend(
        [
            Spacer(1, 8 * mm),
            Paragraph(
                (
                    "<b>Report notice:</b> This report supports "
                    "organisational reflection and improvement planning. "
                    "It should be interpreted alongside worker engagement, "
                    "operational context, and professional health and "
                    "safety judgement."
                ),
                styles["small"],
            ),
        ]
    )

    return story


def generate_assessment_report(
    assessment: Assessment,
    organisation: Organisation,
    analysis: AIAnalysis | None,
    database: Session,
) -> bytes:
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
            f"SafePlus Assessment "
            f"{assessment.organisation_assessment_number}"
        ),
        author="SafePlus",
        subject="SafePlus assessment results and recommendations",
    )

    document.report_name = "SafePlus Assessment Report"

    domain_rows = list(
        database.execute(
            select(
                Domain.name,
                DomainScore.combined_mean,
                DomainScore.maturity_level,
            )
            .join(
                DomainScore,
                DomainScore.domain_id == Domain.id,
            )
            .where(
                DomainScore.assessment_id
                == assessment.id
            )
            .order_by(Domain.display_order)
        ).all()
    )

    question_rows = list(
        database.execute(
            select(
                Question.question_number,
                Question.employee_text,
                Question.manager_text,
                Domain.name,
                QuestionScore.employee_mean,
                QuestionScore.manager_mean,
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

    # The lowest scoring question is marked, as on the results page.
    # Hidden questions are left out, and ties are all marked.
    visible_means = [
        Decimal(str(row[6]))
        for row in question_rows
        if row[6] is not None and not is_hidden(row[7])
    ]

    lowest_mean = min(visible_means) if visible_means else None

    def _is_lowest(question_row: Any) -> bool:
        return (
            lowest_mean is not None
            and question_row[6] is not None
            and not is_hidden(question_row[7])
            and Decimal(str(question_row[6])) == lowest_mean
        )

    story: list[Any] = []

    story.extend(
        cover_section(
            assessment,
            organisation,
            online_entries,
            paper_entries,
            question_rows,
            styles,
        )
    )

    story.extend(
        domain_results_section(
            _is_lowest,
            domain_rows,
            lowest_mean,
            question_rows,
            styles,
        )
    )

    story.extend(
        question_results_section(
            assessment,
            _is_lowest,
            domain_rows,
            question_rows,
            styles,
        )
    )

    story.extend(ai_analysis_section(analysis, styles))

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
