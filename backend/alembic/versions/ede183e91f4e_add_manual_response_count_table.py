"""add manual response count table

Revision ID: ede183e91f4e
Revises: e0864d5eb81c
Create Date: 2026-08-03
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "ede183e91f4e"
down_revision: str | None = "e0864d5eb81c"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "manual_response_count",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "assessment_question_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "respondent_group",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "response_option",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column(
            "count",
            sa.Integer(),
            nullable=False,
        ),
        sa.CheckConstraint(
            (
                "respondent_group IN "
                "('Employee', 'Senior Manager')"
            ),
            name="ck_manual_response_count_respondent_group",
        ),
        sa.CheckConstraint(
            (
                "response_option IN "
                "('Strongly Agree', 'Agree', "
                "'Neither Agree nor Disagree', "
                "'Disagree', 'Strongly Disagree', 'N/A')"
            ),
            name="ck_manual_response_count_option",
        ),
        sa.CheckConstraint(
            "count >= 0",
            name="ck_manual_response_count_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["assessment_question_id"],
            ["assessment_question.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "assessment_question_id",
            "respondent_group",
            "response_option",
            name="uq_manual_response_count_group_option",
        ),
    )

    # response_count previously mixed manually-entered
    # (paper survey) counts with digital-submission counts,
    # since both write paths shared the same table and
    # silently overwrote each other. Rebuild it here purely
    # from digital submissions so it becomes reliably
    # digital-only going forward; any previously-entered
    # manual counts are not recoverable from the mixed data.
    op.execute(
        """
        DELETE FROM response_count
        """
    )

    op.execute(
        """
        INSERT INTO response_count (
            assessment_question_id,
            respondent_group,
            response_option,
            count
        )
        SELECT
            individual_response.assessment_question_id,
            survey_submission.respondent_group,
            individual_response.response_option,
            COUNT(*) AS count
        FROM individual_response
        JOIN survey_submission
            ON individual_response.submission_id
                = survey_submission.id
        WHERE survey_submission.status = 'submitted'
        GROUP BY
            individual_response.assessment_question_id,
            survey_submission.respondent_group,
            individual_response.response_option
        """
    )


def downgrade() -> None:
    op.drop_table("manual_response_count")
