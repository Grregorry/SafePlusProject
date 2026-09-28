from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from html import escape


def score_text(value: Decimal | float | int | str | None) -> str:
    if value is None:
        return "Not available"

    try:
        return f"{Decimal(str(value)):.2f}"
    except Exception:
        return str(value)


def date_text(value: datetime | None) -> str:
    if value is None:
        return "Not available"

    return value.astimezone().strftime(
        "%d %B %Y, %I:%M %p"
    )


def html_text(value: object) -> str:
    if value is None:
        return ""

    return escape(str(value))


def as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value

    return []


def as_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value

    return {}
