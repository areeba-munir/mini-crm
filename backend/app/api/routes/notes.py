from collections.abc import Sequence
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
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
from app.crud.note import (
    create_note as create_note_record,
    get_note as get_note_record,
    list_notes as list_note_records,
)
from app.db.session import get_db
from app.models.note import Note
from app.models.user import User
from app.schemas.note import NoteCreate, NoteRead


router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
    dependencies=[
        Depends(get_current_user),
    ],
)


@router.get(
    "",
    response_model=list[NoteRead],
)
def get_notes(
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[Note]:
    return list_note_records(db)


@router.get(
    "/{note_id}",
    response_model=NoteRead,
)
def get_note(
    db: Annotated[Session, Depends(get_db)],
    note_id: int = Path(ge=1),
) -> Note:
    note = get_note_record(db, note_id)

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    return note


@router.post(
    "",
    response_model=NoteRead,
    status_code=status.HTTP_201_CREATED,
)
def create_note(
    note_data: NoteCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> Note:
    if (
        note_data.company_id is not None
        and get_company_record(
            db,
            note_data.company_id,
        )
        is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    if (
        note_data.contact_id is not None
        and get_contact_record(
            db,
            note_data.contact_id,
        )
        is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    if (
        note_data.lead_id is not None
        and get_lead_record(
            db,
            note_data.lead_id,
        )
        is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    return create_note_record(
        db,
        note_data,
        author_id=current_user.id,
    )