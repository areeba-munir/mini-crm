from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
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
    from app.models.lead import Lead
    from app.models.user import User


class TaskStatus(str, Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Task(Base):
    __tablename__ = "tasks"

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
            ) <= 1
            """,
            name="ck_tasks_at_most_one_related_entity",
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

    status: Mapped[TaskStatus] = mapped_column(
        SqlEnum(
            TaskStatus,
            name="task_status",
            values_callable=lambda statuses: [
                status.value for status in statuses
            ],
        ),
        nullable=False,
        default=TaskStatus.PENDING,
        server_default=TaskStatus.PENDING.value,
        index=True,
    )

    priority: Mapped[TaskPriority] = mapped_column(
        SqlEnum(
            TaskPriority,
            name="task_priority",
            values_callable=lambda priorities: [
                priority.value for priority in priorities
            ],
        ),
        nullable=False,
        default=TaskPriority.MEDIUM,
        server_default=TaskPriority.MEDIUM.value,
        index=True,
    )

    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    assigned_to_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    created_by_id: Mapped[int] = mapped_column(
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

    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "contacts.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    lead_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "leads.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    completed_at: Mapped[datetime | None] = (
        mapped_column(
            DateTime(timezone=True),
            nullable=True,
        )
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

    assigned_to: Mapped["User"] = relationship(
        back_populates="assigned_tasks",
        foreign_keys=[assigned_to_id],
    )

    created_by: Mapped["User"] = relationship(
        back_populates="created_tasks",
        foreign_keys=[created_by_id],
    )

    company: Mapped["Company | None"] = relationship(
        back_populates="tasks"
    )

    contact: Mapped["Contact | None"] = relationship(
        back_populates="tasks"
    )

    lead: Mapped["Lead | None"] = relationship(
        back_populates="tasks"
    )