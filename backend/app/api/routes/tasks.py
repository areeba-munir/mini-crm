from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.crud.company import (
    get_company as get_company_record,
)
from app.crud.contact import (
    get_contact as get_contact_record,
)
from app.crud.lead import (
    get_lead as get_lead_record,
)
from app.crud.task import (
    create_task as create_task_record,
)
from app.db.session import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead


router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
    dependencies=[
        Depends(get_current_user),
    ],
)


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    task_data: TaskCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> Task:
    assigned_user = db.get(
        User,
        task_data.assigned_to_id,
    )

    if assigned_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned user not found",
        )

    if not assigned_user.is_active:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=(
                "Cannot assign a task "
                "to an inactive user"
            ),
        )

    if (
        task_data.company_id is not None
        and get_company_record(
            db,
            task_data.company_id,
        )
        is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    if (
        task_data.contact_id is not None
        and get_contact_record(
            db,
            task_data.contact_id,
        )
        is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    if (
        task_data.lead_id is not None
        and get_lead_record(
            db,
            task_data.lead_id,
        )
        is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    return create_task_record(
        db,
        task_data,
        created_by_id=current_user.id,
    )