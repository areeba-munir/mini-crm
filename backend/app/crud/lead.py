from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.schemas.lead import LeadCreate


def create_lead(
    db: Session,
    lead_data: LeadCreate,
) -> Lead:
    lead = Lead(**lead_data.model_dump())

    db.add(lead)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(lead)
    return lead


def list_leads(
    db: Session,
) -> Sequence[Lead]:
    statement = select(Lead).order_by(
        Lead.created_at.desc(),
        Lead.id.desc(),
    )

    return db.scalars(statement).all()


def get_lead(
    db: Session,
    lead_id: int,
) -> Lead | None:
    return db.get(Lead, lead_id)