from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.crud.company import get_company as get_company_record
from app.crud.contact import (
    create_contact as create_contact_record,
    list_contacts as list_contact_records,
)
from app.db.session import get_db
from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactRead


router = APIRouter(
    prefix="/contacts",
    tags=["Contacts"],
    dependencies=[
        Depends(get_current_user),
    ],
)


@router.get(
    "",
    response_model=list[ContactRead],
)
def get_contacts(
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[Contact]:
    return list_contact_records(db)


@router.post(
    "",
    response_model=ContactRead,
    status_code=status.HTTP_201_CREATED,
)
def create_contact(
    contact_data: ContactCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Contact:
    if (
        contact_data.company_id is not None
        and get_company_record(db, contact_data.company_id) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return create_contact_record(db, contact_data)