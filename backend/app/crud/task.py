from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import (
    Notification,
    NotificationType,
)
from app.models.task import (
    Task,
    TaskPriority,
    TaskStatus,
)
from app.schemas.task import TaskCreate, TaskUpdate


def _add_assignment_notification(
    db: Session,
    task: Task,
) -> None:
    """Queue a notification without committing separately."""
    notification = Notification(
        recipient_id=task.assigned_to_id,
        notification_type=NotificationType.TASK_ASSIGNED,
        title="Task assigned",
        message=(
            f"You have been assigned task "
            f"#{task.id}: {task.title}"
        ),
        link="/tasks",
    )

    db.add(notification)


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
        # Obtain the task ID without committing.
        db.flush()

        _add_assignment_notification(
            db,
            task,
        )

        # Save the task and notification together.
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(task)
    return task


def list_tasks(
    db: Session,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    assigned_to_id: int | None = None,
) -> Sequence[Task]:
    statement = select(Task)

    if status is not None:
        statement = statement.where(
            Task.status == status
        )

    if priority is not None:
        statement = statement.where(
            Task.priority == priority
        )

    if assigned_to_id is not None:
        statement = statement.where(
            Task.assigned_to_id == assigned_to_id
        )

    statement = statement.order_by(
        Task.due_at.asc().nulls_last(),
        Task.id.desc(),
    )

    return db.scalars(statement).all()


def get_task(
    db: Session,
    task_id: int,
) -> Task | None:
    return db.get(Task, task_id)


def update_task(
    db: Session,
    task: Task,
    task_data: TaskUpdate,
) -> Task:
    update_data = task_data.model_dump(
        exclude_unset=True
    )

    previous_assigned_to_id = task.assigned_to_id
    previous_status = task.status

    new_status = update_data.get(
        "status",
        previous_status,
    )

    if (
        previous_status != TaskStatus.COMPLETED
        and new_status == TaskStatus.COMPLETED
    ):
        update_data["completed_at"] = (
            datetime.now(timezone.utc)
        )

    if (
        previous_status == TaskStatus.COMPLETED
        and new_status != TaskStatus.COMPLETED
    ):
        update_data["completed_at"] = None

    for field, value in update_data.items():
        setattr(task, field, value)

    try:
        if (
            task.assigned_to_id
            != previous_assigned_to_id
        ):
            _add_assignment_notification(
                db,
                task,
            )

        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(task)
    return task


def delete_task(
    db: Session,
    task: Task,
) -> None:
    db.delete(task)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise