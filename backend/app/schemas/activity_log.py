from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.activity_log import ActivityAction
from app.models.user import UserRole


class ActivityActorRead(BaseModel):
    id: int
    full_name: str
    email: str
    role: UserRole

    model_config = ConfigDict(
        from_attributes=True
    )


class ActivityLogRead(BaseModel):
    id: int
    actor_id: int | None
    actor: ActivityActorRead | None
    action: ActivityAction
    entity_type: str
    entity_id: int | None
    description: str
    details: dict[str, object] | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )