from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    String,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.assessment import Assessment


ORGANISATION_CATEGORIES = (
    "Construction",
    "Mining and quarrying",
    "Manufacturing",
    "Healthcare",
    "Transport and logistics",
    "Agriculture",
    "Retail",
    "Hospitality",
    "Professional services",
    "Other",
)


class Organisation(Base):
    __tablename__ = "organisation"

    __table_args__ = (
        CheckConstraint(
            (
                "category IN ("
                "'Construction', "
                "'Mining and quarrying', "
                "'Manufacturing', "
                "'Healthcare', "
                "'Transport and logistics', "
                "'Agriculture', "
                "'Retail', "
                "'Hospitality', "
                "'Professional services', "
                "'Other'"
                ")"
            ),
            name="ck_organisation_category",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Other",
        server_default="Other",
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    verification_token: Mapped[
        str | None
    ] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    verification_expires_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    assessments: Mapped[
        list["Assessment"]
    ] = relationship(
        back_populates="organisation",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )