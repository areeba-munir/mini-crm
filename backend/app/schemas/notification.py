from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationType


class NotificationRead(BaseModel):
    id: int
    recipient_id: int
    notification_type: NotificationType
    title: str
    message: str
    link: str | None
    is_read: bool
    read_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class NotificationUnreadCount(BaseModel):
    unread_count: int