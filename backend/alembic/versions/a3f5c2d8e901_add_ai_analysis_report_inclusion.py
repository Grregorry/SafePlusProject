"""add ai analysis report inclusion flag

Revision ID: a3f5c2d8e901
Revises: 0bb22dc74ab3
Create Date: 2026-09-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a3f5c2d8e901"
down_revision: str | None = "0bb22dc74ab3"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Existing analyses start excluded: AI text only reaches a report
    # after a person has reviewed and included it.
    op.add_column(
        "ai_analysis",
        sa.Column(
            "included_in_report",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "ai_analysis",
        "included_in_report",
    )
