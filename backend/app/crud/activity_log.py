from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.activity_log import (
    ActivityAction,
    ActivityLog,
)


def list_activity_logs(
    db: Session,
    *,
    action: ActivityAction | None = None,
    entity_type: str | None = None,
    actor_id: int | None = None,
    offset: int = 0,
    limit: int = 100,
) -> Sequence[ActivityLog]:
    statement = (
        select(ActivityLog)
        .options(
            joinedload(ActivityLog.actor)
        )
        .order_by(
            ActivityLog.created_at.desc(),
            ActivityLog.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    if action is not None:
        statement = statement.where(
            ActivityLog.action == action
        )

    if entity_type is not None:
        statement = statement.where(
            func.lower(
                ActivityLog.entity_type
            )
            == entity_type.strip().lower()
        )

    if actor_id is not None:
        statement = statement.where(
            ActivityLog.actor_id == actor_id
        )

    return db.scalars(statement).all()