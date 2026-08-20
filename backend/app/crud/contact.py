from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.schemas.contact import (
    ContactCreate,
    ContactUpdate,
)


def create_contact(
    db: Session,
    contact_data: ContactCreate,
) -> Contact:
    contact = Contact(**contact_data.model_dump())

    db.add(contact)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(contact)
    return contact


def list_contacts(
    db: Session,
) -> Sequence[Contact]:
    statement = select(Contact).order_by(
        Contact.first_name,
        Contact.id,
    )

    return db.scalars(statement).all()


def get_contact(
    db: Session,
    contact_id: int,
) -> Contact | None:
    return db.get(Contact, contact_id)


def update_contact(
    db: Session,
    contact: Contact,
    contact_data: ContactUpdate,
) -> Contact:
    update_data = contact_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(contact, field, value)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(contact)
    return contact

def delete_contact(
    db: Session,
    contact: Contact,
) -> None:
    db.delete(contact)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise