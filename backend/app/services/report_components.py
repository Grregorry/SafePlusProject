"""Shared building blocks for the SafePlus PDF reports.

Wording, colours and layout follow the results page, so a downloaded
report reads the same way as the screen:

* maturity is one cyan ladder with the level always named in text,
  never red/amber/green;
* intervention tiers are labelled chips, so the colour never carries
  the meaning on its own;
* a combined mean is hidden where the two groups differ by 3.00 or
  more, and that question is marked High Override;
* the radar plots one spoke per question, not per domain.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from html import escape
from math import cos, pi, sin
from typing import Any, Iterable, Sequence

from reportlab.graphics.shapes import (
    Circle,
    Drawing,
    Line,
    Polygon,
    Rect,
    String,
)
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Assessment,
    AssessmentQuestion,
    ManualResponseCount,
    SurveySubmission,
)

# Scale and thresholds mirror get_maturity_level and
# get_intervention_tier in app/services/scoring.py.
SCALE_MIN = Decimal("1")
SCALE_MAX = Decimal("5")
DEVELOPING_MAX = Decimal("2.50")
LEADING_MIN = Decimal("4.50")
HIDDEN_GAP = Decimal("3.00")

WHITE = colors.white
SLATE_900 = colors.HexColor("#0F172A")
SLATE_800 = colors.HexColor("#1E293B")
SLATE_700 = colors.HexColor("#334155")
SLATE_600 = colors.HexColor("#475569")
SLATE_500 = colors.HexColor("#64748B")
SLATE_400 = colors.HexColor("#94A3B8")
SLATE_300 = colors.HexColor("#CBD5E1")
SLATE_200 = colors.HexColor("#E2E8F0")
SLATE_100 = colors.HexColor("#F1F5F9")
SLATE_50 = colors.HexColor("#F8FAFC")

# One hue at three strengths for maturity, matching the ladder on the
# results page.
CYAN_50 = colors.HexColor("#ECFEFF")
CYAN_100 = colors.HexColor("#CFFAFE")
CYAN_200 = colors.HexColor("#A5F3FC")
CYAN_700 = colors.HexColor("#0E7490")
CYAN_800 = colors.HexColor("#155E75")
CYAN_950 = colors.HexColor("#083344")

# Lowest-scoring question. Deliberately not red, and distinct from the
# cyan maturity scale and the violet used for AI content.
LOWEST = colors.HexColor("#1D4ED8")

VIOLET_50 = colors.HexColor("#F5F3FF")
VIOLET_300 = colors.HexColor("#C4B5FD")
VIOLET_800 = colors.HexColor("#5B21B6")

# Tier chips, flattened onto white from the results page colours
# (red-800, red-600/60, orange-400/60, yellow-300/60, #A1FB8E/20).
TIER_COLOURS: dict[str, tuple[colors.Color, colors.Color]] = {
    "High Override": (colors.HexColor("#991B1B"), WHITE),
    "High": (colors.HexColor("#EA7D7D"), colors.HexColor("#450A0A")),
    "Medium": (colors.HexColor("#FDBE8A"), SLATE_900),
    "Low": (colors.HexColor("#FEEC91"), SLATE_900),
    "Not flagged": (colors.HexColor("#ECFEE8"), SLATE_800),
}

MATURITY_MEANINGS = {
    "Developing": "Not yet performing well in this area. Action is needed.",
    "Performing": "Performing adequately. Improvement is possible.",
    "Leading": "Performing at a high level in this area.",
}

# One row per tier; each "or" line in the score column pairs with the
# same line in the gap column. Follows get_intervention_tier.
TIER_RULES: list[tuple[str, list[tuple[str, str]]]] = [
    ("High Override", [("Any score", "≥ 3.00")]),
    ("High", [("≤ 2.50", "> 1.50 and < 3.00")]),
    (
        "Medium",
        [
            ("≤ 2.50", "≤ 1.50"),
            ("> 2.50 and ≤ 3.50", "> 1.50 and < 3.00"),
        ],
    ),
    (
        "Low",
        [
            ("> 2.50 and ≤ 3.50", "≤ 1.50"),
            ("> 3.50 and < 4.50", "> 1.50 and < 3.00"),
        ],
    ),
    (
        "Not flagged",
        [
            ("> 3.50 and < 4.50", "≤ 1.50"),
            ("≥ 4.50", "< 3.00"),
        ],
    ),
]

RESPONSE_ENCODING = [
    ("Strongly Agree", "5"),
    ("Agree", "4"),
    ("Neither Agree nor Disagree", "3"),
    ("Disagree", "2"),
    ("Strongly Disagree", "1"),
    ("N/A", "Excluded"),
]


# ---------------------------------------------------------------------------
# Values and wording


def safe_text(value: object) -> str:
    if value is None:
        return ""

    return escape(str(value))


def to_decimal(value: object) -> Decimal | None:
    if value is None:
        return None

    try:
        return Decimal(str(value))
    except Exception:
        return None


def format_score(value: object) -> str:
    number = to_decimal(value)

    if number is None:
        return "Not available"

    return f"{number:.2f}"


def format_long_date(value: datetime | None) -> str:
    if value is None:
        return "Not available"

    return value.astimezone().strftime("%d %B %Y")


def is_hidden(opinion_gap: object) -> bool:
    """A gap of 3.00 or more hides the combined mean."""

    gap = to_decimal(opinion_gap)

    return gap is not None and gap >= HIDDEN_GAP


def tier_label(intervention_tier: object, opinion_gap: object) -> str:
    if is_hidden(opinion_gap):
        return "High Override"

    return str(intervention_tier or "Not flagged")


def combined_display(combined_mean: object, opinion_gap: object) -> str:
    if is_hidden(opinion_gap):
        return "Hidden"

    return format_score(combined_mean)


def maturity_level(score: object) -> str:
    number = to_decimal(score)

    if number is None:
        return "Not available"

    if number <= DEVELOPING_MAX:
        return "Developing"

    if number >= LEADING_MIN:
        return "Leading"

    return "Performing"


def distance_text(score: object) -> str:
    """"0.92 below Leading", as shown under each ladder."""

    number = to_decimal(score)

    if number is None:
        return ""

    if number <= DEVELOPING_MAX:
        return f"{DEVELOPING_MAX - number:.2f} below Performing"

    if number < LEADING_MIN:
        return f"{LEADING_MIN - number:.2f} below Leading"

    return "At the highest level"


def entry_counts(
    assessment: Assessment,
    database: Session,
) -> tuple[int, int]:
    """Online submissions and paper entries, as counted on the
    results page. Paper totals are entered one question at a time, so
    the most entries recorded for any question is the number of paper
    surveys for that group."""

    online = (
        database.scalar(
            select(func.count(SurveySubmission.id)).where(
                SurveySubmission.assessment_id == assessment.id,
                SurveySubmission.status == "submitted",
            )
        )
        or 0
    )

    paper = 0

    for respondent_group in ("Employee", "Senior Manager"):
        per_question = database.scalars(
            select(
                func.coalesce(func.sum(ManualResponseCount.count), 0)
            )
            .join(
                AssessmentQuestion,
                ManualResponseCount.assessment_question_id
                == AssessmentQuestion.id,
            )
            .where(
                AssessmentQuestion.assessment_id == assessment.id,
                AssessmentQuestion.is_active.is_(True),
                ManualResponseCount.respondent_group == respondent_group,
                ManualResponseCount.response_option != "N/A",
            )
            .group_by(ManualResponseCount.assessment_question_id)
        ).all()

        paper += max(per_question, default=0)

    return int(online), int(paper)


def meta_line(
    assessment: Assessment,
    online: int,
    paper: int,
) -> str:
    """"Opened 14 September 2026 · Closed 14 September 2026 ·
    20 entries (20 online, 0 paper)"."""

    parts = [f"Opened {format_long_date(assessment.created_at)}"]

    if assessment.completed_at is not None:
        parts.append(f"Closed {format_long_date(assessment.completed_at)}")

    total = online + paper
    parts.append(
        f"{total} {'entry' if total == 1 else 'entries'} "
        f"({online} online, {paper} paper)"
    )

    return " · ".join(parts)


