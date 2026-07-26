from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.assessment_question import AssessmentQuestion
    from app.models.survey_submission import SurveySubmission


class IndividualResponse(Base):
    __tablename__ = "individual_response"

    __table_args__ = (
        UniqueConstraint(
            "submission_id",
            "assessment_question_id",
            name="uq_individual_response_submission_question",
        ),
        CheckConstraint(
            (
                "response_option IN "
                "('Strongly Agree', 'Agree', "
                "'Neither Agree nor Disagree', "
                "'Disagree', 'Strongly Disagree', 'N/A')"
            ),
            name="ck_individual_response_option",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    submission_id: Mapped[int] = mapped_column(
        ForeignKey(
            "survey_submission.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    assessment_question_id: Mapped[int] = mapped_column(
        ForeignKey(
            "assessment_question.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    response_option: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    submission: Mapped["SurveySubmission"] = relationship(
        back_populates="responses",
    )

    assessment_question: Mapped["AssessmentQuestion"] = relationship()