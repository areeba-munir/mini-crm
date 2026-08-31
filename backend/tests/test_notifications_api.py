from sqlalchemy import event, select
from app.models.meeting import Meeting
from app.models.task import Task
from app.models.user import User

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.notification import (
    Notification,
    NotificationType,
)


BASE_TIME = datetime(
    2026, 1, 1, tzinfo=timezone.utc
)


@pytest.fixture
def notification_users(
    authenticated_client: TestClient,
) -> tuple[int, int]:
    current_response = authenticated_client.get(
        "/api/v1/auth/me"
    )
    assert current_response.status_code == 200

    other_response = authenticated_client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Other Notification User",
            "email": "notification-other@example.com",
            "password": "StrongPass123!",
        },
    )
    assert other_response.status_code == 201

    return (
        current_response.json()["id"],
        other_response.json()["id"],
    )


def create_notification(
    db: Session,
    *,
    recipient_id: int,
    title: str = "Test notification",
    is_read: bool = False,
    created_at: datetime = BASE_TIME,
) -> Notification:
    notification = Notification(
        recipient_id=recipient_id,
        notification_type=NotificationType.SYSTEM,
        title=title,
        message="Notification test message.",
        link=None,
        is_read=is_read,
        read_at=(
            created_at + timedelta(minutes=1)
            if is_read
            else None
        ),
        created_at=created_at,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


def test_list_notifications_is_scoped_sorted_and_paginated(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    recipient_id, other_id = notification_users
    newer_time = BASE_TIME + timedelta(days=1)

    newer = create_notification(
        db_session,
        recipient_id=recipient_id,
        title="Newer",
        created_at=newer_time,
    )
    newest = create_notification(
        db_session,
        recipient_id=recipient_id,
        title="Newest",
        created_at=newer_time,
    )
    oldest = create_notification(
        db_session,
        recipient_id=recipient_id,
        title="Oldest",
        created_at=BASE_TIME,
    )
    create_notification(
        db_session,
        recipient_id=other_id,
        title="Another user's notification",
        created_at=newer_time,
    )

    response = authenticated_client.get(
        "/api/v1/notifications"
    )

    assert response.status_code == 200
    records = response.json()

    assert [
        record["id"] for record in records
    ] == [
        newest.id,
        newer.id,
        oldest.id,
    ]
    assert all(
        record["recipient_id"] == recipient_id
        for record in records
    )
    assert records[0]["notification_type"] == "System"
    assert records[0]["link"] is None
    assert records[0]["read_at"] is None

    page_response = authenticated_client.get(
        "/api/v1/notifications",
        params={
            "offset": 1,
            "limit": 1,
        },
    )

    assert page_response.status_code == 200
    assert [
        record["id"]
        for record in page_response.json()
    ] == [newer.id]


def test_notifications_support_unread_filter(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    recipient_id, other_id = notification_users

    unread = create_notification(
        db_session,
        recipient_id=recipient_id,
    )
    create_notification(
        db_session,
        recipient_id=recipient_id,
        is_read=True,
    )
    create_notification(
        db_session,
        recipient_id=other_id,
    )

    response = authenticated_client.get(
        "/api/v1/notifications",
        params={"unread_only": True},
    )

    assert response.status_code == 200
    assert [
        record["id"] for record in response.json()
    ] == [unread.id]


def test_unread_count_is_scoped_to_recipient(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    recipient_id, other_id = notification_users

    empty_response = authenticated_client.get(
        "/api/v1/notifications/unread-count"
    )

    assert empty_response.status_code == 200
    assert empty_response.json() == {
        "unread_count": 0,
    }

    create_notification(
        db_session,
        recipient_id=recipient_id,
    )
    create_notification(
        db_session,
        recipient_id=recipient_id,
        is_read=True,
    )
    create_notification(
        db_session,
        recipient_id=other_id,
    )

    response = authenticated_client.get(
        "/api/v1/notifications/unread-count"
    )

    assert response.status_code == 200
    assert response.json() == {
        "unread_count": 1,
    }


def test_mark_notification_read_is_idempotent(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    recipient_id, _ = notification_users

    notification = create_notification(
        db_session,
        recipient_id=recipient_id,
    )
    untouched = create_notification(
        db_session,
        recipient_id=recipient_id,
    )

    response = authenticated_client.patch(
        f"/api/v1/notifications/{notification.id}/read"
    )

    assert response.status_code == 200
    record = response.json()

    assert record["id"] == notification.id
    assert record["is_read"] is True
    assert record["read_at"] is not None

    first_read_at = record["read_at"]

    repeat_response = authenticated_client.patch(
        f"/api/v1/notifications/{notification.id}/read"
    )

    assert repeat_response.status_code == 200
    assert repeat_response.json()["read_at"] == first_read_at

    db_session.refresh(notification)
    db_session.refresh(untouched)

    assert notification.is_read is True
    assert notification.read_at == datetime.fromisoformat(
        first_read_at
    )
    assert untouched.is_read is False
    assert untouched.read_at is None

    count_response = authenticated_client.get(
        "/api/v1/notifications/unread-count"
    )

    assert count_response.status_code == 200
    assert count_response.json() == {
        "unread_count": 1,
    }


def test_cannot_mark_another_users_notification_read(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    _, other_id = notification_users

    notification = create_notification(
        db_session,
        recipient_id=other_id,
    )

    response = authenticated_client.patch(
        f"/api/v1/notifications/{notification.id}/read"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found"

    db_session.refresh(notification)

    assert notification.is_read is False
    assert notification.read_at is None


def test_missing_notification_returns_404(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    recipient_id, _ = notification_users

    notification = create_notification(
        db_session,
        recipient_id=recipient_id,
    )
    missing_id = notification.id

    db_session.delete(notification)
    db_session.commit()

    response = authenticated_client.patch(
        f"/api/v1/notifications/{missing_id}/read"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found"


def test_mark_all_read_is_scoped_and_idempotent(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    recipient_id, other_id = notification_users

    unread_notifications = [
        create_notification(
            db_session,
            recipient_id=recipient_id,
        )
        for _ in range(2)
    ]
    already_read = create_notification(
        db_session,
        recipient_id=recipient_id,
        is_read=True,
    )
    other_notification = create_notification(
        db_session,
        recipient_id=other_id,
    )

    original_read_at = already_read.read_at

    response = authenticated_client.patch(
        "/api/v1/notifications/read-all"
    )

    assert response.status_code == 200
    assert response.json() == {
        "unread_count": 0,
    }

    for notification in unread_notifications:
        db_session.refresh(notification)
        assert notification.is_read is True
        assert notification.read_at is not None

    first_read_times = [
        notification.read_at
        for notification in unread_notifications
    ]

    db_session.refresh(already_read)
    db_session.refresh(other_notification)

    assert already_read.read_at == original_read_at
    assert other_notification.is_read is False
    assert other_notification.read_at is None

    repeat_response = authenticated_client.patch(
        "/api/v1/notifications/read-all"
    )

    assert repeat_response.status_code == 200
    assert repeat_response.json() == {
        "unread_count": 0,
    }

    for notification, first_read_at in zip(
        unread_notifications,
        first_read_times,
        strict=True,
    ):
        db_session.refresh(notification)
        assert notification.read_at == first_read_at


def test_mark_all_read_handles_no_notifications(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.patch(
        "/api/v1/notifications/read-all"
    )

    assert response.status_code == 200
    assert response.json() == {
        "unread_count": 0,
    }


def test_member_can_access_own_notifications(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    admin_id, member_id = notification_users

    member_notification = create_notification(
        db_session,
        recipient_id=member_id,
    )
    create_notification(
        db_session,
        recipient_id=admin_id,
    )

    login_response = authenticated_client.post(
        "/api/v1/auth/login",
        data={
            "username": "notification-other@example.com",
            "password": "StrongPass123!",
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    authenticated_client.headers["Authorization"] = (
        f"Bearer {token}"
    )

    me_response = authenticated_client.get(
        "/api/v1/auth/me"
    )
    assert me_response.status_code == 200
    assert me_response.json()["role"] == "Member"

    response = authenticated_client.get(
        "/api/v1/notifications"
    )

    assert response.status_code == 200
    assert [
        record["id"] for record in response.json()
    ] == [member_notification.id]

    read_response = authenticated_client.patch(
        f"/api/v1/notifications/{member_notification.id}/read"
    )

    assert read_response.status_code == 200
    assert read_response.json()["is_read"] is True


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/notifications"),
        ("GET", "/api/v1/notifications/unread-count"),
        ("PATCH", "/api/v1/notifications/read-all"),
        ("PATCH", "/api/v1/notifications/1/read"),
    ],
)
def test_notification_endpoints_require_authentication(
    client: TestClient,
    method: str,
    path: str,
) -> None:
    response = client.request(method, path)

    assert response.status_code == 401

def _create_assigned_task(
    client: TestClient,
    *,
    recipient_id: int,
    title: str = "Notification task",
) -> int:
    response = client.post(
        "/api/v1/tasks",
        json={
            "title": title,
            "assigned_to_id": recipient_id,
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def _assignment_notifications(
    db: Session,
) -> list[Notification]:
    return list(
        db.scalars(
            select(Notification)
            .where(
                Notification.notification_type
                == NotificationType.TASK_ASSIGNED
            )
            .order_by(Notification.id)
        )
    )


def _reject_notification_insert(
    _mapper: object,
    _connection: object,
    _target: Notification,
) -> None:
    raise RuntimeError(
        "Simulated notification insert failure"
    )


@pytest.mark.parametrize(
    "assign_to_self",
    [False, True],
)
def test_task_creation_notifies_assignee(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
    assign_to_self: bool,
) -> None:
    current_user_id, other_user_id = notification_users

    recipient_id = (
        current_user_id
        if assign_to_self
        else other_user_id
    )

    task_id = _create_assigned_task(
        authenticated_client,
        recipient_id=recipient_id,
        title="Send proposal",
    )

    notifications = _assignment_notifications(
        db_session
    )

    assert len(notifications) == 1

    notification = notifications[0]

    assert notification.recipient_id == recipient_id
    assert notification.is_read is False
    assert notification.read_at is None
    assert notification.link == "/tasks"
    assert f"#{task_id}:" in notification.message
    assert "Send proposal" in notification.message


def test_task_reassignment_notifies_new_assignee(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    first_user_id, second_user_id = notification_users

    task_id = _create_assigned_task(
        authenticated_client,
        recipient_id=first_user_id,
    )

    original_notifications = _assignment_notifications(
        db_session
    )
    assert len(original_notifications) == 1

    original_notification_id = original_notifications[0].id

    response = authenticated_client.patch(
        f"/api/v1/tasks/{task_id}",
        json={
            "assigned_to_id": second_user_id,
        },
    )

    assert response.status_code == 200

    notifications = _assignment_notifications(
        db_session
    )

    assert len(notifications) == 2
    assert notifications[0].id == original_notification_id
    assert [
        notification.recipient_id
        for notification in notifications
    ] == [
        first_user_id,
        second_user_id,
    ]
    assert f"#{task_id}:" in notifications[1].message


def test_task_edits_do_not_duplicate_assignment_notifications(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    recipient_id, _ = notification_users

    task_id = _create_assigned_task(
        authenticated_client,
        recipient_id=recipient_id,
    )

    original_notifications = _assignment_notifications(
        db_session
    )
    assert len(original_notifications) == 1
    original_notification_id = original_notifications[0].id

    updates = [
        {"assigned_to_id": recipient_id},
        {"title": "Updated task title"},
        {"priority": "High"},
        {"status": "Completed"},
    ]

    for update in updates:
        response = authenticated_client.patch(
            f"/api/v1/tasks/{task_id}",
            json=update,
        )

        assert response.status_code == 200

        notifications = _assignment_notifications(
            db_session
        )

        assert len(notifications) == 1
        assert notifications[0].id == original_notification_id


def test_inactive_assignee_creates_no_task_or_notification(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    _, inactive_user_id = notification_users

    inactive_user = db_session.get(
        User,
        inactive_user_id,
    )
    assert inactive_user is not None

    inactive_user.is_active = False
    db_session.commit()

    response = authenticated_client.post(
        "/api/v1/tasks",
        json={
            "title": "Inactive assignment",
            "assigned_to_id": inactive_user_id,
        },
    )

    assert response.status_code == 422
    assert _assignment_notifications(db_session) == []

    task = db_session.scalar(
        select(Task).where(
            Task.title == "Inactive assignment"
        )
    )
    assert task is None


def test_notification_failure_rolls_back_task_creation(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    recipient_id, _ = notification_users

    event.listen(
        Notification,
        "before_insert",
        _reject_notification_insert,
    )

    try:
        with pytest.raises(
            RuntimeError,
            match="Simulated notification insert failure",
        ):
            _create_assigned_task(
                authenticated_client,
                recipient_id=recipient_id,
                title="Rollback create",
            )
    finally:
        event.remove(
            Notification,
            "before_insert",
            _reject_notification_insert,
        )

    db_session.expire_all()

    task = db_session.scalar(
        select(Task).where(
            Task.title == "Rollback create"
        )
    )

    assert task is None
    assert _assignment_notifications(db_session) == []


def test_notification_failure_rolls_back_task_reassignment(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    first_user_id, second_user_id = notification_users

    task_id = _create_assigned_task(
        authenticated_client,
        recipient_id=first_user_id,
    )

    original_notifications = _assignment_notifications(
        db_session
    )
    assert len(original_notifications) == 1
    original_notification_id = original_notifications[0].id

    event.listen(
        Notification,
        "before_insert",
        _reject_notification_insert,
    )

    try:
        with pytest.raises(
            RuntimeError,
            match="Simulated notification insert failure",
        ):
            authenticated_client.patch(
                f"/api/v1/tasks/{task_id}",
                json={
                    "assigned_to_id": second_user_id,
                },
            )
    finally:
        event.remove(
            Notification,
            "before_insert",
            _reject_notification_insert,
        )

    db_session.expire_all()

    task = db_session.get(Task, task_id)

    assert task is not None
    assert task.assigned_to_id == first_user_id

    notifications = _assignment_notifications(
        db_session
    )

    assert len(notifications) == 1
    assert notifications[0].id == original_notification_id
    assert notifications[0].recipient_id == first_user_id

def _create_notification_meeting(
    client: TestClient,
    *,
    organizer_id: int,
    user_ids: list[int],
    title: str = "Notification meeting",
) -> int:
    response = client.post(
        "/api/v1/meetings",
        json={
            "title": title,
            "organizer_id": organizer_id,
            "starts_at": BASE_TIME.isoformat(),
            "ends_at": (
                BASE_TIME + timedelta(hours=1)
            ).isoformat(),
            "user_participant_ids": user_ids,
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def _meeting_invitations(
    db: Session,
) -> list[Notification]:
    return list(
        db.scalars(
            select(Notification)
            .where(
                Notification.notification_type
                == NotificationType.MEETING_INVITATION
            )
            .order_by(Notification.id)
        )
    )


@pytest.mark.parametrize(
    "include_organizer",
    [False, True],
)
def test_meeting_creation_notifies_selected_users(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
    include_organizer: bool,
) -> None:
    organizer_id, participant_id = notification_users

    user_ids = [participant_id]

    if include_organizer:
        user_ids.append(organizer_id)

    meeting_id = _create_notification_meeting(
        authenticated_client,
        organizer_id=organizer_id,
        user_ids=user_ids,
        title="Planning discussion",
    )

    notifications = _meeting_invitations(
        db_session
    )

    assert [
        notification.recipient_id
        for notification in notifications
    ] == sorted(user_ids)

    for notification in notifications:
        assert notification.is_read is False
        assert notification.read_at is None
        assert notification.link == "/meetings"
        assert f"#{meeting_id}:" in notification.message
        assert "Planning discussion" in notification.message


def test_meeting_without_user_participants_creates_no_invitations(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    organizer_id, _ = notification_users

    _create_notification_meeting(
        authenticated_client,
        organizer_id=organizer_id,
        user_ids=[],
    )

    assert _meeting_invitations(db_session) == []


def test_meeting_update_invites_only_new_participants(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    organizer_id, participant_id = notification_users

    meeting_id = _create_notification_meeting(
        authenticated_client,
        organizer_id=organizer_id,
        user_ids=[organizer_id],
    )

    original_notifications = _meeting_invitations(
        db_session
    )
    assert len(original_notifications) == 1
    original_id = original_notifications[0].id

    response = authenticated_client.patch(
        f"/api/v1/meetings/{meeting_id}",
        json={
            "title": "Expanded discussion",
            "user_participant_ids": [
                organizer_id,
                participant_id,
            ],
        },
    )

    assert response.status_code == 200

    notifications = _meeting_invitations(
        db_session
    )

    assert len(notifications) == 2
    assert notifications[0].id == original_id
    assert notifications[0].recipient_id == organizer_id
    assert notifications[1].recipient_id == participant_id
    assert "Expanded discussion" in notifications[1].message


def test_meeting_edits_do_not_duplicate_invitations(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    organizer_id, participant_id = notification_users
    user_ids = sorted([organizer_id, participant_id])

    meeting_id = _create_notification_meeting(
        authenticated_client,
        organizer_id=organizer_id,
        user_ids=user_ids,
    )

    original_ids = [
        notification.id
        for notification in _meeting_invitations(
            db_session
        )
    ]
    assert len(original_ids) == 2

    updates = [
        {
            "user_participant_ids": list(
                reversed(user_ids)
            ),
        },
        {"title": "Updated meeting title"},
        {"notes": "Updated agenda"},
        {
            "starts_at": (
                BASE_TIME + timedelta(hours=2)
            ).isoformat(),
            "ends_at": (
                BASE_TIME + timedelta(hours=3)
            ).isoformat(),
        },
        {"contact_participant_ids": []},
    ]

    for update in updates:
        response = authenticated_client.patch(
            f"/api/v1/meetings/{meeting_id}",
            json=update,
        )

        assert response.status_code == 200
        assert response.json()["user_participant_ids"] == user_ids

        assert [
            notification.id
            for notification in _meeting_invitations(
                db_session
            )
        ] == original_ids


def test_meeting_removal_and_readding_participants(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    organizer_id, participant_id = notification_users

    meeting_id = _create_notification_meeting(
        authenticated_client,
        organizer_id=organizer_id,
        user_ids=[organizer_id, participant_id],
    )

    original_ids = [
        notification.id
        for notification in _meeting_invitations(
            db_session
        )
    ]
    assert len(original_ids) == 2

    for remaining_ids in ([organizer_id], []):
        response = authenticated_client.patch(
            f"/api/v1/meetings/{meeting_id}",
            json={
                "user_participant_ids": remaining_ids,
            },
        )

        assert response.status_code == 200
        assert response.json()["user_participant_ids"] == remaining_ids

        assert [
            notification.id
            for notification in _meeting_invitations(
                db_session
            )
        ] == original_ids

    readd_response = authenticated_client.patch(
        f"/api/v1/meetings/{meeting_id}",
        json={
            "user_participant_ids": [participant_id],
        },
    )

    assert readd_response.status_code == 200

    notifications = _meeting_invitations(
        db_session
    )

    assert len(notifications) == 3
    assert [
        notification.id
        for notification in notifications[:2]
    ] == original_ids
    assert notifications[2].recipient_id == participant_id


def test_inactive_meeting_participant_creates_no_invitation(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    organizer_id, participant_id = notification_users

    participant = db_session.get(
        User,
        participant_id,
    )
    assert participant is not None

    participant.is_active = False
    db_session.commit()

    response = authenticated_client.post(
        "/api/v1/meetings",
        json={
            "title": "Inactive invitation",
            "organizer_id": organizer_id,
            "starts_at": BASE_TIME.isoformat(),
            "ends_at": (
                BASE_TIME + timedelta(hours=1)
            ).isoformat(),
            "user_participant_ids": [participant_id],
        },
    )

    assert response.status_code == 422
    assert _meeting_invitations(db_session) == []

    meeting = db_session.scalar(
        select(Meeting).where(
            Meeting.title == "Inactive invitation"
        )
    )
    assert meeting is None


def test_notification_failure_rolls_back_meeting_creation(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    organizer_id, participant_id = notification_users

    event.listen(
        Notification,
        "before_insert",
        _reject_notification_insert,
    )

    try:
        with pytest.raises(
            RuntimeError,
            match="Simulated notification insert failure",
        ):
            _create_notification_meeting(
                authenticated_client,
                organizer_id=organizer_id,
                user_ids=[organizer_id, participant_id],
                title="Rollback meeting creation",
            )
    finally:
        event.remove(
            Notification,
            "before_insert",
            _reject_notification_insert,
        )

    db_session.expire_all()

    meeting = db_session.scalar(
        select(Meeting).where(
            Meeting.title == "Rollback meeting creation"
        )
    )

    assert meeting is None
    assert _meeting_invitations(db_session) == []


def test_notification_failure_rolls_back_meeting_update(
    authenticated_client: TestClient,
    db_session: Session,
    notification_users: tuple[int, int],
) -> None:
    organizer_id, participant_id = notification_users

    meeting_id = _create_notification_meeting(
        authenticated_client,
        organizer_id=organizer_id,
        user_ids=[organizer_id],
        title="Original meeting title",
    )

    original_notifications = _meeting_invitations(
        db_session
    )
    assert len(original_notifications) == 1
    original_id = original_notifications[0].id

    event.listen(
        Notification,
        "before_insert",
        _reject_notification_insert,
    )

    try:
        with pytest.raises(
            RuntimeError,
            match="Simulated notification insert failure",
        ):
            authenticated_client.patch(
                f"/api/v1/meetings/{meeting_id}",
                json={
                    "title": "Should be rolled back",
                    "user_participant_ids": [
                        organizer_id,
                        participant_id,
                    ],
                },
            )
    finally:
        event.remove(
            Notification,
            "before_insert",
            _reject_notification_insert,
        )

    db_session.expire_all()

    meeting = db_session.get(
        Meeting,
        meeting_id,
    )

    assert meeting is not None
    assert meeting.title == "Original meeting title"
    assert meeting.user_participant_ids == [organizer_id]

    notifications = _meeting_invitations(
        db_session
    )

    assert len(notifications) == 1
    assert notifications[0].id == original_id
    assert notifications[0].recipient_id == organizer_id