# ---------------------------------------------------------------------------
# Chips and small tables


def tier_chip(
    tier: str,
    styles: dict[str, ParagraphStyle],
    width: float = 26 * mm,
) -> Table:
    """The tier as a labelled chip: colour plus the name in text."""

    background, text_colour = TIER_COLOURS.get(
        tier,
        TIER_COLOURS["Not flagged"],
    )

    chip = Table(
        [
            [
                Paragraph(
                    f'<font color="{text_colour.hexval()}">'
                    f"<b>{safe_text(tier)}</b></font>",
                    styles["table_cell"],
                )
            ]
        ],
        colWidths=[width],
    )

    chip.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    return chip


MATURITY_COLOURS: dict[str, tuple[colors.Color, colors.Color]] = {
    "Leading": (CYAN_800, WHITE),
    "Performing": (CYAN_200, CYAN_950),
    "Developing": (CYAN_50, CYAN_950),
}


def maturity_chip(
    level: str,
    styles: dict[str, ParagraphStyle],
    width: float = 24 * mm,
) -> Table:
    """One hue at three strengths, with the level always named, so
    maturity never reads as red/amber/green."""

    background, text_colour = MATURITY_COLOURS.get(
        level,
        (SLATE_100, SLATE_700),
    )

    chip = Table(
        [
            [
                Paragraph(
                    f'<font color="{text_colour.hexval()}">'
                    f"<b>{safe_text(level)}</b></font>",
                    styles["table_cell"],
                )
            ]
        ],
        colWidths=[width],
    )

    chip.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("BOX", (0, 0), (-1, -1), 0.4, CYAN_200),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    return chip


