"""add respondent survey foundation

Revision ID: b7c4d9e2a1f0
Revises: 0964f8c2bbbb
Create Date: 2026-07-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b7c4d9e2a1f0"
down_revision: str | None = "0964f8c2bbbb"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "assessment",
        sa.Column(
            "public_code",
            sa.String(length=16),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE assessment
        SET public_code =
            'SP-' ||
            UPPER(
                SUBSTRING(
                    MD5(
                        RANDOM()::TEXT ||
                        id::TEXT ||
                        CLOCK_TIMESTAMP()::TEXT
                    ),
                    1,
                    8
                )
            )
        WHERE public_code IS NULL
        """
    )

    op.alter_column(
        "assessment",
        "public_code",
        existing_type=sa.String(length=16),
        nullable=False,
    )

    op.create_unique_constraint(
        "uq_assessment_public_code",
        "assessment",
        ["public_code"],
    )

    op.create_table(
        "survey_submission",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "assessment_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "access_token",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "respondent_group",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="in_progress",
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.CheckConstraint(
            (
                "respondent_group IN "
                "('Employee', 'Senior Manager')"
            ),
            name="ck_survey_submission_respondent_group",
        ),
        sa.CheckConstraint(
            (
                "status IN "
                "('in_progress', 'submitted')"
            ),
            name="ck_survey_submission_status",
        ),
        sa.CheckConstraint(
            (
                "submitted_at IS NULL OR "
                "submitted_at >= started_at"
            ),
            name="ck_survey_submission_time",
        ),
        sa.ForeignKeyConstraint(
            ["assessment_id"],
            ["assessment.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "access_token",
            name="uq_survey_submission_access_token",
        ),
    )

    op.create_table(
        "individual_response",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "submission_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "assessment_question_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "response_option",
            sa.String(length=40),
            nullable=False,
        ),
        sa.CheckConstraint(
            (
                "response_option IN "
                "('Strongly Agree', 'Agree', "
                "'Neither Agree nor Disagree', "
                "'Disagree', 'Strongly Disagree', 'N/A')"
            ),
            name="ck_individual_response_option",
        ),
        sa.ForeignKeyConstraint(
            ["assessment_question_id"],
            ["assessment_question.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["submission_id"],
            ["survey_submission.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "submission_id",
            "assessment_question_id",
            name=(
                "uq_individual_response_submission_question"
            ),
        ),
    )


def downgrade() -> None:
    op.drop_table("individual_response")
    op.drop_table("survey_submission")

    op.drop_constraint(
        "uq_assessment_public_code",
        "assessment",
        type_="unique",
    )

    op.drop_column(
        "assessment",
        "public_code",
    )