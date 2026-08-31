from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import (
    Session,
    selectinload,
)

from app.models.contact import Contact
from app.models.meeting import Meeting, MeetingStatus
from app.models.notification import (
    Notification,
    NotificationType,
)
from app.models.user import User
from app.schemas.meeting import MeetingCreate, MeetingUpdate


def _add_meeting_invitations(
    db: Session,
    meeting: Meeting,
    recipient_ids: set[int],
) -> None:
    """Queue invitations without committing separately."""
    for recipient_id in sorted(recipient_ids):
        notification = Notification(
            recipient_id=recipient_id,
            notification_type=(
                NotificationType.MEETING_INVITATION
            ),
            title="Meeting invitation",
            message=(
                f"You have been invited to meeting "
                f"#{meeting.id}: {meeting.title}"
            ),
            link="/meetings",
        )

        db.add(notification)


def create_meeting(
    db: Session,
    meeting_data: MeetingCreate,
    user_participants: Sequence[User],
    contact_participants: Sequence[Contact],
) -> Meeting:
    meeting_values = meeting_data.model_dump(
        exclude={
            "user_participant_ids",
            "contact_participant_ids",
        }
    )

    meeting = Meeting(**meeting_values)

    meeting.user_participants = list(
        user_participants
    )
    meeting.contact_participants = list(
        contact_participants
    )

    db.add(meeting)

    try:
        # Obtain the meeting ID without committing.
        db.flush()

        recipient_ids = {
            user.id
            for user in meeting.user_participants
        }

        _add_meeting_invitations(
            db,
            meeting,
            recipient_ids,
        )

        # Save the meeting, participants, and invitations together.
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(meeting)
    return meeting


def list_meetings(
    db: Session,
    status: MeetingStatus | None = None,
    organizer_id: int | None = None,
    company_id: int | None = None,
    starts_from: datetime | None = None,
    starts_to: datetime | None = None,
) -> Sequence[Meeting]:
    statement = select(Meeting).options(
        selectinload(Meeting.user_participants),
        selectinload(Meeting.contact_participants),
    )

    if status is not None:
        statement = statement.where(
            Meeting.status == status
        )

    if organizer_id is not None:
        statement = statement.where(
            Meeting.organizer_id == organizer_id
        )

    if company_id is not None:
        statement = statement.where(
            Meeting.company_id == company_id
        )

    if starts_from is not None:
        statement = statement.where(
            Meeting.starts_at >= starts_from
        )

    if starts_to is not None:
        statement = statement.where(
            Meeting.starts_at <= starts_to
        )

    statement = statement.order_by(
        Meeting.starts_at.asc(),
        Meeting.id.asc(),
    )

    return db.scalars(statement).all()


def get_meeting(
    db: Session,
    meeting_id: int,
) -> Meeting | None:
    statement = (
        select(Meeting)
        .where(Meeting.id == meeting_id)
        .options(
            selectinload(Meeting.user_participants),
            selectinload(
                Meeting.contact_participants
            ),
        )
    )

    return db.scalar(statement)


def update_meeting(
    db: Session,
    meeting: Meeting,
    meeting_data: MeetingUpdate,
    user_participants: Sequence[User] | None,
    contact_participants: Sequence[Contact] | None,
) -> Meeting:
    update_values = meeting_data.model_dump(
        exclude_unset=True,
        exclude={
            "user_participant_ids",
            "contact_participant_ids",
        },
    )

    try:
        added_user_ids: set[int] = set()

        if user_participants is not None:
            previous_user_ids = {
                user.id
                for user in meeting.user_participants
            }
            next_user_ids = {
                user.id
                for user in user_participants
            }

            added_user_ids = (
                next_user_ids - previous_user_ids
            )

        for field, value in update_values.items():
            setattr(meeting, field, value)

        if user_participants is not None:
            meeting.user_participants = list(
                user_participants
            )

        if contact_participants is not None:
            meeting.contact_participants = list(
                contact_participants
            )

        _add_meeting_invitations(
            db,
            meeting,
            added_user_ids,
        )

        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(meeting)
    return meeting


def delete_meeting(
    db: Session,
    meeting: Meeting,
) -> None:
    db.delete(meeting)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise