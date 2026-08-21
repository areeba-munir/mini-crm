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
    delete_task as delete_task_record,
    get_task as get_task_record,
    list_tasks as list_task_records,
    update_task as update_task_record,
)
from app.db.session import get_db
from app.models.task import (
    Task,
    TaskPriority,
    TaskStatus,
)
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskRead,
    TaskUpdate,
)

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
    dependencies=[
        Depends(get_current_user),
    ],
)


@router.get(
    "",
    response_model=list[TaskRead],
)
def get_tasks(
    db: Annotated[Session, Depends(get_db)],
    task_status: TaskStatus | None = Query(
        default=None,
        alias="status",
    ),
    priority: TaskPriority | None = Query(
        default=None,
    ),
    assigned_to_id: int | None = Query(
        default=None,
        ge=1,
    ),
) -> Sequence[Task]:
    return list_task_records(
        db,
        status=task_status,
        priority=priority,
        assigned_to_id=assigned_to_id,
    )


@router.get(
    "/{task_id}",
    response_model=TaskRead,
)
def get_task(
    db: Annotated[Session, Depends(get_db)],
    task_id: int = Path(ge=1),
) -> Task:
    task = get_task_record(db, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


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

@router.patch(
    "/{task_id}",
    response_model=TaskRead,
)
def update_task(
    task_data: TaskUpdate,
    db: Annotated[Session, Depends(get_db)],
    task_id: int = Path(ge=1),
) -> Task:
    task = get_task_record(db, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    if "assigned_to_id" in task_data.model_fields_set:
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

    company_id = (
        task_data.company_id
        if "company_id" in task_data.model_fields_set
        else task.company_id
    )
    contact_id = (
        task_data.contact_id
        if "contact_id" in task_data.model_fields_set
        else task.contact_id
    )
    lead_id = (
        task_data.lead_id
        if "lead_id" in task_data.model_fields_set
        else task.lead_id
    )

    related_ids = (
        company_id,
        contact_id,
        lead_id,
    )

    if sum(
        value is not None
        for value in related_ids
    ) > 1:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=(
                "A task may relate to at most one "
                "company, contact, or lead"
            ),
        )

    if (
        company_id is not None
        and get_company_record(db, company_id) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    if (
        contact_id is not None
        and get_contact_record(db, contact_id) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    if (
        lead_id is not None
        and get_lead_record(db, lead_id) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    return update_task_record(
        db,
        task,
        task_data,
    )
@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_task(
    db: Annotated[Session, Depends(get_db)],
    task_id: int = Path(ge=1),
) -> None:
    task = get_task_record(db, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    delete_task_record(db, task)