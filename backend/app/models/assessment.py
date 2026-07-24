from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.organisation import Organisation


class Assessment(Base):
    __tablename__ = "assessment"

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'in_progress', 'completed')",
            name="ck_assessment_status",
        ),
        CheckConstraint(
            (
                "overall_combined_mean IS NULL OR "
                "overall_combined_mean BETWEEN 1.00 AND 5.00"
            ),
            name="ck_assessment_overall_mean",
        ),
        CheckConstraint(
            (
                "overall_maturity_label IS NULL OR "
                "overall_maturity_label IN "
                "('Developing', 'Performing', 'Leading')"
            ),
            name="ck_assessment_maturity_label",
        ),
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= created_at",
            name="ck_assessment_completion_time",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    organisation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "organisation.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        server_default="draft",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    overall_combined_mean: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2),
        nullable=True,
    )

    overall_maturity_label: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    organisation: Mapped["Organisation"] = relationship(
        back_populates="assessments",
    )