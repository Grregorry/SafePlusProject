"""split expected manual entries by respondent group

Revision ID: 0bb22dc74ab3
Revises: d9c54b36fcea
Create Date: 2026-08-03
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0bb22dc74ab3"
down_revision: str | None = "d9c54b36fcea"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_assessment_expected_manual_entries",
        "assessment",
        type_="check",
    )

    op.alter_column(
        "assessment",
        "expected_manual_entries",
        new_column_name="expected_manual_entries_employee",
    )

    op.add_column(
        "assessment",
        sa.Column(
            "expected_manual_entries_manager",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.create_check_constraint(
        "ck_assessment_expected_manual_entries_employee",
        "assessment",
        "expected_manual_entries_employee >= 0",
    )

    op.create_check_constraint(
        "ck_assessment_expected_manual_entries_manager",
        "assessment",
        "expected_manual_entries_manager >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_assessment_expected_manual_entries_manager",
        "assessment",
        type_="check",
    )

    op.drop_constraint(
        "ck_assessment_expected_manual_entries_employee",
        "assessment",
        type_="check",
    )

    op.drop_column(
        "assessment",
        "expected_manual_entries_manager",
    )

    op.alter_column(
        "assessment",
        "expected_manual_entries_employee",
        new_column_name="expected_manual_entries",
    )

    op.create_check_constraint(
        "ck_assessment_expected_manual_entries",
        "assessment",
        "expected_manual_entries >= 0",
    )
