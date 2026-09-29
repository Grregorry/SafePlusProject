"""Report generation entry point.

The reports live in app.services.reports; this module keeps the original
import path working.
"""

from app.services.reports import (
    generate_assessment_report,
    generate_board_report,
    generate_business_leader_report,
    generate_operational_manager_report,
)

__all__ = [
    "generate_assessment_report",
    "generate_board_report",
    "generate_business_leader_report",
    "generate_operational_manager_report",
]