def source_chips(
    sources: Sequence[str],
    styles: dict[str, ParagraphStyle],
    width: float = 168 * mm,
) -> Table | None:
    """The WorkSafe sources under an AI item, as on the results page."""

    labels = [safe_text(source) for source in sources if source]

    if not labels:
        return None

    table = Table(
        [
            [
                Paragraph(
                    "<b>WORKSAFE SOURCES</b>  "
                    + "   ·   ".join(labels),
                    styles["tiny"],
                )
            ]
        ],
        colWidths=[width],
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CYAN_50),
                ("BOX", (0, 0), (-1, -1), 0.4, CYAN_200),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    return table


# ---------------------------------------------------------------------------
# Maturity ladder


def _scale_fraction(value: Decimal) -> float:
    span = float(SCALE_MAX - SCALE_MIN)
    clamped = max(
        float(SCALE_MIN),
        min(float(SCALE_MAX), float(value)),
    )

    return (clamped - float(SCALE_MIN)) / span


def maturity_ladder(
    label: str,
    score: object,
    width: float = 150,
    show_label: bool = True,
) -> Drawing:
    """A track split into the three levels with a marker at the score,
    so the distance to the next threshold is visible, not just the
    number. The level is named in text, so colour is never the only
    cue."""

    number = to_decimal(score)
    height = 46 if show_label else 32
    drawing = Drawing(width, height)

    track_y = 18 if show_label else 16
    track_height = 7

    developing_width = width * _scale_fraction(DEVELOPING_MAX)
    leading_start = width * _scale_fraction(LEADING_MIN)

    segments = [
        (0.0, developing_width, CYAN_50, CYAN_200),
        (developing_width, leading_start - developing_width, CYAN_200, None),
        (leading_start, width - leading_start, CYAN_800, None),
    ]

    for start, segment_width, fill, stroke in segments:
        drawing.add(
            Rect(
                start,
                track_y,
                max(segment_width, 0.1),
                track_height,
                fillColor=fill,
                strokeColor=stroke,
                strokeWidth=0.5 if stroke else 0,
            )
        )

    if show_label:
        drawing.add(
            String(
                0,
                height - 9,
                label,
                fontName="Helvetica-Bold",
                fontSize=9,
                fillColor=SLATE_900,
            )
        )

        if number is not None:
            drawing.add(
                String(
                    width,
                    height - 9,
                    f"{number:.2f}  {maturity_level(number)}",
                    fontName="Helvetica-Bold",
                    fontSize=9,
                    fillColor=SLATE_900,
                    textAnchor="end",
                )
            )

    if number is not None:
        marker_x = width * _scale_fraction(number)

        drawing.add(
            Rect(
                max(0.0, min(width - 1.6, marker_x - 0.8)),
                track_y - 2.5,
                1.6,
                track_height + 5,
                fillColor=SLATE_900,
                strokeColor=None,
            )
        )

    for text, anchor, x_position in (
        ("Developing", "start", 0.0),
        ("Performing", "start", developing_width),
        ("Leading", "end", width),
    ):
        drawing.add(
            String(
                x_position,
                track_y - 10,
                text,
                fontName="Helvetica",
                fontSize=6.5,
                fillColor=SLATE_500,
                textAnchor=anchor,
            )
        )

    if number is not None:
        drawing.add(
            String(
                0,
                track_y - 19,
                distance_text(number),
                fontName="Helvetica-Bold",
                fontSize=7,
                fillColor=SLATE_600,
            )
        )

    return drawing


