from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.assessment import Assessment
    from app.models.question import Question
    from app.models.question_score import QuestionScore
    from app.models.response_count import ResponseCount


class AssessmentQuestion(Base):
    __tablename__ = "assessment_question"

    __table_args__ = (
        UniqueConstraint(
            "assessment_id",
            "question_id",
            name="uq_assessment_question",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    assessment_id: Mapped[int] = mapped_column(
        ForeignKey(
            "assessment.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey(
            "question.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    assessment: Mapped["Assessment"] = relationship(
        back_populates="assessment_questions",
    )

    question: Mapped["Question"] = relationship(
        back_populates="assessment_questions",
    )

    response_counts: Mapped[list["ResponseCount"]] = relationship(
        back_populates="assessment_question",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    question_score: Mapped["QuestionScore | None"] = relationship(
        back_populates="assessment_question",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )