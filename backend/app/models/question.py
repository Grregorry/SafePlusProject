from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.domain import Domain
    from app.models.assessment_question import AssessmentQuestion


class Question(Base):
    __tablename__ = "question"

    __table_args__ = (
        UniqueConstraint(
            "domain_id",
            "question_number",
            name="uq_question_domain_number",
        ),
        CheckConstraint(
            "is_compulsory <> is_situation_dependent",
            name="ck_question_exactly_one_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    domain_id: Mapped[int] = mapped_column(
        ForeignKey(
            "domain.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    question_number: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    employee_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    manager_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_compulsory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    is_situation_dependent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    domain: Mapped["Domain"] = relationship(
        back_populates="questions",
    )

    assessment_questions: Mapped[list["AssessmentQuestion"]] = relationship(
        back_populates="question",
    )