# ---------------------------------------------------------------------------
# Question profile radar


class ProfilePoint:
    """One scored question on the radar."""

    def __init__(
        self,
        label: str,
        value: object,
        hidden: bool = False,
        lowest: bool = False,
        domain_start: bool = False,
    ) -> None:
        self.label = label
        self.value = to_decimal(value)
        self.hidden = hidden
        self.lowest = lowest
        self.domain_start = domain_start


def question_profile(
    points: Sequence[ProfilePoint],
    width: float = 430,
    height: float = 430,
) -> Drawing:
    """One spoke per scored question, grouped by domain, so
    differences between questions are shown at their true size."""

    drawing = Drawing(width, height)

    centre_x = width / 2
    centre_y = height / 2
    radius = min(width, height) / 2 - 42

    count = max(len(points), 3)
    angles = [
        -pi / 2 + (2 * pi * index / count) for index in range(count)
    ]

    def point_at(angle: float, value: Decimal) -> tuple[float, float]:
        point_radius = radius * _scale_fraction(value)

        return (
            centre_x + point_radius * cos(angle),
            centre_y - point_radius * sin(angle),
        )

    def ring(value: Decimal, dashed: bool) -> None:
        ring_radius = radius * _scale_fraction(value)
        ring_points: list[float] = []

        for angle in angles:
            ring_points.extend(
                [
                    centre_x + ring_radius * cos(angle),
                    centre_y - ring_radius * sin(angle),
                ]
            )

        polygon = Polygon(
            ring_points,
            strokeColor=SLATE_400 if dashed else SLATE_300,
            fillColor=None,
            strokeWidth=0.6,
        )

        if dashed:
            polygon.strokeDashArray = [2, 2]

        drawing.add(polygon)

    for level in (Decimal("2"), Decimal("3"), Decimal("4"), SCALE_MAX):
        ring(level, False)

    # Dashed rings mark the Performing (above 2.50) and Leading (4.50)
    # thresholds.
    ring(DEVELOPING_MAX, True)
    ring(LEADING_MIN, True)

    for index, angle in enumerate(angles[: len(points)]):
        profile_point = points[index]
        end_x = centre_x + radius * cos(angle)
        end_y = centre_y - radius * sin(angle)

        drawing.add(
            Line(
                centre_x,
                centre_y,
                end_x,
                end_y,
                # Heavier spokes mark where each domain starts.
                strokeColor=(
                    SLATE_700 if profile_point.domain_start else SLATE_200
                ),
                strokeWidth=1.3 if profile_point.domain_start else 0.5,
            )
        )

        label_radius = radius + 13
        label_x = centre_x + label_radius * cos(angle)
        label_y = centre_y - label_radius * sin(angle) - 2

        anchor = "middle"

        if cos(angle) > 0.2:
            anchor = "start"
        elif cos(angle) < -0.2:
            anchor = "end"

        drawing.add(
            String(
                label_x,
                label_y,
                profile_point.label,
                fontName=(
                    "Helvetica-Bold" if profile_point.lowest else "Helvetica"
                ),
                fontSize=6.2,
                fillColor=LOWEST if profile_point.lowest else SLATE_600,
                textAnchor=anchor,
            )
        )

        if profile_point.lowest:
            drawing.add(
                String(
                    label_x,
                    label_y - 7,
                    "lowest",
                    fontName="Helvetica-Bold",
                    fontSize=5.6,
                    fillColor=LOWEST,
                    textAnchor=anchor,
                )
            )

    shape_points: list[float] = []

    for index, profile_point in enumerate(points):
        if profile_point.hidden or profile_point.value is None:
            continue

        x_position, y_position = point_at(
            angles[index],
            profile_point.value,
        )
        shape_points.extend([x_position, y_position])

    if len(shape_points) >= 6:
        drawing.add(
            Polygon(
                shape_points,
                strokeColor=CYAN_700,
                fillColor=colors.Color(
                    CYAN_200.red,
                    CYAN_200.green,
                    CYAN_200.blue,
                    alpha=0.45,
                ),
                strokeWidth=1.4,
            )
        )

    for index, profile_point in enumerate(points):
        if profile_point.hidden:
            # Hollow points on the outer ring are questions where the
            # two groups differ by 3.00 or more; the combined score is
            # not plotted because it would hide the split.
            x_position, y_position = point_at(angles[index], SCALE_MAX)

            drawing.add(
                Circle(
                    x_position,
                    y_position,
                    2.6,
                    fillColor=WHITE,
                    strokeColor=SLATE_700,
                    strokeWidth=0.9,
                )
            )
            continue

        if profile_point.value is None:
            continue

        x_position, y_position = point_at(
            angles[index],
            profile_point.value,
        )

        drawing.add(
            Circle(
                x_position,
                y_position,
                3.2 if profile_point.lowest else 2.0,
                fillColor=LOWEST if profile_point.lowest else CYAN_700,
                strokeColor=LOWEST if profile_point.lowest else CYAN_700,
            )
        )

    drawing.add(
        String(
            2,
            8,
            "Centre = 1   ·   Outer ring = 5",
            fontName="Helvetica",
            fontSize=6.5,
            fillColor=SLATE_500,
        )
    )

    return drawing


