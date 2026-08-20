from datetime import datetime
from typing import TYPE_CHECKING
from app.models.lead import Lead
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


if TYPE_CHECKING:
    from app.models.contact import Contact


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    industry: Mapped[str | None] = mapped_column(
        String(100)
    )

    website: Mapped[str | None] = mapped_column(
        String(500)
    )

    email: Mapped[str | None] = mapped_column(
        String(255)
    )

    phone: Mapped[str | None] = mapped_column(
        String(50)
    )

    address: Mapped[str | None] = mapped_column(
        Text
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    contacts: Mapped[list["Contact"]] = relationship(
        "Contact",
        back_populates="company",
        passive_deletes=True,
    )
    leads: Mapped[list["Lead"]] = relationship(
    back_populates="company",
    passive_deletes=True,
    )