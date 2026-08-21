from datetime import datetime
from typing import TYPE_CHECKING
from app.models.lead import Lead
from app.models.meeting import Meeting

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.task import Task
    from app.models.note import Note



class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    last_name: Mapped[str | None] = mapped_column(
        String(100)
    )

    email: Mapped[str | None] = mapped_column(
        String(320)
    )

    phone: Mapped[str | None] = mapped_column(
        String(50)
    )

    job_title: Mapped[str | None] = mapped_column(
        String(150)
    )

    company_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "companies.id",
            ondelete="SET NULL",
        ),
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

    company: Mapped["Company | None"] = relationship(
        "Company",
        back_populates="contacts",
    )
    leads: Mapped[list["Lead"]] = relationship(
    back_populates="contact",
    passive_deletes=True,
    )
    tasks: Mapped[list["Task"]] = relationship(
    back_populates="contact",
    passive_deletes=True,
    )
    participating_meetings: Mapped[list["Meeting"]] = (
    relationship(
        secondary="meeting_contact_participants",
        back_populates="contact_participants",
        passive_deletes=True,
    )
    )
    notes: Mapped[list["Note"]] = relationship(
    back_populates="contact",
    passive_deletes=True,
    )