from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.crud.company import get_company
from app.crud.contact import create_contact as create_contact_record
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


@router.post(
    "",
    response_model=ContactRead,
    status_code=status.HTTP_201_CREATED,
)
def create_contact(
    contact_data: ContactCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Contact:
    if contact_data.company_id is not None:
        company = get_company(
            db,
            contact_data.company_id,
        )

        if company is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )

    return create_contact_record(
        db,
        contact_data,
    )