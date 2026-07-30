from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from html import escape
from io import BytesIO
from math import cos, pi, sin
from typing import Any

from reportlab.graphics.shapes import (
    Circle,
    Drawing,
    Line,
    Polygon,
    String,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
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


PAGE_WIDTH, PAGE_HEIGHT = A4

CYAN = colors.HexColor("#0E7490")
DARK_CYAN = colors.HexColor("#155E75")
SLATE_900 = colors.HexColor("#0F172A")
SLATE_700 = colors.HexColor("#334155")
SLATE_600 = colors.HexColor("#475569")
SLATE_500 = colors.HexColor("#64748B")
SLATE_300 = colors.HexColor("#CBD5E1")
SLATE_200 = colors.HexColor("#E2E8F0")
SLATE_100 = colors.HexColor("#F1F5F9")
WHITE = colors.white

RED_700 = colors.HexColor("#B91C1C")
RED_100 = colors.HexColor("#FEE2E2")
ORANGE_700 = colors.HexColor("#C2410C")
ORANGE_100 = colors.HexColor("#FFEDD5")
YELLOW_800 = colors.HexColor("#854D0E")
YELLOW_100 = colors.HexColor("#FEF9C3")
GREEN_700 = colors.HexColor("#047857")
GREEN_100 = colors.HexColor("#D1FAE5")
VIOLET_700 = colors.HexColor("#6D28D9")
VIOLET_100 = colors.HexColor("#EDE9FE")


def _score(value: Decimal | float | int | str | None) -> str:
    if value is None:
        return "Not available"

    try:
        return f"{Decimal(str(value)):.2f}"
    except Exception:
        return str(value)


def _date(value: datetime | None) -> str:
    if value is None:
        return "Not available"

    return value.astimezone().strftime(
        "%d %B %Y, %I:%M %p"
    )


def _safe_text(value: object) -> str:
    if value is None:
        return ""

    return escape(str(value))


def _normalise_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value

    return []


def _normalise_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value

    return {}


def _maturity_colours(
    maturity: str,
) -> tuple[colors.Color, colors.Color]:
    if maturity == "Leading":
        return GREEN_100, GREEN_700

    if maturity == "Performing":
        return YELLOW_100, YELLOW_800

    return RED_100, RED_700


def _tier_colours(
    tier: str,
    high_override: bool,
) -> tuple[colors.Color, colors.Color]:
    if high_override:
        return RED_700, WHITE

    if tier == "High":
        return RED_100, RED_700

    if tier == "Medium":
        return ORANGE_100, ORANGE_700

    if tier == "Low":
        return YELLOW_100, YELLOW_800

    return SLATE_100, SLATE_700


def _build_styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=sample["Title"],
            fontName="Helvetica-Bold",
            fontSize=25,
            leading=31,
            textColor=SLATE_900,
            spaceAfter=10,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=17,
            textColor=SLATE_600,
            spaceAfter=5,
        ),
        "section": ParagraphStyle(
            "SectionTitle",
            parent=sample["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=22,
            textColor=SLATE_900,
            spaceBefore=10,
            spaceAfter=10,
        ),
        "subsection": ParagraphStyle(
            "SubsectionTitle",
            parent=sample["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=18,
            textColor=SLATE_900,
            spaceBefore=10,
            spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "ReportBody",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14.5,
            textColor=SLATE_700,
            spaceAfter=8,
        ),
        "small": ParagraphStyle(
            "SmallBody",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=SLATE_600,
        ),
        "tiny": ParagraphStyle(
            "TinyBody",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=SLATE_600,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=sample["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=WHITE,
            alignment=TA_LEFT,
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=7.2,
            leading=9,
            textColor=SLATE_700,
        ),
        "table_cell_bold": ParagraphStyle(
            "TableCellBold",
            parent=sample["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.2,
            leading=9,
            textColor=SLATE_900,
        ),
        "centre": ParagraphStyle(
            "Centre",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            alignment=TA_CENTER,
            textColor=SLATE_700,
        ),
        "callout": ParagraphStyle(
            "Callout",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=14,
            textColor=RED_700,
        ),
    }


def _page_header_footer(
    canvas: Any,
    document: SimpleDocTemplate,
) -> None:
    canvas.saveState()

    canvas.setStrokeColor(SLATE_200)
    canvas.setLineWidth(0.5)
    canvas.line(
        document.leftMargin,
        PAGE_HEIGHT - 24 * mm,
        PAGE_WIDTH - document.rightMargin,
        PAGE_HEIGHT - 24 * mm,
    )

    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(DARK_CYAN)
    canvas.drawString(
        document.leftMargin,
        PAGE_HEIGHT - 19 * mm,
        "SafePlus Assessment Report",
    )

    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(SLATE_500)
    canvas.drawRightString(
        PAGE_WIDTH - document.rightMargin,
        PAGE_HEIGHT - 19 * mm,
        "Confidential assessment information",
    )

    canvas.setStrokeColor(SLATE_200)
    canvas.line(
        document.leftMargin,
        18 * mm,
        PAGE_WIDTH - document.rightMargin,
        18 * mm,
    )

    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(SLATE_500)
    canvas.drawString(
        document.leftMargin,
        12 * mm,
        "Generated by SafePlus",
    )

    canvas.drawRightString(
        PAGE_WIDTH - document.rightMargin,
        12 * mm,
        f"Page {document.page}",
    )

    canvas.restoreState()


def _summary_card(
    label: str,
    value: str,
    styles: dict[str, ParagraphStyle],
    background: colors.Color = SLATE_100,
    value_colour: colors.Color = SLATE_900,
) -> Table:
    table = Table(
        [
            [
                Paragraph(
                    _safe_text(label),
                    styles["small"],
                )
            ],
            [
                Paragraph(
                    f"<b>{_safe_text(value)}</b>",
                    ParagraphStyle(
                        "CardValue",
                        parent=styles["body"],
                        fontName="Helvetica-Bold",
                        fontSize=18,
                        leading=21,
                        textColor=value_colour,
                        spaceAfter=0,
                    ),
                )
            ],
        ],
        colWidths=[49 * mm],
        rowHeights=[8 * mm, 14 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("BOX", (0, 0), (-1, -1), 0.5, SLATE_200),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    return table


def _radar_chart(
    domain_rows: list[tuple[str, Decimal]],
) -> Drawing:
    width = 440
    height = 260
    centre_x = width / 2
    centre_y = 118
    radius = 88
    levels = 5

    drawing = Drawing(width, height)

    axis_count = max(len(domain_rows), 3)
    angles = [
        -pi / 2 + (2 * pi * index / axis_count)
        for index in range(axis_count)
    ]

    for level in range(1, levels + 1):
        level_radius = radius * level / levels
        points: list[float] = []

        for angle in angles:
            points.extend(
                [
                    centre_x + level_radius * cos(angle),
                    centre_y - level_radius * sin(angle),
                ]
            )

        drawing.add(
            Polygon(
                points,
                strokeColor=SLATE_300,
                fillColor=None,
                strokeWidth=0.6,
            )
        )

    for angle in angles:
        end_x = centre_x + radius * cos(angle)
        end_y = centre_y - radius * sin(angle)

        drawing.add(
            Line(
                centre_x,
                centre_y,
                end_x,
                end_y,
                strokeColor=SLATE_300,
                strokeWidth=0.7,
            )
        )

    score_points: list[float] = []

    for index, (domain_name, score_value) in enumerate(
        domain_rows
    ):
        angle = angles[index]
        safe_score = max(
            0.0,
            min(5.0, float(score_value)),
        )
        score_radius = radius * safe_score / 5.0
        point_x = centre_x + score_radius * cos(angle)
        point_y = centre_y - score_radius * sin(angle)

        score_points.extend([point_x, point_y])

        label_radius = radius + 31
        label_x = centre_x + label_radius * cos(angle)
        label_y = centre_y - label_radius * sin(angle)

        anchor = "middle"

        if cos(angle) > 0.25:
            anchor = "start"
        elif cos(angle) < -0.25:
            anchor = "end"

        drawing.add(
            String(
                label_x,
                label_y,
                domain_name,
                fontName="Helvetica-Bold",
                fontSize=8,
                fillColor=SLATE_700,
                textAnchor=anchor,
            )
        )

        drawing.add(
            String(
                label_x,
                label_y - 11,
                _score(score_value),
                fontName="Helvetica",
                fontSize=7.5,
                fillColor=CYAN,
                textAnchor=anchor,
            )
        )

    if len(score_points) >= 6:
        drawing.add(
            Polygon(
                score_points,
                strokeColor=DARK_CYAN,
                fillColor=colors.Color(
                    CYAN.red,
                    CYAN.green,
                    CYAN.blue,
                    alpha=0.22,
                ),
                strokeWidth=1.8,
            )
        )

        for index in range(0, len(score_points), 2):
            drawing.add(
                Circle(
                    score_points[index],
                    score_points[index + 1],
                    2.5,
                    fillColor=DARK_CYAN,
                    strokeColor=DARK_CYAN,
                )
            )

    drawing.add(
        String(
            12,
            12,
            "Scale: 1 = lower maturity, 5 = higher maturity",
            fontName="Helvetica",
            fontSize=7,
            fillColor=SLATE_500,
        )
    )

    return drawing


def _bullet_items(
    values: list[object],
    styles: dict[str, ParagraphStyle],
) -> list[Paragraph]:
    return [
        Paragraph(
            f"&#8226; {_safe_text(value)}",
            styles["body"],
        )
        for value in values
        if value not in (None, "")
    ]


def _heading(
    text: str,
    styles: dict[str, ParagraphStyle],
) -> Paragraph:
    return Paragraph(
        _safe_text(text),
        styles["section"],
    )


def generate_assessment_report(
    assessment: Assessment,
    organisation: Organisation,
    analysis: AIAnalysis | None,
    database: Session,
) -> bytes:
    styles = _build_styles()
    buffer = BytesIO()

    document = SimpleDocTemplate(
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
                    f"{_safe_text(assessment.name)}"
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
                    _safe_text(organisation.name),
                    styles["body"],
                ),
            ],
            [
                Paragraph(
                    "<b>Category</b>",
                    styles["small"],
                ),
                Paragraph(
                    _safe_text(organisation.category),
                    styles["body"],
                ),
            ],
            [
                Paragraph(
                    "<b>Account email</b>",
                    styles["small"],
                ),
                Paragraph(
                    _safe_text(organisation.email),
                    styles["body"],
                ),
            ],
            [
                Paragraph(
                    "<b>Assessment status</b>",
                    styles["small"],
                ),
                Paragraph(
                    _safe_text(
                        assessment.status
                        .replace("_", " ")
                        .title()
                    ),
                    styles["body"],
                ),
            ],
            [
                Paragraph(
                    "<b>Created</b>",
                    styles["small"],
                ),
                Paragraph(
                    _date(assessment.created_at),
                    styles["body"],
                ),
            ],
            [
                Paragraph(
                    "<b>Completed</b>",
                    styles["small"],
                ),
                Paragraph(
                    _date(assessment.completed_at),
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
                    "results for the organisation. Question-level "
                    "combined means are hidden where the Employee and "
                    "Senior Manager opinion gap is 3.00 points or greater, "
                    "because the average could mask strongly opposing "
                    "perceptions."
                ),
                styles["body"],
            ),
            Spacer(1, 4 * mm),
        ]
    )

    overall_background, overall_colour = _maturity_colours(
        assessment.overall_maturity_label
        or "Developing"
    )

    summary_cards = Table(
        [
            [
                _summary_card(
                    "Questions scored",
                    str(len(question_rows)),
                    styles,
                ),
                _summary_card(
                    "Overall combined mean",
                    _score(
                        assessment.overall_combined_mean
                    ),
                    styles,
                    background=colors.HexColor("#ECFEFF"),
                    value_colour=DARK_CYAN,
                ),
                _summary_card(
                    "Overall maturity",
                    assessment.overall_maturity_label
                    or "Not available",
                    styles,
                    background=overall_background,
                    value_colour=overall_colour,
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
            _heading("Domain results", styles),
        ]
    )

    if domain_rows:
        domain_table_data: list[list[Any]] = [
            [
                Paragraph("Domain", styles["table_header"]),
                Paragraph(
                    "Combined mean",
                    styles["table_header"],
                ),
                Paragraph(
                    "Maturity",
                    styles["table_header"],
                ),
            ]
        ]

        for (
            domain_name,
            combined_mean,
            maturity_level,
        ) in domain_rows:
            maturity_background, maturity_colour = (
                _maturity_colours(maturity_level)
            )

            domain_table_data.append(
                [
                    Paragraph(
                        f"<b>{_safe_text(domain_name)}</b>",
                        styles["table_cell"],
                    ),
                    Paragraph(
                        _score(combined_mean),
                        styles["table_cell_bold"],
                    ),
                    Paragraph(
                        (
                            f'<font color="{maturity_colour.hexval()}">'
                            f"<b>{_safe_text(maturity_level)}</b>"
                            f"</font>"
                        ),
                        styles["table_cell"],
                    ),
                ]
            )

        domain_table = Table(
            domain_table_data,
            colWidths=[
                86 * mm,
                42 * mm,
                44 * mm,
            ],
            repeatRows=1,
        )

        domain_table_style = [
            ("BACKGROUND", (0, 0), (-1, 0), DARK_CYAN),
            ("BOX", (0, 0), (-1, -1), 0.5, SLATE_300),
            ("INNERGRID", (0, 0), (-1, -1), 0.35, SLATE_200),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]

        for row_index, row in enumerate(domain_rows, start=1):
            maturity_background, _ = _maturity_colours(
                row[2]
            )
            domain_table_style.append(
                (
                    "BACKGROUND",
                    (2, row_index),
                    (2, row_index),
                    maturity_background,
                )
            )

        domain_table.setStyle(
            TableStyle(domain_table_style)
        )

        radar_values = [
            (row[0], row[1])
            for row in domain_rows
        ]

        story.extend(
            [
                domain_table,
                Spacer(1, 6 * mm),
                KeepTogether(
                    [
                        Paragraph(
                            "SafePlus domain profile",
                            styles["subsection"],
                        ),
                        Paragraph(
                            (
                                "The radar chart compares the three "
                                "combined domain scores on the SafePlus "
                                "1 to 5 maturity scale."
                            ),
                            styles["body"],
                        ),
                        _radar_chart(radar_values),
                    ]
                ),
            ]
        )
    else:
        story.append(
            Paragraph(
                "No domain scores were available.",
                styles["body"],
            )
        )

    story.extend(
        [
            PageBreak(),
            _heading("Question results", styles),
            Paragraph(
                (
                    "Employee and Senior Manager perceptions are shown "
                    "side by side. Combined means remain visible for "
                    "ordinary results. For High Override results, where "
                    "the opinion gap is 3.00 or greater, the combined mean "
                    "is intentionally hidden."
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
                Paragraph("Employee", styles["table_header"]),
                Paragraph(
                    "Senior Manager",
                    styles["table_header"],
                ),
                Paragraph("Combined", styles["table_header"]),
                Paragraph("Gap", styles["table_header"]),
                Paragraph("Tier", styles["table_header"]),
            ]
        ]

        high_override_rows: set[int] = set()

        for row_index, row in enumerate(
            question_rows,
            start=1,
        ):
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
            ) = row

            high_override = (
                Decimal(str(opinion_gap))
                >= Decimal("3.00")
            )

            if high_override:
                high_override_rows.add(row_index)

            displayed_combined = (
                "Hidden"
                if high_override
                else _score(combined_mean)
            )

            displayed_tier = (
                "High Override"
                if high_override
                else intervention_tier
            )

            question_table_data.append(
                [
                    Paragraph(
                        f"<b>{_safe_text(question_number)}</b>",
                        styles["table_cell"],
                    ),
                    Paragraph(
                        _safe_text(domain_name),
                        styles["table_cell"],
                    ),
                    Paragraph(
                        _score(employee_mean),
                        styles["table_cell"],
                    ),
                    Paragraph(
                        _score(manager_mean),
                        styles["table_cell"],
                    ),
                    Paragraph(
                        displayed_combined,
                        styles["table_cell"],
                    ),
                    Paragraph(
                        _score(opinion_gap),
                        styles["table_cell_bold"],
                    ),
                    Paragraph(
                        f"<b>{_safe_text(displayed_tier)}</b>",
                        styles["table_cell"],
                    ),
                ]
            )

        question_table = Table(
            question_table_data,
            colWidths=[
                16 * mm,
                35 * mm,
                23 * mm,
                27 * mm,
                23 * mm,
                18 * mm,
                30 * mm,
            ],
            repeatRows=1,
        )

        question_style: list[tuple[Any, ...]] = [
            ("BACKGROUND", (0, 0), (-1, 0), DARK_CYAN),
            ("BOX", (0, 0), (-1, -1), 0.5, SLATE_300),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, SLATE_200),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]

        for row_index in range(1, len(question_table_data)):
            if row_index % 2 == 0:
                question_style.append(
                    (
                        "BACKGROUND",
                        (0, row_index),
                        (-1, row_index),
                        SLATE_100,
                    )
                )

            if row_index in high_override_rows:
                question_style.extend(
                    [
                        (
                            "BACKGROUND",
                            (4, row_index),
                            (4, row_index),
                            RED_100,
                        ),
                        (
                            "TEXTCOLOR",
                            (4, row_index),
                            (4, row_index),
                            RED_700,
                        ),
                        (
                            "BACKGROUND",
                            (5, row_index),
                            (6, row_index),
                            RED_100,
                        ),
                        (
                            "TEXTCOLOR",
                            (5, row_index),
                            (6, row_index),
                            RED_700,
                        ),
                    ]
                )

        question_table.setStyle(
            TableStyle(question_style)
        )

        story.append(question_table)

        if high_override_rows:
            story.extend(
                [
                    Spacer(1, 5 * mm),
                    Table(
                        [
                            [
                                Paragraph(
                                    (
                                        "<b>High Override:</b> The "
                                        "Employee and Senior Manager "
                                        "scores differ by 3.00 points "
                                        "or more. The question's combined "
                                        "mean is hidden because it could "
                                        "mask opposing perceptions."
                                    ),
                                    styles["callout"],
                                )
                            ]
                        ],
                        colWidths=[172 * mm],
                        style=TableStyle(
                            [
                                (
                                    "BACKGROUND",
                                    (0, 0),
                                    (-1, -1),
                                    RED_100,
                                ),
                                (
                                    "BOX",
                                    (0, 0),
                                    (-1, -1),
                                    0.7,
                                    colors.HexColor("#FCA5A5"),
                                ),
                                (
                                    "LEFTPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    8,
                                ),
                                (
                                    "RIGHTPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    8,
                                ),
                                (
                                    "TOPPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    7,
                                ),
                                (
                                    "BOTTOMPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    7,
                                ),
                            ]
                        ),
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

    story.extend(
        [
            PageBreak(),
            _heading("AI-supported improvement analysis", styles),
        ]
    )

    if analysis is None:
        story.append(
            Paragraph(
                (
                    "No saved AI analysis was available when this "
                    "report was generated. The calculated assessment "
                    "results remain valid; generate the AI analysis "
                    "from the results page to include recommendations."
                ),
                styles["body"],
            )
        )
    elif analysis.status != "completed":
        story.append(
            Paragraph(
                (
                    "The saved AI analysis is not complete. Current "
                    f"status: {_safe_text(analysis.status)}."
                ),
                styles["body"],
            )
        )
    else:
        story.extend(
            [
                Paragraph(
                    "Overall summary",
                    styles["subsection"],
                ),
                Paragraph(
                    _safe_text(
                        analysis.overall_summary
                        or "No summary was returned."
                    ),
                    styles["body"],
                ),
            ]
        )

        domain_data = _normalise_dict(
            analysis.domain_summaries
        )
        key_strengths = _normalise_list(
            domain_data.get("key_strengths")
        )
        key_risks = _normalise_list(
            domain_data.get("key_risks")
        )
        ai_domains = _normalise_list(
            domain_data.get("domains")
        )
        limitations = _normalise_list(
            domain_data.get("limitations")
        )
        guidance_sources = _normalise_list(
            domain_data.get("guidance_sources")
        )

        strengths_risks = Table(
            [
                [
                    Paragraph(
                        "<b>Key strengths</b>",
                        styles["subsection"],
                    ),
                    Paragraph(
                        "<b>Key risks</b>",
                        styles["subsection"],
                    ),
                ],
                [
                    [
                        *_bullet_items(
                            key_strengths,
                            styles,
                        )
                    ]
                    or [
                        Paragraph(
                            "No strengths were returned.",
                            styles["body"],
                        )
                    ],
                    [
                        *_bullet_items(
                            key_risks,
                            styles,
                        )
                    ]
                    or [
                        Paragraph(
                            "No risks were returned.",
                            styles["body"],
                        )
                    ],
                ],
            ],
            colWidths=[84 * mm, 84 * mm],
        )

        strengths_risks.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), GREEN_100),
                    ("BACKGROUND", (1, 0), (1, -1), RED_100),
                    ("BOX", (0, 0), (-1, -1), 0.5, SLATE_200),
                    ("INNERGRID", (0, 0), (-1, -1), 0.35, SLATE_200),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        story.extend(
            [
                Spacer(1, 3 * mm),
                strengths_risks,
                Spacer(1, 6 * mm),
                Paragraph(
                    "Domain analysis",
                    styles["subsection"],
                ),
            ]
        )

        for item in ai_domains:
            domain_summary = _normalise_dict(item)

            if not domain_summary:
                continue

            title = str(
                domain_summary.get(
                    "domain_name",
                    "Domain",
                )
            )
            maturity = str(
                domain_summary.get(
                    "maturity_level",
                    "",
                )
            )
            score_value = domain_summary.get(
                "score"
            )
            summary = domain_summary.get(
                "summary",
                "",
            )
            strengths = _normalise_list(
                domain_summary.get("strengths")
            )
            improvements = _normalise_list(
                domain_summary.get(
                    "improvement_areas"
                )
            )

            maturity_background, maturity_colour = (
                _maturity_colours(maturity)
            )

            domain_flowables: list[Any] = [
                Table(
                    [
                        [
                            Paragraph(
                                f"<b>{_safe_text(title)}</b>",
                                styles["subsection"],
                            ),
                            Paragraph(
                                (
                                    f'<font color="{maturity_colour.hexval()}">'
                                    f"<b>{_safe_text(maturity)}</b>"
                                    f"</font>"
                                ),
                                styles["centre"],
                            ),
                            Paragraph(
                                f"<b>{_score(score_value)}</b>",
                                styles["centre"],
                            ),
                        ]
                    ],
                    colWidths=[
                        92 * mm,
                        42 * mm,
                        34 * mm,
                    ],
                    style=TableStyle(
                        [
                            (
                                "BACKGROUND",
                                (0, 0),
                                (0, 0),
                                SLATE_100,
                            ),
                            (
                                "BACKGROUND",
                                (1, 0),
                                (1, 0),
                                maturity_background,
                            ),
                            (
                                "BACKGROUND",
                                (2, 0),
                                (2, 0),
                                colors.HexColor("#ECFEFF"),
                            ),
                            (
                                "BOX",
                                (0, 0),
                                (-1, -1),
                                0.5,
                                SLATE_200,
                            ),
                            (
                                "INNERGRID",
                                (0, 0),
                                (-1, -1),
                                0.35,
                                SLATE_200,
                            ),
                            (
                                "LEFTPADDING",
                                (0, 0),
                                (-1, -1),
                                7,
                            ),
                            (
                                "RIGHTPADDING",
                                (0, 0),
                                (-1, -1),
                                7,
                            ),
                            (
                                "TOPPADDING",
                                (0, 0),
                                (-1, -1),
                                6,
                            ),
                            (
                                "BOTTOMPADDING",
                                (0, 0),
                                (-1, -1),
                                6,
                            ),
                            (
                                "VALIGN",
                                (0, 0),
                                (-1, -1),
                                "MIDDLE",
                            ),
                        ]
                    ),
                ),
                Paragraph(
                    _safe_text(summary),
                    styles["body"],
                ),
            ]

            if strengths:
                domain_flowables.append(
                    Spacer(1, 2 * mm)
                )
                domain_flowables.append(
                    Paragraph(
                        "<b>Strengths</b>",
                        styles["body"],
                    )
                )
                domain_flowables.extend(
                    _bullet_items(
                        strengths,
                        styles,
                    )
                )

            if improvements:
                domain_flowables.append(
                    Spacer(1, 2.5 * mm)
                )
                domain_flowables.append(
                    Paragraph(
                        "<b>Improvement areas</b>",
                        styles["body"],
                    )
                )
                domain_flowables.extend(
                    _bullet_items(
                        improvements,
                        styles,
                    )
                )

            story.extend(
                [
                    KeepTogether(domain_flowables),
                    Spacer(1, 7 * mm),
                ]
            )

        priority_actions = _normalise_list(
            analysis.priority_actions
        )

        if priority_actions:
            story.extend(
                [
                    PageBreak(),
                    _heading("Priority actions", styles),
                ]
            )

            for action in priority_actions:
                action_data = _normalise_dict(action)

                if not action_data:
                    continue

                priority = action_data.get(
                    "priority",
                    "",
                )
                title = action_data.get(
                    "title",
                    "Priority action",
                )
                related_domain = action_data.get(
                    "related_domain",
                    "",
                )
                urgency = action_data.get(
                    "urgency",
                    "",
                )
                evidence = _normalise_list(
                    action_data.get(
                        "assessment_evidence"
                    )
                )
                reason = action_data.get(
                    "reason",
                    "",
                )
                recommended_action = action_data.get(
                    "recommended_action",
                    "",
                )
                source_relevance = action_data.get(
                    "source_relevance",
                    "",
                )

                action_story: list[Any] = [
                    Table(
                        [
                            [
                                Paragraph(
                                    (
                                        f"<b>Priority "
                                        f"{_safe_text(priority)}: "
                                        f"{_safe_text(title)}</b>"
                                    ),
                                    styles["subsection"],
                                ),
                                Paragraph(
                                    _safe_text(urgency),
                                    styles["centre"],
                                ),
                            ]
                        ],
                        colWidths=[
                            133 * mm,
                            35 * mm,
                        ],
                        style=TableStyle(
                            [
                                (
                                    "BACKGROUND",
                                    (0, 0),
                                    (0, 0),
                                    VIOLET_100,
                                ),
                                (
                                    "BACKGROUND",
                                    (1, 0),
                                    (1, 0),
                                    ORANGE_100,
                                ),
                                (
                                    "BOX",
                                    (0, 0),
                                    (-1, -1),
                                    0.5,
                                    SLATE_200,
                                ),
                                (
                                    "LEFTPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    8,
                                ),
                                (
                                    "RIGHTPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    8,
                                ),
                                (
                                    "TOPPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    6,
                                ),
                                (
                                    "BOTTOMPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    6,
                                ),
                            ]
                        ),
                    ),
                    Paragraph(
                        (
                            f"<b>Related domain:</b> "
                            f"{_safe_text(related_domain)}"
                        ),
                        styles["body"],
                    ),
                ]

                if evidence:
                    action_story.append(
                        Paragraph(
                            "<b>Assessment evidence</b>",
                            styles["body"],
                        )
                    )
                    action_story.extend(
                        _bullet_items(
                            evidence,
                            styles,
                        )
                    )

                action_story.extend(
                    [
                        Paragraph(
                            "<b>Why this matters</b>",
                            styles["body"],
                        ),
                        Paragraph(
                            _safe_text(reason),
                            styles["body"],
                        ),
                        Table(
                            [
                                [
                                    Paragraph(
                                        (
                                            "<b>Recommended action</b><br/>"
                                            f"{_safe_text(recommended_action)}"
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
                                    (
                                        "BOX",
                                        (0, 0),
                                        (-1, -1),
                                        0.5,
                                        SLATE_200,
                                    ),
                                    (
                                        "LEFTPADDING",
                                        (0, 0),
                                        (-1, -1),
                                        8,
                                    ),
                                    (
                                        "RIGHTPADDING",
                                        (0, 0),
                                        (-1, -1),
                                        8,
                                    ),
                                    (
                                        "TOPPADDING",
                                        (0, 0),
                                        (-1, -1),
                                        7,
                                    ),
                                    (
                                        "BOTTOMPADDING",
                                        (0, 0),
                                        (-1, -1),
                                        7,
                                    ),
                                ]
                            ),
                        ),
                    ]
                )

                if source_relevance:
                    action_story.append(
                        Paragraph(
                            (
                                f"<b>Source relevance:</b> "
                                f"{_safe_text(source_relevance)}"
                            ),
                            styles["small"],
                        )
                    )

                story.extend(
                    [
                        KeepTogether(action_story),
                        Spacer(1, 6 * mm),
                    ]
                )

        roadmap = _normalise_list(
            analysis.roadmap
        )

        if roadmap:
            story.extend(
                [
                    PageBreak(),
                    _heading("Improvement roadmap", styles),
                ]
            )

            for index, roadmap_item in enumerate(
                roadmap,
                start=1,
            ):
                item = _normalise_dict(
                    roadmap_item
                )

                if not item:
                    continue

                timeframe = item.get(
                    "timeframe",
                    "",
                )
                objective = item.get(
                    "objective",
                    "",
                )
                actions = _normalise_list(
                    item.get("actions")
                )
                success_indicator = item.get(
                    "success_indicator",
                    "",
                )

                roadmap_story: list[Any] = [
                    Table(
                        [
                            [
                                Paragraph(
                                    f"<b>Step {index}</b>",
                                    styles["centre"],
                                ),
                                Paragraph(
                                    (
                                        f"<b>{_safe_text(timeframe)}</b><br/>"
                                        f"{_safe_text(objective)}"
                                    ),
                                    styles["body"],
                                ),
                            ]
                        ],
                        colWidths=[
                            26 * mm,
                            142 * mm,
                        ],
                        style=TableStyle(
                            [
                                (
                                    "BACKGROUND",
                                    (0, 0),
                                    (0, 0),
                                    colors.HexColor("#CFFAFE"),
                                ),
                                (
                                    "BACKGROUND",
                                    (1, 0),
                                    (1, 0),
                                    SLATE_100,
                                ),
                                (
                                    "BOX",
                                    (0, 0),
                                    (-1, -1),
                                    0.5,
                                    SLATE_200,
                                ),
                                (
                                    "LEFTPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    8,
                                ),
                                (
                                    "RIGHTPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    8,
                                ),
                                (
                                    "TOPPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    7,
                                ),
                                (
                                    "BOTTOMPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    7,
                                ),
                                (
                                    "VALIGN",
                                    (0, 0),
                                    (-1, -1),
                                    "MIDDLE",
                                ),
                            ]
                        ),
                    ),
                ]

                if actions:
                    roadmap_story.append(
                        Paragraph(
                            "<b>Actions</b>",
                            styles["body"],
                        )
                    )
                    roadmap_story.extend(
                        _bullet_items(
                            actions,
                            styles,
                        )
                    )

                roadmap_story.append(
                    Table(
                        [
                            [
                                Paragraph(
                                    (
                                        "<b>Success indicator</b><br/>"
                                        f"{_safe_text(success_indicator)}"
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
                                    GREEN_100,
                                ),
                                (
                                    "BOX",
                                    (0, 0),
                                    (-1, -1),
                                    0.5,
                                    colors.HexColor("#6EE7B7"),
                                ),
                                (
                                    "LEFTPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    8,
                                ),
                                (
                                    "RIGHTPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    8,
                                ),
                                (
                                    "TOPPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    7,
                                ),
                                (
                                    "BOTTOMPADDING",
                                    (0, 0),
                                    (-1, -1),
                                    7,
                                ),
                            ]
                        ),
                    )
                )

                story.extend(
                    [
                        KeepTogether(roadmap_story),
                        Spacer(1, 6 * mm),
                    ]
                )

        if guidance_sources or limitations:
            story.extend(
                [
                    PageBreak(),
                    _heading(
                        "Guidance sources and limitations",
                        styles,
                    ),
                ]
            )

        if guidance_sources:
            story.append(
                Paragraph(
                    (
                        "The AI analysis was grounded using the "
                        "curated official WorkSafe SafePlus sources "
                        "listed below."
                    ),
                    styles["body"],
                )
            )

            source_table_data: list[list[Any]] = [
                [
                    Paragraph(
                        "Source",
                        styles["table_header"],
                    ),
                    Paragraph(
                        "Reference",
                        styles["table_header"],
                    ),
                ]
            ]

            for source_item in guidance_sources:
                source = _normalise_dict(
                    source_item
                )

                if not source:
                    continue

                title = source.get(
                    "title",
                    "WorkSafe source",
                )
                url = source.get("url", "")
                source_id = source.get(
                    "source_id",
                    "",
                )

                source_table_data.append(
                    [
                        Paragraph(
                            f"<b>{_safe_text(title)}</b>",
                            styles["table_cell"],
                        ),
                        Paragraph(
                            (
                                f"{_safe_text(source_id)}<br/>"
                                f"{_safe_text(url)}"
                            ),
                            styles["tiny"],
                        ),
                    ]
                )

            source_table = Table(
                source_table_data,
                colWidths=[
                    73 * mm,
                    95 * mm,
                ],
                repeatRows=1,
            )

            source_table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            DARK_CYAN,
                        ),
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            SLATE_300,
                        ),
                        (
                            "INNERGRID",
                            (0, 0),
                            (-1, -1),
                            0.35,
                            SLATE_200,
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            6,
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            6,
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            5,
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "TOP",
                        ),
                    ]
                )
            )

            story.extend(
                [
                    source_table,
                    Spacer(1, 6 * mm),
                ]
            )

        if limitations:
            story.extend(
                [
                    Paragraph(
                        "Important limitations",
                        styles["subsection"],
                    ),
                    *_bullet_items(
                        limitations,
                        styles,
                    ),
                ]
            )

        story.extend(
            [
                Spacer(1, 6 * mm),
                Table(
                    [
                        [
                            Paragraph(
                                (
                                    "<b>AI provider:</b> "
                                    f"{_safe_text(analysis.ai_provider)}<br/>"
                                    "<b>Generated:</b> "
                                    f"{_date(analysis.generated_at)}"
                                ),
                                styles["small"],
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
                                VIOLET_100,
                            ),
                            (
                                "BOX",
                                (0, 0),
                                (-1, -1),
                                0.5,
                                colors.HexColor("#C4B5FD"),
                            ),
                            (
                                "LEFTPADDING",
                                (0, 0),
                                (-1, -1),
                                8,
                            ),
                            (
                                "RIGHTPADDING",
                                (0, 0),
                                (-1, -1),
                                8,
                            ),
                            (
                                "TOPPADDING",
                                (0, 0),
                                (-1, -1),
                                7,
                            ),
                            (
                                "BOTTOMPADDING",
                                (0, 0),
                                (-1, -1),
                                7,
                            ),
                        ]
                    ),
                ),
            ]
        )

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

    document.build(
        story,
        onFirstPage=_page_header_footer,
        onLaterPages=_page_header_footer,
    )

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes