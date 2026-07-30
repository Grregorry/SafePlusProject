"""add organisation category

Revision ID: e0864d5eb81c
Revises: 21fd707243b6
Create Date: 2026-07-30 12:57:15.113295
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e0864d5eb81c"
down_revision: Union[
    str,
    Sequence[str],
    None,
] = "21fd707243b6"
branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None
depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


def upgrade() -> None:
    op.add_column(
        "organisation",
        sa.Column(
            "category",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE organisation
        SET category = 'Other'
        WHERE category IS NULL
        """
    )

    op.alter_column(
        "organisation",
        "category",
        existing_type=sa.String(
            length=100
        ),
        nullable=False,
        server_default="Other",
    )

    op.create_check_constraint(
        "ck_organisation_category",
        "organisation",
        (
            "category IN ("
            "'Construction', "
            "'Mining and quarrying', "
            "'Manufacturing', "
            "'Healthcare', "
            "'Transport and logistics', "
            "'Agriculture', "
            "'Retail', "
            "'Hospitality', "
            "'Professional services', "
            "'Other'"
            ")"
        ),
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_organisation_category",
        "organisation",
        type_="check",
    )

    op.drop_column(
        "organisation",
        "category",
    )