def profile_legend(
    domain_ranges: Sequence[tuple[str, str, str]],
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """"Clockwise from the top: Leadership 1.1-1.11 ..." plus the note
    about heavier spokes, dashed rings and hollow points."""

    parts = [
        f"<b>{safe_text(name)}</b> {safe_text(first)}–{safe_text(last)}"
        for name, first, last in domain_ranges
    ]

    return [
        Paragraph(
            "Clockwise from the top: " + " · ".join(parts),
            styles["centre"],
        ),
        Spacer(1, 2 * mm),
        Paragraph(
            "Heavier spokes mark where each domain starts. Dashed rings "
            "mark the Performing (above 2.50) and Leading (4.50) "
            "thresholds. Hollow points on the outer ring are questions "
            "where employees and managers differ by 3.00 or more; their "
            "combined score is not plotted because it would hide the "
            "split.",
            styles["small"],
        ),
    ]


# ---------------------------------------------------------------------------
# How scores and tiers are calculated


def _plain_table(
    data: list[list[Any]],
    column_widths: list[float],
) -> Table:
    table = Table(data, colWidths=column_widths, repeatRows=1)

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), SLATE_100),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, SLATE_300),
                ("LINEBELOW", (0, 1), (-1, -2), 0.3, SLATE_200),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    return table


def how_scores_are_calculated(
    domain_workings: Sequence[tuple[str, Decimal, int, Decimal]],
    overall_score: object,
    styles: dict[str, ParagraphStyle],
    width: float = 168 * mm,
) -> list[Any]:
    """The same explanation the results page shows under the question
    table: worked example, response encoding, maturity thresholds,
    opinion gap and the intervention tier table."""

    title = "How scores and tiers are calculated"
    heading = Paragraph(title, styles["subsection"])
    # Picked up by the report's contents page.
    heading.toc_entry = (1, title)

    flowables: list[Any] = [heading]

    if domain_workings:
        flowables.extend(
            [
                Paragraph(
                    "<b>Worked example from this assessment</b>",
                    styles["body"],
                ),
                Paragraph(
                    "A domain score is the average of the combined means "
                    "of its scored questions. The overall score is the "
                    "average of the three domain scores. Each step is "
                    "rounded to two decimals.",
                    styles["body"],
                ),
            ]
        )

        working_rows = [
            [
                Paragraph(
                    f"{safe_text(name)}: {total:.2f} ÷ {count} "
                    f"{'question' if count == 1 else 'questions'} "
                    f"= {mean:.2f}",
                    styles["table_cell"],
                )
            ]
            for name, total, count, mean in domain_workings
        ]

        overall = to_decimal(overall_score)

        if overall is not None:
            means = " + ".join(
                f"{mean:.2f}" for _name, _total, _count, mean in domain_workings
            )
            working_rows.append(
                [
                    Paragraph(
                        f"Overall: ({means}) ÷ "
                        f"{len(domain_workings)} = {overall:.2f}",
                        styles["table_cell"],
                    )
                ]
            )

        workings_table = Table(working_rows, colWidths=[width])
        workings_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), CYAN_50),
                    ("LINEBELOW", (0, 0), (-1, -2), 0.4, WHITE),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        flowables.extend([workings_table, Spacer(1, 5 * mm)])

    flowables.extend(
        [
            Paragraph("<b>Response encoding</b>", styles["body"]),
            Paragraph(
                "Every response is converted to a number before any score "
                "is calculated. N/A responses (situation-dependent "
                "questions only) are excluded from both the numerator and "
                "denominator.",
                styles["body"],
            ),
            _plain_table(
                [
                    [
                        Paragraph("<b>Response</b>", styles["table_cell_bold"]),
                        Paragraph("<b>Score</b>", styles["table_cell_bold"]),
                    ],
                    *[
                        [
                            Paragraph(response, styles["table_cell"]),
                            Paragraph(value, styles["table_cell"]),
                        ]
                        for response, value in RESPONSE_ENCODING
                    ],
                ],
                [width * 0.6, width * 0.4],
            ),
            Spacer(1, 5 * mm),
            Paragraph("<b>Maturity thresholds</b>", styles["body"]),
            Paragraph(
                "Applied to the Combined mean score — the average of "
                "the Employee mean and the Senior Manager mean.",
                styles["body"],
            ),
            _plain_table(
                [
                    [
                        Paragraph(
                            "<b>Maturity level</b>",
                            styles["table_cell_bold"],
                        ),
                        Paragraph(
                            "<b>Combined mean score</b>",
                            styles["table_cell_bold"],
                        ),
                        Paragraph("<b>Meaning</b>", styles["table_cell_bold"]),
                    ],
                    [
                        Paragraph("Developing", styles["table_cell"]),
                        Paragraph("≤ 2.50", styles["table_cell"]),
                        Paragraph(
                            MATURITY_MEANINGS["Developing"],
                            styles["table_cell"],
                        ),
                    ],
                    [
                        Paragraph("Performing", styles["table_cell"]),
                        Paragraph(
                            "&gt; 2.50 and &lt; 4.50",
                            styles["table_cell"],
                        ),
                        Paragraph(
                            MATURITY_MEANINGS["Performing"],
                            styles["table_cell"],
                        ),
                    ],
                    [
                        Paragraph("Leading", styles["table_cell"]),
                        Paragraph("≥ 4.50", styles["table_cell"]),
                        Paragraph(
                            MATURITY_MEANINGS["Leading"],
                            styles["table_cell"],
                        ),
                    ],
                ],
                [width * 0.22, width * 0.26, width * 0.52],
            ),
            Spacer(1, 5 * mm),
            Paragraph("<b>Opinion gap</b>", styles["body"]),
            Paragraph(
                "The absolute difference between the Employee mean and the "
                "Senior Manager mean for a question — how differently "
                "the two groups perceive the same practice. A higher gap is "
                "not automatically a problem, but it is a signal worth "
                "investigating.",
                styles["body"],
            ),
            Spacer(1, 2 * mm),
            Paragraph("<b>Intervention tier</b>", styles["body"]),
            tier_rules_table(styles, width),
        ]
    )

    return flowables


def tier_rules_table(
    styles: dict[str, ParagraphStyle],
    width: float = 168 * mm,
) -> Table:
    """One row per tier; each "or" line in the score column pairs with
    the same line in the gap column."""

    data: list[list[Any]] = [
        [
            Paragraph("<b>Tier</b>", styles["table_cell_bold"]),
            Paragraph("<b>Combined mean score</b>", styles["table_cell_bold"]),
            Paragraph("<b>Opinion gap</b>", styles["table_cell_bold"]),
        ]
    ]

    def lines(values: Iterable[str]) -> str:
        parts = list(values)

        return "<br/>".join(
            part
            if index == 0
            else f'<font color="{SLATE_500.hexval()}">or</font> {part}'
            for index, part in enumerate(parts)
        )

    for tier, conditions in TIER_RULES:
        data.append(
            [
                tier_chip(tier, styles, width=width * 0.2 - 12),
                Paragraph(
                    lines(score for score, _gap in conditions),
                    styles["table_cell"],
                ),
                Paragraph(
                    lines(gap for _score, gap in conditions),
                    styles["table_cell"],
                ),
            ]
        )

    return _plain_table(
        data,
        [width * 0.2, width * 0.42, width * 0.38],
    )
