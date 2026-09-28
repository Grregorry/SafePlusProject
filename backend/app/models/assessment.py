from __future__ import annotations

import secrets
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.ai_analysis import AIAnalysis
    from app.models.assessment_question import (
        AssessmentQuestion,
    )
    from app.models.domain_score import DomainScore
    from app.models.organisation import Organisation
    from app.models.survey_submission import (
        SurveySubmission,
    )


PUBLIC_CODE_CHARACTERS = (
    "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
)


def generate_public_code() -> str:
    random_part = "".join(
        secrets.choice(
            PUBLIC_CODE_CHARACTERS
        )
        for _ in range(8)
    )

    return f"SP-{random_part}"


class Assessment(Base):
    __tablename__ = "assessment"

    __table_args__ = (
        UniqueConstraint(
            "organisation_id",
            "organisation_assessment_number",
            name=(
                "uq_assessment_organisation_number"
            ),
        ),
        CheckConstraint(
            (
                "organisation_assessment_number "
                ">= 1"
            ),
            name=(
                "ck_assessment_organisation_number"
            ),
        ),
        CheckConstraint(
            (
                "status IN "
                "('draft', 'in_progress', "
                "'completed')"
            ),
            name="ck_assessment_status",
        ),
        CheckConstraint(
            (
                "overall_combined_mean IS NULL "
                "OR overall_combined_mean "
                "BETWEEN 1.00 AND 5.00"
            ),
            name=(
                "ck_assessment_overall_mean"
            ),
        ),
        CheckConstraint(
            (
                "overall_maturity_label IS NULL "
                "OR overall_maturity_label IN "
                "('Developing', 'Performing', "
                "'Leading')"
            ),
            name=(
                "ck_assessment_maturity_label"
            ),
        ),
        CheckConstraint(
            (
                "completed_at IS NULL "
                "OR completed_at >= created_at"
            ),
            name=(
                "ck_assessment_completion_time"
            ),
        ),
        CheckConstraint(
            "expected_manual_entries_employee >= 0",
            name=(
                "ck_assessment_expected_manual_entries_employee"
            ),
        ),
        CheckConstraint(
            "expected_manual_entries_manager >= 0",
            name=(
                "ck_assessment_expected_manual_entries_manager"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    organisation_id: Mapped[int] = (
        mapped_column(
            ForeignKey(
                "organisation.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        )
    )

    organisation_assessment_number: Mapped[
        int
    ] = mapped_column(
        Integer,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    public_code: Mapped[str] = (
        mapped_column(
            String(16),
            nullable=False,
            unique=True,
            default=generate_public_code,
        )
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        server_default="draft",
    )

    created_at: Mapped[datetime] = (
        mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )

    completed_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    overall_combined_mean: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(3, 2),
        nullable=True,
    )

    overall_maturity_label: Mapped[
        str | None
    ] = mapped_column(
        String(20),
        nullable=True,
    )

    expected_manual_entries_employee: Mapped[
        int
    ] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    expected_manual_entries_manager: Mapped[
        int
    ] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    organisation: Mapped[
        "Organisation"
    ] = relationship(
        back_populates="assessments",
    )

    assessment_questions: Mapped[
        list["AssessmentQuestion"]
    ] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    domain_scores: Mapped[
        list["DomainScore"]
    ] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    ai_analysis: Mapped[
        "AIAnalysis | None"
    ] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )

    survey_submissions: Mapped[
        list["SurveySubmission"]
    ] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )