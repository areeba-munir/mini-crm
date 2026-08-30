from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.notification import Notification


def list_notifications(
    db: Session,
    *,
    recipient_id: int,
    unread_only: bool = False,
    offset: int = 0,
    limit: int = 100,
) -> Sequence[Notification]:
    statement = select(Notification).where(
        Notification.recipient_id == recipient_id,
    )

    if unread_only:
        statement = statement.where(
            Notification.is_read.is_(False),
        )

    statement = (
        statement
        .order_by(
            Notification.created_at.desc(),
            Notification.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(statement).all()


def count_unread_notifications(
    db: Session,
    *,
    recipient_id: int,
) -> int:
    statement = (
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.recipient_id == recipient_id,
            Notification.is_read.is_(False),
        )
    )

    return db.scalar(statement) or 0


def mark_notification_read(
    db: Session,
    *,
    notification_id: int,
    recipient_id: int,
) -> Notification | None:
    statement = (
        update(Notification)
        .where(
            Notification.id == notification_id,
            Notification.recipient_id == recipient_id,
            Notification.is_read.is_(False),
        )
        .values(
            is_read=True,
            read_at=datetime.now(timezone.utc),
        )
    )

    db.execute(statement)
    db.commit()

    return db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.recipient_id == recipient_id,
        )
    )


def mark_all_notifications_read(
    db: Session,
    *,
    recipient_id: int,
) -> None:
    statement = (
        update(Notification)
        .where(
            Notification.recipient_id == recipient_id,
            Notification.is_read.is_(False),
        )
        .values(
            is_read=True,
            read_at=datetime.now(timezone.utc),
        )
    )

    db.execute(statement)
    db.commit()