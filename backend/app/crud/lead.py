from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Literal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.lead import Lead, LeadStage
from app.schemas.lead import (
    LeadCreate,
    LeadUpdate,
)


LeadSort = Literal[
    "newest",
    "oldest",
    "value_high",
    "value_low",
    "close_soon",
]


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
    *,
    stage: LeadStage | None = None,
    search: str | None = None,
    company_id: int | None = None,
    contact_id: int | None = None,
    min_estimated_value: Decimal | None = None,
    max_estimated_value: Decimal | None = None,
    expected_close_from: date | None = None,
    expected_close_to: date | None = None,
    sort_by: LeadSort = "newest",
) -> Sequence[Lead]:
    statement = select(Lead)

    if stage is not None:
        statement = statement.where(
            Lead.stage == stage
        )

    if search is not None:
        stripped_search = search.strip()

        if stripped_search:
            search_pattern = (
                f"%{stripped_search}%"
            )

            statement = statement.where(
                or_(
                    Lead.title.ilike(
                        search_pattern
                    ),
                    Lead.source.ilike(
                        search_pattern
                    ),
                    Lead.description.ilike(
                        search_pattern
                    ),
                )
            )

    if company_id is not None:
        statement = statement.where(
            Lead.company_id == company_id
        )

    if contact_id is not None:
        statement = statement.where(
            Lead.contact_id == contact_id
        )

    if min_estimated_value is not None:
        statement = statement.where(
            Lead.estimated_value
            >= min_estimated_value
        )

    if max_estimated_value is not None:
        statement = statement.where(
            Lead.estimated_value
            <= max_estimated_value
        )

    if expected_close_from is not None:
        statement = statement.where(
            Lead.expected_close_date
            >= expected_close_from
        )

    if expected_close_to is not None:
        statement = statement.where(
            Lead.expected_close_date
            <= expected_close_to
        )

    if sort_by == "oldest":
        statement = statement.order_by(
            Lead.created_at.asc(),
            Lead.id.asc(),
        )
    elif sort_by == "value_high":
        statement = statement.order_by(
            Lead.estimated_value.desc().nullslast(),
            Lead.created_at.desc(),
            Lead.id.desc(),
        )
    elif sort_by == "value_low":
        statement = statement.order_by(
            Lead.estimated_value.asc().nullslast(),
            Lead.created_at.desc(),
            Lead.id.desc(),
        )
    elif sort_by == "close_soon":
        statement = statement.order_by(
            Lead.expected_close_date.asc().nullslast(),
            Lead.created_at.desc(),
            Lead.id.desc(),
        )
    else:
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