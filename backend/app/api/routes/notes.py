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
    delete_note as delete_note_record,
    get_note as get_note_record,
    list_notes as list_note_records,
    update_note as update_note_record,
)
from app.db.session import get_db
from app.models.note import Note
from app.models.user import User
from app.schemas.note import NoteCreate, NoteRead, NoteUpdate


router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
    dependencies=[
        Depends(get_current_user),
    ],
)
def ensure_note_author(
    note: Note,
    current_user: User,
) -> None:
    if note.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You may only modify "
                "your own notes"
            ),
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
@router.patch(
    "/{note_id}",
    response_model=NoteRead,
)
def update_note(
    note_data: NoteUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    note_id: int = Path(ge=1),
) -> Note:
    note = get_note_record(db, note_id)

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    ensure_note_author(note, current_user)

    company_id = (
        note_data.company_id
        if "company_id" in note_data.model_fields_set
        else note.company_id
    )
    contact_id = (
        note_data.contact_id
        if "contact_id" in note_data.model_fields_set
        else note.contact_id
    )
    lead_id = (
        note_data.lead_id
        if "lead_id" in note_data.model_fields_set
        else note.lead_id
    )

    related_ids = (
        company_id,
        contact_id,
        lead_id,
    )

    if sum(
        value is not None
        for value in related_ids
    ) != 1:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=(
                "A note must relate to exactly one "
                "company, contact, or lead"
            ),
        )

    if (
        company_id is not None
        and get_company_record(db, company_id) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    if (
        contact_id is not None
        and get_contact_record(db, contact_id) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    if (
        lead_id is not None
        and get_lead_record(db, lead_id) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    return update_note_record(
        db,
        note,
        note_data,
    )
@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_note(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    note_id: int = Path(ge=1),
) -> None:
    note = get_note_record(db, note_id)

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )

    ensure_note_author(note, current_user)
    delete_note_record(db, note)