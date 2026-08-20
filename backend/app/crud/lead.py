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