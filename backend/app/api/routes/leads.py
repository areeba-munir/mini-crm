from typing import Annotated
from collections.abc import Sequence
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
    create_lead as create_lead_record,
    get_lead as get_lead_record,
    list_leads as list_lead_records,
)
from app.db.session import get_db
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadRead


router = APIRouter(
    prefix="/leads",
    tags=["Leads"],
    dependencies=[
        Depends(get_current_user),
    ],
)
@router.get(
    "",
    response_model=list[LeadRead],
)
def get_leads(
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[Lead]:
    return list_lead_records(db)


@router.get(
    "/{lead_id}",
    response_model=LeadRead,
)
def get_lead(
    lead_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
) -> Lead:
    lead = get_lead_record(db, lead_id)

    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    return lead


@router.post(
    "",
    response_model=LeadRead,
    status_code=status.HTTP_201_CREATED,
)
def create_lead(
    lead_data: LeadCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Lead:
    company = get_company_record(
        db,
        lead_data.company_id,
    )

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    if lead_data.contact_id is not None:
        contact = get_contact_record(
            db,
            lead_data.contact_id,
        )

        if contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found",
            )

        if contact.company_id != lead_data.company_id:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_CONTENT
                ),
                detail=(
                    "Contact must belong to "
                    "the lead company"
                ),
            )

    return create_lead_record(
        db,
        lead_data,
    )