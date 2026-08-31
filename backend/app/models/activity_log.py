from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    JSON,
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
    from app.models.user import User


class ActivityAction(str, Enum):
    CREATED = "Created"
    UPDATED = "Updated"
    DELETED = "Deleted"


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    __table_args__ = (
        Index(
            "ix_activity_logs_entity",
            "entity_type",
            "entity_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    action: Mapped[ActivityAction] = mapped_column(
        SqlEnum(
            ActivityAction,
            name="activity_action",
            values_callable=lambda actions: [
                action.value for action in actions
            ],
        ),
        nullable=False,
        index=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    entity_id: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    details: Mapped[
        dict[str, object] | None
    ] = mapped_column(
        JSON(),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    actor: Mapped["User | None"] = relationship(
        back_populates="activity_logs"
    )