from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.contact import Contact
    from app.models.task import Task
    from app.models.note import Note


class LeadStage(str, Enum):
    NEW = "New"
    CONTACTED = "Contacted"
    QUALIFIED = "Qualified"
    WON = "Won"
    LOST = "Lost"


class Lead(Base):
    __tablename__ = "leads"

    __table_args__ = (
        CheckConstraint(
            (
                "estimated_value IS NULL "
                "OR estimated_value >= 0"
            ),
            name="ck_leads_estimated_value_nonnegative",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey(
            "companies.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "contacts.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    stage: Mapped[LeadStage] = mapped_column(
        SqlEnum(
            LeadStage,
            name="lead_stage",
            values_callable=lambda stages: [
                stage.value for stage in stages
            ],
        ),
        nullable=False,
        default=LeadStage.NEW,
        server_default=LeadStage.NEW.value,
        index=True,
    )

    estimated_value: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(12, 2),
            nullable=True,
        )
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    expected_close_date: Mapped[date | None] = (
        mapped_column(
            Date(),
            nullable=True,
        )
    )

    description: Mapped[str | None] = mapped_column(
        Text(),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    company: Mapped["Company"] = relationship(
        back_populates="leads"
    )

    contact: Mapped["Contact | None"] = relationship(
        back_populates="leads"
    )
    tasks: Mapped[list["Task"]] = relationship(
    back_populates="lead",
    passive_deletes=True,
    )
    notes: Mapped[list["Note"]] = relationship(
    back_populates="lead",
    passive_deletes=True,
    )