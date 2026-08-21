from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.crud.company import (
    get_company as get_company_record,
)
from app.crud.meeting import (
    create_meeting as create_meeting_record,
)
from app.db.session import get_db
from app.models.contact import Contact
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.meeting import (
    MeetingCreate,
    MeetingRead,
)


router = APIRouter(
    prefix="/meetings",
    tags=["Meetings"],
    dependencies=[
        Depends(get_current_user),
    ],
)


@router.post(
    "",
    response_model=MeetingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_meeting(
    meeting_data: MeetingCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Meeting:
    organizer = db.get(
        User,
        meeting_data.organizer_id,
    )

    if organizer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organizer not found",
        )

    if not organizer.is_active:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=(
                "An inactive user cannot "
                "organize a meeting"
            ),
        )

    if (
        meeting_data.company_id is not None
        and get_company_record(
            db,
            meeting_data.company_id,
        )
        is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    user_participants = list(
        db.scalars(
            select(User).where(
                User.id.in_(
                    meeting_data.user_participant_ids
                )
            )
        ).all()
    )

    found_user_ids = {
        user.id for user in user_participants
    }

    if found_user_ids != set(
        meeting_data.user_participant_ids
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "One or more user participants "
                "were not found"
            ),
        )

    if any(
        not user.is_active
        for user in user_participants
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=(
                "Inactive users cannot "
                "participate in meetings"
            ),
        )

    contact_participants = list(
        db.scalars(
            select(Contact).where(
                Contact.id.in_(
                    meeting_data.contact_participant_ids
                )
            )
        ).all()
    )

    found_contact_ids = {
        contact.id
        for contact in contact_participants
    }

    if found_contact_ids != set(
        meeting_data.contact_participant_ids
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "One or more contact participants "
                "were not found"
            ),
        )

    return create_meeting_record(
        db,
        meeting_data,
        user_participants,
        contact_participants,
    )