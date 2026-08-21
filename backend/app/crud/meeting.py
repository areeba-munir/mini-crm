from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.meeting import MeetingCreate


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
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(meeting)
    return meeting