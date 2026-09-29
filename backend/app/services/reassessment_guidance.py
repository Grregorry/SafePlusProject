from __future__ import annotations

from decimal import Decimal


def get_reassessment_timeframe(
    overall_maturity_label: str | None,
) -> str:
    """FR25(1): rule-based re-assessment timeframe."""

    if overall_maturity_label == "Developing":
        return "6 months"

    return "12 months"


def get_largest_improvement_opportunity(
    domain_rows: list[tuple[str, Decimal, str]],
) -> tuple[str, Decimal, str] | None:
    """FR25(2): domain with the lowest Combined mean score."""

    if not domain_rows:
        return None

    return min(
        domain_rows,
        key=lambda row: row[1],
    )


def describe_meaningful_improvement(
    domain_name: str,
    combined_mean: Decimal,
    maturity_level: str,
) -> str:
    """FR25(3): what a meaningful improvement would look like."""

    current = f"{combined_mean:.2f}"

    if maturity_level == "Developing":
        return (
            f"{domain_name} is currently at {current} "
            f"(Developing). Moving above 2.50 would shift this "
            f"domain from Developing to Performing."
        )

    if maturity_level == "Performing":
        return (
            f"{domain_name} is currently at {current} "
            f"(Performing). Reaching 4.50 or above would shift "
            f"this domain from Performing to Leading."
        )

    return (
        f"{domain_name} is currently at {current} (Leading). "
        f"Maintaining current practice sustains this level."
    )


def build_reassessment_guidance(
    overall_maturity_label: str | None,
    domain_rows: list[tuple[str, Decimal, str]],
) -> dict[str, object]:
    timeframe = get_reassessment_timeframe(
        overall_maturity_label
    )

    lowest_domain = (
        get_largest_improvement_opportunity(
            domain_rows
        )
    )

    if lowest_domain is None:
        improvement_description = (
            "No domain scores are available yet to identify "
            "the largest improvement opportunity."
        )
        largest_opportunity_domain = None
    else:
        domain_name, combined_mean, maturity_level = (
            lowest_domain
        )

        largest_opportunity_domain = domain_name

        improvement_description = (
            describe_meaningful_improvement(
                domain_name,
                combined_mean,
                maturity_level,
            )
        )

    return {
        "recommended_timeframe": timeframe,
        "largest_opportunity_domain": (
            largest_opportunity_domain
        ),
        "improvement_description": (
            improvement_description
        ),
    }
