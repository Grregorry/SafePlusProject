from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.assessment_question import AssessmentQuestion


class QuestionScore(Base):
    __tablename__ = "question_score"

    __table_args__ = (
        CheckConstraint(
            "employee_mean IS NULL OR employee_mean BETWEEN 1.00 AND 5.00",
            name="ck_question_score_employee_mean",
        ),
        CheckConstraint(
            "manager_mean IS NULL OR manager_mean BETWEEN 1.00 AND 5.00",
            name="ck_question_score_manager_mean",
        ),
        CheckConstraint(
            "combined_mean BETWEEN 1.00 AND 5.00",
            name="ck_question_score_combined_mean",
        ),
        CheckConstraint(
            "opinion_gap BETWEEN 0.00 AND 4.00",
            name="ck_question_score_opinion_gap",
        ),
        CheckConstraint(
            "maturity_level IN ('Developing', 'Performing', 'Leading')",
            name="ck_question_score_maturity",
        ),
        CheckConstraint(
            "intervention_tier IN ('High', 'Medium', 'Low', 'Not flagged')",
            name="ck_question_score_intervention",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    assessment_question_id: Mapped[int] = mapped_column(
        ForeignKey(
            "assessment_question.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    employee_mean: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2),
        nullable=True,
    )

    manager_mean: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2),
        nullable=True,
    )

    combined_mean: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
    )

    opinion_gap: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
    )

    maturity_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    intervention_tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    assessment_question: Mapped["AssessmentQuestion"] = relationship(
        back_populates="question_score",
    )