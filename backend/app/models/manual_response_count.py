from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.assessment_question import AssessmentQuestion


class ManualResponseCount(Base):
    __tablename__ = "manual_response_count"

    __table_args__ = (
        UniqueConstraint(
            "assessment_question_id",
            "respondent_group",
            "response_option",
            name="uq_manual_response_count_group_option",
        ),
        CheckConstraint(
            "respondent_group IN ('Employee', 'Senior Manager')",
            name="ck_manual_response_count_respondent_group",
        ),
        CheckConstraint(
        (
        "response_option IN "
        "('Strongly Agree', 'Agree', "
        "'Neither Agree nor Disagree', "
        "'Disagree', 'Strongly Disagree', 'N/A')"
        ),
            name="ck_manual_response_count_option",
        ),
        CheckConstraint(
            "count >= 0",
            name="ck_manual_response_count_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    assessment_question_id: Mapped[int] = mapped_column(
        ForeignKey(
            "assessment_question.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    respondent_group: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    response_option: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    assessment_question: Mapped["AssessmentQuestion"] = relationship(
        back_populates="manual_response_counts",
    )
