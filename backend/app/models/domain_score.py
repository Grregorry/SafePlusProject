from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.assessment import Assessment
    from app.models.domain import Domain


class DomainScore(Base):
    __tablename__ = "domain_score"

    __table_args__ = (
        UniqueConstraint(
            "assessment_id",
            "domain_id",
            name="uq_domain_score_assessment_domain",
        ),
        CheckConstraint(
            "combined_mean BETWEEN 1.00 AND 5.00",
            name="ck_domain_score_combined_mean",
        ),
        CheckConstraint(
            "maturity_level IN ('Developing', 'Performing', 'Leading')",
            name="ck_domain_score_maturity",
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

    domain_id: Mapped[int] = mapped_column(
        ForeignKey(
            "domain.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    combined_mean: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
    )

    maturity_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    assessment: Mapped["Assessment"] = relationship(
        back_populates="domain_scores",
    )

    domain: Mapped["Domain"] = relationship(
        back_populates="domain_scores",
    )