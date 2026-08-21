from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.models.contact import Contact
from app.models.meeting import Meeting, MeetingStatus
from app.models.user import User
from app.schemas.meeting import (
    MeetingCreate,
    MeetingRead,
    MeetingUpdate,
)


def test_meeting_create_normalizes_input(
) -> None:
    meeting = MeetingCreate(
        title="  Project discussion  ",
        starts_at="2026-08-25T10:00:00+05:00",
        ends_at="2026-08-25T11:00:00+05:00",
        organizer_id=1,
        meeting_link=(
            "https://meet.example.com/room"
        ),
    )

    assert meeting.title == "Project discussion"
    assert meeting.status == MeetingStatus.SCHEDULED
    assert meeting.starts_at.hour == 5
    assert meeting.starts_at.utcoffset() == timedelta(0)


def test_meeting_create_rejects_invalid_time_range(
) -> None:
    with pytest.raises(ValidationError):
        MeetingCreate(
            title="Invalid meeting",
            starts_at="2026-08-25T11:00:00Z",
            ends_at="2026-08-25T10:00:00Z",
            organizer_id=1,
        )


def test_meeting_create_rejects_naive_datetime(
) -> None:
    with pytest.raises(ValidationError):
        MeetingCreate(
            title="Naive time meeting",
            starts_at="2026-08-25T10:00:00",
            ends_at="2026-08-25T11:00:00",
            organizer_id=1,
        )


def test_meeting_create_rejects_duplicate_participants(
) -> None:
    with pytest.raises(ValidationError):
        MeetingCreate(
            title="Duplicate participants",
            starts_at="2026-08-25T10:00:00Z",
            ends_at="2026-08-25T11:00:00Z",
            organizer_id=1,
            user_participant_ids=[2, 2],
        )


def test_meeting_create_rejects_invalid_link(
) -> None:
    with pytest.raises(ValidationError):
        MeetingCreate(
            title="Invalid link",
            starts_at="2026-08-25T10:00:00Z",
            ends_at="2026-08-25T11:00:00Z",
            organizer_id=1,
            meeting_link="not-a-url",
        )


def test_meeting_update_includes_only_provided_fields(
) -> None:
    update = MeetingUpdate(
        status=MeetingStatus.COMPLETED,
        user_participant_ids=[],
    )

    assert update.model_dump(exclude_unset=True) == {
        "status": MeetingStatus.COMPLETED,
        "user_participant_ids": [],
    }


def test_meeting_read_accepts_sqlalchemy_model(
) -> None:
    now = datetime.now(timezone.utc)

    user = User(
        id=2,
        full_name="Participant User",
        email="participant@example.com",
        password_hash="unused",
        is_active=True,
    )
    contact = Contact(
        id=3,
        first_name="Client",
    )

    meeting_model = Meeting(
        id=1,
        title="Project discussion",
        description=None,
        starts_at=now,
        ends_at=now + timedelta(hours=1),
        location=None,
        meeting_link=None,
        notes=None,
        status=MeetingStatus.SCHEDULED,
        organizer_id=1,
        company_id=None,
        created_at=now,
        updated_at=now,
        user_participants=[user],
        contact_participants=[contact],
    )

    meeting = MeetingRead.model_validate(
        meeting_model
    )

    assert meeting.id == 1
    assert meeting.user_participant_ids == [2]
    assert meeting.contact_participant_ids == [3]