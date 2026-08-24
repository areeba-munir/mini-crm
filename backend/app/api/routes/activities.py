from collections.abc import Sequence
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_manager,
)
from app.crud.activity_log import (
    list_activity_logs as list_activity_records,
)
from app.db.session import get_db
from app.models.activity_log import (
    ActivityAction,
    ActivityLog,
)
from app.schemas.activity_log import (
    ActivityLogRead,
)


router = APIRouter(
    prefix="/activities",
    tags=["Activity Logs"],
)


@router.get(
    "",
    response_model=list[ActivityLogRead],
)
def get_activity_logs(
    db: Annotated[Session, Depends(get_db)],
    current_manager: Annotated[
        object,
        Depends(get_current_manager),
    ],
    action: Annotated[
        ActivityAction | None,
        Query(),
    ] = None,
    entity_type: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=50,
        ),
    ] = None,
    actor_id: Annotated[
        int | None,
        Query(ge=1),
    ] = None,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=200),
    ] = 100,
) -> Sequence[ActivityLog]:
    del current_manager

    return list_activity_records(
        db,
        action=action,
        entity_type=entity_type,
        actor_id=actor_id,
        offset=offset,
        limit=limit,
    )