"""AI sections of the full report: summary, strengths, risks and domains."""

from __future__ import annotations

from typing import Any

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.models import AIAnalysis
from app.services.report_components import maturity_chip
from app.services.reports.blocks import bullet_items
from app.services.reports.helpers import (
    as_dict,
    as_list,
    html_text,
    score_text,
)
from app.services.reports.styles import (
    GREEN_100,
    RED_100,
    SLATE_100,
    SLATE_200,
    WHITE,
)


def overall_summary_section(
    analysis: AIAnalysis | None,
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Overall summary paragraph."""

    story: list[Any] = []

    story.extend(
        [
            Paragraph(
                "Overall summary",
                styles["subsection"],
            ),
            Paragraph(
                html_text(
                    analysis.overall_summary
                    or "No summary was returned."
                ),
                styles["body"],
            ),
        ]
    )

    return story


def strengths_risks_section(
    styles: dict[str, ParagraphStyle],
    key_risks: list[Any],
    key_strengths: list[Any],
) -> list[Any]:
    """Key strengths and key risks side by side."""

    story: list[Any] = []

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
                    *bullet_items(
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
                    *bullet_items(
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

    return story


def domain_summaries_section(
    styles: dict[str, ParagraphStyle],
    ai_domains: list[Any],
) -> list[Any]:
    """One AI summary block for each domain."""

    story: list[Any] = []

    for item in ai_domains:
        domain_summary = as_dict(item)

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
        strengths = as_list(
            domain_summary.get("strengths")
        )
        improvements = as_list(
            domain_summary.get(
                "improvement_areas"
            )
        )

        domain_flowables: list[Any] = [
            Table(
                [
                    [
                        Paragraph(
                            f"<b>{html_text(title)}</b>",
                            styles["subsection"],
                        ),
                        maturity_chip(
                            str(maturity),
                            styles,
                            width=34 * mm,
                        ),
                        Paragraph(
                            f"<b>{score_text(score_value)}</b>",
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
                            WHITE,
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
                html_text(summary),
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
                bullet_items(
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
                bullet_items(
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

    return story
