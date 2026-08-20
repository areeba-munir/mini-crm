from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.task import (
    Task,
    TaskPriority,
    TaskStatus,
)
from app.schemas.task import (
    TaskCreate,
    TaskRead,
    TaskUpdate,
)


def test_task_create_normalizes_input_and_defaults(
) -> None:
    task = TaskCreate(
        title="  Call customer  ",
        assigned_to_id=1,
    )

    assert task.title == "Call customer"
    assert task.status == TaskStatus.PENDING
    assert task.priority == TaskPriority.MEDIUM


def test_task_create_rejects_blank_title() -> None:
    with pytest.raises(ValidationError):
        TaskCreate(
            title="   ",
            assigned_to_id=1,
        )


def test_task_create_rejects_multiple_related_entities(
) -> None:
    with pytest.raises(ValidationError):
        TaskCreate(
            title="Invalid relationship task",
            assigned_to_id=1,
            company_id=1,
            contact_id=2,
        )


def test_task_create_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        TaskCreate(
            title="Invalid status task",
            assigned_to_id=1,
            status="Unknown",
        )


def test_task_update_includes_only_provided_fields(
) -> None:
    update = TaskUpdate(
        priority=TaskPriority.HIGH,
    )

    assert update.model_dump(exclude_unset=True) == {
        "priority": TaskPriority.HIGH,
    }


def test_task_update_can_clear_optional_fields(
) -> None:
    update = TaskUpdate(
        due_at=None,
        company_id=None,
    )

    assert update.model_dump(exclude_unset=True) == {
        "due_at": None,
        "company_id": None,
    }


def test_task_read_accepts_sqlalchemy_model() -> None:
    now = datetime.now(timezone.utc)

    task_model = Task(
        id=1,
        title="Call customer",
        description=None,
        status=TaskStatus.PENDING,
        priority=TaskPriority.MEDIUM,
        due_at=None,
        assigned_to_id=2,
        created_by_id=1,
        company_id=None,
        contact_id=None,
        lead_id=None,
        completed_at=None,
        created_at=now,
        updated_at=now,
    )

    task = TaskRead.model_validate(task_model)

    assert task.id == 1
    assert task.title == "Call customer"
    assert task.assigned_to_id == 2
    assert task.created_by_id == 1