from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
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
    from app.models.user import User


meeting_user_participants = Table(
    "meeting_user_participants",
    Base.metadata,
    Column(
        "meeting_id",
        ForeignKey(
            "meetings.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    Column(
        "user_id",
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    Index(
        "ix_meeting_user_participants_user_id",
        "user_id",
    ),
)


meeting_contact_participants = Table(
    "meeting_contact_participants",
    Base.metadata,
    Column(
        "meeting_id",
        ForeignKey(
            "meetings.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    Column(
        "contact_id",
        ForeignKey(
            "contacts.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    Index(
        "ix_meeting_contact_participants_contact_id",
        "contact_id",
    ),
)


class MeetingStatus(str, Enum):
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class Meeting(Base):
    __tablename__ = "meetings"

    __table_args__ = (
        CheckConstraint(
            "ends_at > starts_at",
            name="ck_meetings_end_after_start",
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

    description: Mapped[str | None] = mapped_column(
        Text(),
        nullable=True,
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    meeting_link: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text(),
        nullable=True,
    )

    status: Mapped[MeetingStatus] = mapped_column(
        SqlEnum(
            MeetingStatus,
            name="meeting_status",
            values_callable=lambda statuses: [
                status.value for status in statuses
            ],
        ),
        nullable=False,
        default=MeetingStatus.SCHEDULED,
        server_default=MeetingStatus.SCHEDULED.value,
        index=True,
    )

    organizer_id: Mapped[int] = mapped_column(
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
            ondelete="SET NULL",
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

    organizer: Mapped["User"] = relationship(
        back_populates="organized_meetings",
        foreign_keys=[organizer_id],
    )

    company: Mapped["Company | None"] = relationship(
        back_populates="meetings"
    )

    user_participants: Mapped[list["User"]] = relationship(
        secondary=meeting_user_participants,
        back_populates="participating_meetings",
        passive_deletes=True,
    )

    contact_participants: Mapped[list["Contact"]] = (
        relationship(
            secondary=meeting_contact_participants,
            back_populates="participating_meetings",
            passive_deletes=True,
        )
    )