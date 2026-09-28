"""AI sections of the full report: priority actions and roadmap."""

from __future__ import annotations

from typing import Any

from reportlab.lib import colors
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

from app.models import AIAnalysis
from app.services.report_components import source_chips, tier_chip
from app.services.reports.blocks import (
    bullet_items,
    section_heading,
    source_titles,
)
from app.services.reports.helpers import as_dict, as_list, html_text
from app.services.reports.styles import (
    GREEN_100,
    SLATE_100,
    SLATE_200,
    VIOLET_100,
    WHITE,
)


def priority_actions_section(
    analysis: AIAnalysis | None,
    styles: dict[str, ParagraphStyle],
    guidance_sources: list[Any],
) -> list[Any]:
    """Priority actions, one card each."""

    story: list[Any] = []

    priority_actions = as_list(
        analysis.priority_actions
    )

    if priority_actions:
        story.extend(
            [
                PageBreak(),
                section_heading("Priority actions", styles),
            ]
        )

        for action in priority_actions:
            action_data = as_dict(action)

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
            evidence = as_list(
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
                                    f"{html_text(priority)}: "
                                    f"{html_text(title)}</b>"
                                ),
                                styles["subsection"],
                            ),
                            tier_chip(
                                str(urgency),
                                styles,
                                width=28 * mm,
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
                                WHITE,
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
                        f"{html_text(related_domain)}"
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
                    bullet_items(
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
                            f"{html_text(source_relevance)}"
                        ),
                        styles["small"],
                    )
                )

            action_sources = source_chips(
                source_titles(
                    action_data.get("source_ids"),
                    guidance_sources,
                ),
                styles,
            )

            if action_sources is not None:
                action_story.extend(
                    [
                        Spacer(1, 1.5 * mm),
                        action_sources,
                    ]
                )

            story.extend(
                [
                    KeepTogether(action_story),
                    Spacer(1, 6 * mm),
                ]
            )

    return story


def roadmap_section(
    analysis: AIAnalysis | None,
    styles: dict[str, ParagraphStyle],
    guidance_sources: list[Any],
) -> list[Any]:
    """Improvement roadmap by time frame."""

    story: list[Any] = []

    roadmap = as_list(
        analysis.roadmap
    )

    if roadmap:
        story.extend(
            [
                PageBreak(),
                section_heading("Improvement roadmap", styles),
            ]
        )

        for index, roadmap_item in enumerate(
            roadmap,
            start=1,
        ):
            item = as_dict(
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
            actions = as_list(
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
                                    f"<b>{html_text(timeframe)}</b><br/>"
                                    f"{html_text(objective)}"
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
                    bullet_items(
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
                                    f"{html_text(success_indicator)}"
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

            roadmap_sources = source_chips(
                source_titles(
                    item.get("source_ids"),
                    guidance_sources,
                ),
                styles,
            )

            if roadmap_sources is not None:
                roadmap_story.extend(
                    [
                        Spacer(1, 1.5 * mm),
                        roadmap_sources,
                    ]
                )

            story.extend(
                [
                    KeepTogether(roadmap_story),
                    Spacer(1, 6 * mm),
                ]
            )

    return story
