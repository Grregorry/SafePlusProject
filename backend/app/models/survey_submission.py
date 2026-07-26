from __future__ import annotations

import secrets
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.assessment import Assessment
    from app.models.individual_response import IndividualResponse


def generate_submission_token() -> str:
    return secrets.token_urlsafe(32)


class SurveySubmission(Base):
    __tablename__ = "survey_submission"

    __table_args__ = (
        CheckConstraint(
            "respondent_group IN ('Employee', 'Senior Manager')",
            name="ck_survey_submission_respondent_group",
        ),
        CheckConstraint(
            "status IN ('in_progress', 'submitted')",
            name="ck_survey_submission_status",
        ),
        CheckConstraint(
            "submitted_at IS NULL OR submitted_at >= started_at",
            name="ck_survey_submission_time",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    assessment_id: Mapped[int] = mapped_column(
        ForeignKey(
            "assessment.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    access_token: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        default=generate_submission_token,
    )

    respondent_group: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="in_progress",
        server_default="in_progress",
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    assessment: Mapped["Assessment"] = relationship(
        back_populates="survey_submissions",
    )

    responses: Mapped[list["IndividualResponse"]] = relationship(
        back_populates="submission",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )