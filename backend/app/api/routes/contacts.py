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

from app.api.dependencies import (
    get_current_manager,
    get_current_user,
)
from app.crud.company import (
    get_company as get_company_record,
)
from app.crud.contact import (
    create_contact as create_contact_record,
    delete_contact as delete_contact_record,
    get_contact as get_contact_record,
    list_contacts as list_contact_records,
    update_contact as update_contact_record,
)
from app.db.session import get_db
from app.models.contact import Contact
from app.schemas.contact import (
    ContactCreate,
    ContactRead,
    ContactUpdate,
)


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


@router.get(
    "/{contact_id}",
    response_model=ContactRead,
)
def get_contact(
    contact_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
) -> Contact:
    contact = get_contact_record(
        db,
        contact_id,
    )

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    return contact


@router.post(
    "",
    response_model=ContactRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(get_current_manager),
    ],
)
def create_contact(
    contact_data: ContactCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Contact:
    if (
        contact_data.company_id is not None
        and get_company_record(
            db,
            contact_data.company_id,
        )
        is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return create_contact_record(
        db,
        contact_data,
    )


@router.patch(
    "/{contact_id}",
    response_model=ContactRead,
    dependencies=[
        Depends(get_current_manager),
    ],
)
def update_contact(
    contact_id: Annotated[int, Path(ge=1)],
    contact_data: ContactUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> Contact:
    contact = get_contact_record(
        db,
        contact_id,
    )

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    company_id_was_provided = (
        "company_id" in contact_data.model_fields_set
    )

    if (
        company_id_was_provided
        and contact_data.company_id is not None
        and get_company_record(
            db,
            contact_data.company_id,
        )
        is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return update_contact_record(
        db,
        contact,
        contact_data,
    )


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(get_current_manager),
    ],
)
def delete_contact(
    contact_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    contact = get_contact_record(
        db,
        contact_id,
    )

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    delete_contact_record(
        db,
        contact,
    )