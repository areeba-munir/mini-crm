from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lead import Lead, LeadStage
from app.schemas.lead import (
    LeadCreate,
    LeadUpdate,
)


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
    stage: LeadStage | None = None,
) -> Sequence[Lead]:
    statement = select(Lead)

    if stage is not None:
        statement = statement.where(
            Lead.stage == stage
        )

    statement = statement.order_by(
        Lead.created_at.desc(),
        Lead.id.desc(),
    )

    return db.scalars(statement).all()


def get_lead(
    db: Session,
    lead_id: int,
) -> Lead | None:
    return db.get(Lead, lead_id)


def update_lead(
    db: Session,
    lead: Lead,
    lead_data: LeadUpdate,
) -> Lead:
    update_data = lead_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(lead, field, value)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(lead)
    return lead
def delete_lead(
    db: Session,
    lead: Lead,
) -> None:
    db.delete(lead)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise