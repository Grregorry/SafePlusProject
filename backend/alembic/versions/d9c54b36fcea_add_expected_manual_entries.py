"""add expected manual entries to assessment

Revision ID: d9c54b36fcea
Revises: ede183e91f4e
Create Date: 2026-08-03
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d9c54b36fcea"
down_revision: str | None = "ede183e91f4e"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "assessment",
        sa.Column(
            "expected_manual_entries",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.create_check_constraint(
        "ck_assessment_expected_manual_entries",
        "assessment",
        "expected_manual_entries >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_assessment_expected_manual_entries",
        "assessment",
        type_="check",
    )

    op.drop_column(
        "assessment",
        "expected_manual_entries",
    )
