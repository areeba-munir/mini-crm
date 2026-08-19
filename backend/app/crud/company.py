from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.schemas.company import CompanyCreate


def create_company(db: Session, company_data: CompanyCreate) -> Company:
    company = Company(**company_data.model_dump())

    db.add(company)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(company)
    return company


def list_companies(db: Session) -> Sequence[Company]:
    statement = select(Company).order_by(
        Company.name,
        Company.id,
    )

    return db.scalars(statement).all()