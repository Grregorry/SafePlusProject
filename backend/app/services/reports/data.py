from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Assessment, Domain, DomainScore
from app.services.report_components import is_hidden, ProfilePoint


def fetch_domain_rows(
    assessment: Assessment,
    database: Session,
) -> list[tuple[str, Decimal, str]]:
    return list(
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


def profile_from_rows(
    rows: list[Any],
    number_index: int,
    domain_index: int,
    combined_index: int,
    gap_index: int,
    lowest_mean: Decimal | None,
) -> tuple[list[ProfilePoint], list[tuple[str, str, str]]]:
    """Builds the question profile points and the domain ranges used in
    the legend, from any query returning a question number, domain,
    combined mean and opinion gap."""

    points: list[ProfilePoint] = []
    ranges: list[list[str]] = []
    previous_domain: str | None = None

    for row in rows:
        domain_name = str(row[domain_index])
        number = str(row[number_index])
        starts_domain = domain_name != previous_domain
        hidden = is_hidden(row[gap_index])

        points.append(
            ProfilePoint(
                label=number,
                value=row[combined_index],
                hidden=hidden,
                lowest=(
                    lowest_mean is not None
                    and row[combined_index] is not None
                    and not hidden
                    and Decimal(str(row[combined_index])) == lowest_mean
                ),
                domain_start=starts_domain,
            )
        )

        if starts_domain:
            ranges.append([domain_name, number, number])
        else:
            ranges[-1][2] = number

        previous_domain = domain_name

    return points, [
        (item[0], item[1], item[2]) for item in ranges
    ]
