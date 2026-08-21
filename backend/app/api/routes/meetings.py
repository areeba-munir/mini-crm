from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session
from collections.abc import Sequence

from pydantic import AwareDatetime

from app.api.dependencies import get_current_user
from app.crud.company import (
    get_company as get_company_record,
)
from app.crud.meeting import (
    create_meeting as create_meeting_record,
    get_meeting as get_meeting_record,
    list_meetings as list_meeting_records,
    update_meeting as update_meeting_record,
)
from app.db.session import get_db
from app.models.contact import Contact
from app.models.meeting import Meeting, MeetingStatus
from app.models.user import User
from app.schemas.meeting import (
    MeetingCreate,
    MeetingRead,
    MeetingUpdate,
)


router = APIRouter(
    prefix="/meetings",
    tags=["Meetings"],
    dependencies=[
        Depends(get_current_user),
    ],
)
@router.get(
    "",
    response_model=list[MeetingRead],
)
def get_meetings(
    db: Annotated[Session, Depends(get_db)],
    meeting_status: MeetingStatus | None = Query(
        default=None,
        alias="status",
    ),
    organizer_id: int | None = Query(
        default=None,
        ge=1,
    ),
    company_id: int | None = Query(
        default=None,
        ge=1,
    ),
    starts_from: AwareDatetime | None = Query(
        default=None,
    ),
    starts_to: AwareDatetime | None = Query(
        default=None,
    ),
) -> Sequence[Meeting]:
    if (
        starts_from is not None
        and starts_to is not None
        and starts_to < starts_from
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=(
                "starts_to cannot be earlier "
                "than starts_from"
            ),
        )

    return list_meeting_records(
        db,
        status=meeting_status,
        organizer_id=organizer_id,
        company_id=company_id,
        starts_from=starts_from,
        starts_to=starts_to,
    )


@router.get(
    "/{meeting_id}",
    response_model=MeetingRead,
)
def get_meeting(
    db: Annotated[Session, Depends(get_db)],
    meeting_id: int = Path(ge=1),
) -> Meeting:
    meeting = get_meeting_record(
        db,
        meeting_id,
    )

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    return meeting

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

@router.patch(
    "/{meeting_id}",
    response_model=MeetingRead,
)
def update_meeting(
    meeting_data: MeetingUpdate,
    db: Annotated[Session, Depends(get_db)],
    meeting_id: int = Path(ge=1),
) -> Meeting:
    meeting = get_meeting_record(
        db,
        meeting_id,
    )

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    starts_at = (
        meeting_data.starts_at
        if "starts_at" in meeting_data.model_fields_set
        else meeting.starts_at
    )
    ends_at = (
        meeting_data.ends_at
        if "ends_at" in meeting_data.model_fields_set
        else meeting.ends_at
    )

    if ends_at <= starts_at:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail="Meeting end must be after start",
        )

    if "organizer_id" in meeting_data.model_fields_set:
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
        "company_id" in meeting_data.model_fields_set
        and meeting_data.company_id is not None
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

    user_participants = None

    if (
        "user_participant_ids"
        in meeting_data.model_fields_set
    ):
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

    contact_participants = None

    if (
        "contact_participant_ids"
        in meeting_data.model_fields_set
    ):
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

    return update_meeting_record(
        db,
        meeting,
        meeting_data,
        user_participants,
        contact_participants,
    )