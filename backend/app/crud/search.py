from collections.abc import Sequence

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.contact import Contact
from app.models.lead import Lead


SearchRecordGroups = tuple[
    Sequence[Company],
    Sequence[Contact],
    Sequence[Lead],
]


def build_search_pattern(query: str) -> str:
    escaped_query = (
        query.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )

    return f"%{escaped_query}%"


def search_crm(
    db: Session,
    query: str,
    limit: int,
) -> SearchRecordGroups:
    pattern = build_search_pattern(
        query.strip()
    )

    company_statement = (
        select(Company)
        .where(
            or_(
                Company.name.ilike(
                    pattern,
                    escape="\\",
                ),
                Company.industry.ilike(
                    pattern,
                    escape="\\",
                ),
                Company.email.ilike(
                    pattern,
                    escape="\\",
                ),
            )
        )
        .order_by(
            Company.name,
            Company.id,
        )
        .limit(limit)
    )

    contact_statement = (
        select(Contact)
        .where(
            or_(
                Contact.first_name.ilike(
                    pattern,
                    escape="\\",
                ),
                Contact.last_name.ilike(
                    pattern,
                    escape="\\",
                ),
                Contact.email.ilike(
                    pattern,
                    escape="\\",
                ),
                Contact.phone.ilike(
                    pattern,
                    escape="\\",
                ),
            )
        )
        .order_by(
            Contact.first_name,
            Contact.id,
        )
        .limit(limit)
    )

    lead_statement = (
        select(Lead)
        .where(
            or_(
                Lead.title.ilike(
                    pattern,
                    escape="\\",
                ),
                Lead.source.ilike(
                    pattern,
                    escape="\\",
                ),
                Lead.description.ilike(
                    pattern,
                    escape="\\",
                ),
            )
        )
        .order_by(
            Lead.created_at.desc(),
            Lead.id.desc(),
        )
        .limit(limit)
    )

    companies = db.scalars(
        company_statement
    ).all()
    contacts = db.scalars(
        contact_statement
    ).all()
    leads = db.scalars(
        lead_statement
    ).all()

    return companies, contacts, leads