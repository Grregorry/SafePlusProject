"""add assessment names and organisation numbering

Revision ID: 21fd707243b6
Revises: b7c4d9e2a1f0
Create Date: 2026-07-30 12:39:14.907614
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "21fd707243b6"
down_revision: Union[
    str,
    Sequence[str],
    None,
] = "b7c4d9e2a1f0"
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
        "assessment",
        sa.Column(
            "organisation_assessment_number",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "assessment",
        sa.Column(
            "name",
            sa.String(length=150),
            nullable=True,
        ),
    )

    op.execute(
        """
        WITH numbered_assessments AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY organisation_id
                    ORDER BY created_at, id
                ) AS organisation_number
            FROM assessment
        )
        UPDATE assessment
        SET
            organisation_assessment_number =
                numbered_assessments.organisation_number,
            name =
                'Assessment '
                || numbered_assessments.organisation_number
        FROM numbered_assessments
        WHERE
            assessment.id =
            numbered_assessments.id
        """
    )

    op.alter_column(
        "assessment",
        "organisation_assessment_number",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "assessment",
        "name",
        existing_type=sa.String(
            length=150
        ),
        nullable=False,
    )

    op.create_check_constraint(
        "ck_assessment_organisation_number",
        "assessment",
        (
            "organisation_assessment_number "
            ">= 1"
        ),
    )

    op.create_unique_constraint(
        "uq_assessment_organisation_number",
        "assessment",
        [
            "organisation_id",
            "organisation_assessment_number",
        ],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_assessment_organisation_number",
        "assessment",
        type_="unique",
    )

    op.drop_constraint(
        "ck_assessment_organisation_number",
        "assessment",
        type_="check",
    )

    op.drop_column(
        "assessment",
        "name",
    )

    op.drop_column(
        "assessment",
        "organisation_assessment_number",
    )