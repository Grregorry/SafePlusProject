"""update response option wording

Revision ID: 0964f8c2bbbb
Revises: d1b18544226d
Create Date: 2026-07-25 23:54:37.583030

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0964f8c2bbbb'
down_revision: Union[str, Sequence[str], None] = 'd1b18544226d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_response_count_option",
        "response_count",
        type_="check",
    )

    op.alter_column(
        "response_count",
        "response_option",
        existing_type=sa.String(length=30),
        type_=sa.String(length=40),
        existing_nullable=False,
    )

    op.create_check_constraint(
        "ck_response_count_option",
        "response_count",
        """
        response_option IN (
            'Strongly Agree',
            'Agree',
            'Neither Agree nor Disagree',
            'Disagree',
            'Strongly Disagree',
            'N/A'
        )
        """,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_response_count_option",
        "response_count",
        type_="check",
    )

    op.alter_column(
        "response_count",
        "response_option",
        existing_type=sa.String(length=40),
        type_=sa.String(length=30),
        existing_nullable=False,
    )

    op.create_check_constraint(
        "ck_response_count_option",
        "response_count",
        """
        response_option IN (
            'Strongly Agree',
            'Agree',
            'Neither',
            'Disagree',
            'Strongly Disagree',
            'N/A'
        )
        """,
    )
