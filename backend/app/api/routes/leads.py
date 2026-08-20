from typing import Annotated
from collections.abc import Sequence
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
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
    delete_lead as delete_lead_record,
    get_lead as get_lead_record,
    list_leads as list_lead_records,
    update_lead as update_lead_record,
)
from app.db.session import get_db
from app.models.lead import Lead, LeadStage
from app.schemas.lead import LeadCreate, LeadRead, LeadUpdate


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
    stage: Annotated[
        LeadStage | None,
        Query(),
    ] = None,
) -> Sequence[Lead]:
    return list_lead_records(
        db,
        stage=stage,
    )


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
@router.patch(
    "/{lead_id}",
    response_model=LeadRead,
)
def update_lead(
    lead_id: Annotated[int, Path(ge=1)],
    lead_data: LeadUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> Lead:
    lead = get_lead_record(db, lead_id)

    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    company_id = (
        lead_data.company_id
        if "company_id" in lead_data.model_fields_set
        else lead.company_id
    )

    if get_company_record(db, company_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    contact_id = (
        lead_data.contact_id
        if "contact_id" in lead_data.model_fields_set
        else lead.contact_id
    )

    if contact_id is not None:
        contact = get_contact_record(
            db,
            contact_id,
        )

        if contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found",
            )

        if contact.company_id != company_id:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_CONTENT
                ),
                detail=(
                    "Contact must belong to "
                    "the lead company"
                ),
            )

    return update_lead_record(
        db,
        lead,
        lead_data,
    )
@router.delete(
    "/{lead_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_lead(
    lead_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    lead = get_lead_record(db, lead_id)

    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    delete_lead_record(db, lead)