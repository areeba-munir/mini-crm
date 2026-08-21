from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
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
    from app.models.lead import Lead
    from app.models.user import User


class Note(Base):
    __tablename__ = "notes"

    __table_args__ = (
        CheckConstraint(
            """
            (
                CASE
                    WHEN company_id IS NULL THEN 0
                    ELSE 1
                END
                +
                CASE
                    WHEN contact_id IS NULL THEN 0
                    ELSE 1
                END
                +
                CASE
                    WHEN lead_id IS NULL THEN 0
                    ELSE 1
                END
            ) = 1
            """,
            name="ck_notes_exactly_one_related_entity",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    body: Mapped[str] = mapped_column(
        Text(),
        nullable=False,
    )

    author_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    company_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "companies.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "contacts.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    lead_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "leads.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
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

    author: Mapped["User"] = relationship(
        back_populates="notes"
    )

    company: Mapped["Company | None"] = relationship(
        back_populates="notes"
    )

    contact: Mapped["Contact | None"] = relationship(
        back_populates="notes"
    )

    lead: Mapped["Lead | None"] = relationship(
        back_populates="notes"
    )