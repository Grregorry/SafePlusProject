from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.assessment import Assessment


class AIAnalysis(Base):
    __tablename__ = "ai_analysis"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="ck_ai_analysis_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    assessment_id: Mapped[int] = mapped_column(
        ForeignKey(
            "assessment.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    overall_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    domain_summaries: Mapped[dict[str, object] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    priority_actions: Mapped[list[dict[str, object]] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    roadmap: Mapped[list[dict[str, object]] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    ai_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
    )

    # AI text never reaches a report by default; a person has to
    # include it after reading it. Regenerating resets this.
    included_in_report: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    assessment: Mapped["Assessment"] = relationship(
        back_populates="ai_analysis",
    )