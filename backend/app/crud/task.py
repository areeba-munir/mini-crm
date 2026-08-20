from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate


def create_task(
    db: Session,
    task_data: TaskCreate,
    created_by_id: int,
) -> Task:
    task_values = task_data.model_dump()

    if task_data.status == TaskStatus.COMPLETED:
        task_values["completed_at"] = (
            datetime.now(timezone.utc)
        )

    task = Task(
        **task_values,
        created_by_id=created_by_id,
    )

    db.add(task)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(task)
    return task