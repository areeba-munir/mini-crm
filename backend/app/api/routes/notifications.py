from collections.abc import Sequence
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.crud.notification import (
    count_unread_notifications,
    list_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    NotificationRead,
    NotificationUnreadCount,
)


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get(
    "",
    response_model=list[NotificationRead],
)
def get_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    unread_only: Annotated[
        bool,
        Query(),
    ] = False,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=200),
    ] = 100,
) -> Sequence[Notification]:
    return list_notifications(
        db,
        recipient_id=current_user.id,
        unread_only=unread_only,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/unread-count",
    response_model=NotificationUnreadCount,
)
def get_notification_unread_count(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> NotificationUnreadCount:
    return NotificationUnreadCount(
        unread_count=count_unread_notifications(
            db,
            recipient_id=current_user.id,
        ),
    )


@router.patch(
    "/read-all",
    response_model=NotificationUnreadCount,
)
def read_all_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> NotificationUnreadCount:
    mark_all_notifications_read(
        db,
        recipient_id=current_user.id,
    )

    return NotificationUnreadCount(
        unread_count=count_unread_notifications(
            db,
            recipient_id=current_user.id,
        ),
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationRead,
)
def read_notification(
    notification_id: Annotated[
        int,
        Path(ge=1),
    ],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> Notification:
    notification = mark_notification_read(
        db,
        notification_id=notification_id,
        recipient_id=current_user.id,
    )

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return notification