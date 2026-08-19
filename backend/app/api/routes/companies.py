from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud.company import create_company as create_company_record
from app.db.session import get_db
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyRead


router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


@router.post(
    "",
    response_model=CompanyRead,
    status_code=status.HTTP_201_CREATED,
)
def create_company(
    company_data: CompanyCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Company:
    return create_company_record(db, company_data)