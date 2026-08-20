from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.schemas.contact import ContactCreate


def create_contact(
    db: Session,
    contact_data: ContactCreate,
) -> Contact:
    contact = Contact(
        **contact_data.model_dump()
    )

    db.add(contact)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(contact)
    return contact