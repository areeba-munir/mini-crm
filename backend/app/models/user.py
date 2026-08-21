from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    String,
    func,
    true,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.meeting import Meeting
    from app.models.note import Note


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=True,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=true(),
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

    assigned_tasks: Mapped[list["Task"]] = relationship(
        back_populates="assigned_to",
        foreign_keys="Task.assigned_to_id",
        passive_deletes=True,
    )

    created_tasks: Mapped[list["Task"]] = relationship(
        back_populates="created_by",
        foreign_keys="Task.created_by_id",
        passive_deletes=True,
    )
    organized_meetings: Mapped[list["Meeting"]] = relationship(
    back_populates="organizer",
    foreign_keys="Meeting.organizer_id",
    passive_deletes=True,
    )
    participating_meetings: Mapped[list["Meeting"]] = (
    relationship(
        secondary="meeting_user_participants",
        back_populates="user_participants",
        passive_deletes=True,
    )
    )
    notes: Mapped[list["Note"]] = relationship(
    back_populates="author",
    passive_deletes=True,
    )