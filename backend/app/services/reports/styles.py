from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


PAGE_WIDTH, PAGE_HEIGHT = A4

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
GREEN_100 = colors.HexColor("#D1FAE5")
VIOLET_700 = colors.HexColor("#6D28D9")
VIOLET_300 = colors.HexColor("#C4B5FD")
VIOLET_100 = colors.HexColor("#EDE9FE")
VIOLET_50 = colors.HexColor("#F5F3FF")
SLATE_50 = colors.HexColor("#F8FAFC")


def build_styles() -> dict[str, ParagraphStyle]:
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
