"""AI sections of the full report: sources, limitations and disclaimer."""

from __future__ import annotations

from typing import Any

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle

from app.models import AIAnalysis
from app.services.reports.blocks import bullet_items, section_heading
from app.services.reports.helpers import as_dict, date_text, html_text
from app.services.reports.styles import (
    DARK_CYAN,
    SLATE_200,
    SLATE_300,
    VIOLET_100,
)


def sources_limitations_section(
    styles: dict[str, ParagraphStyle],
    guidance_sources: list[Any],
    limitations: list[Any],
) -> list[Any]:
    """Guidance sources and important limitations."""

    story: list[Any] = []

    if guidance_sources or limitations:
        story.extend(
            [
                PageBreak(),
                section_heading(
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
            source = as_dict(
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
                        f"<b>{html_text(title)}</b>",
                        styles["table_cell"],
                    ),
                    Paragraph(
                        (
                            f"{html_text(source_id)}<br/>"
                            f"{html_text(url)}"
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
                *bullet_items(
                    limitations,
                    styles,
                ),
            ]
        )

    return story


def ai_disclaimer_section(
    analysis: AIAnalysis | None,
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Closing disclaimer for the AI analysis."""

    story: list[Any] = []

    story.extend(
        [
            Spacer(1, 6 * mm),
            Table(
                [
                    [
                        Paragraph(
                            (
                                "<b>AI analysis:</b> written by "
                                f"{html_text(analysis.ai_provider)} on "
                                f"{date_text(analysis.generated_at)}. "
                                "It is included here because "
                                "“With AI analysis” was chosen "
                                "when downloading this report. The "
                                "calculated results above do not "
                                "depend on it."
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

    return story
