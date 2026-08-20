from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.contact import Contact
from app.schemas.contact import (
    ContactCreate,
    ContactRead,
    ContactUpdate,
)


def test_contact_create_normalizes_input() -> None:
    contact = ContactCreate(
        first_name="  Areeb  ",
        email="AREEB@EXAMPLE.COM",
    )

    assert contact.first_name == "Areeb"
    assert str(contact.email) == "areeb@example.com"


def test_contact_create_rejects_blank_first_name() -> None:
    with pytest.raises(ValidationError):
        ContactCreate(first_name="   ")


def test_contact_create_rejects_invalid_company_id() -> None:
    with pytest.raises(ValidationError):
        ContactCreate(
            first_name="Areeb",
            company_id=0,
        )


def test_contact_update_includes_only_supplied_fields() -> None:
    update = ContactUpdate(company_id=None)

    assert update.model_dump(exclude_unset=True) == {
        "company_id": None,
    }


def test_contact_update_rejects_null_first_name() -> None:
    with pytest.raises(ValidationError):
        ContactUpdate(first_name=None)


def test_contact_read_accepts_sqlalchemy_model() -> None:
    now = datetime.now(UTC)
    contact = Contact(
        id=1,
        first_name="Areeb",
        created_at=now,
        updated_at=now,
    )

    response = ContactRead.model_validate(contact)

    assert response.id == 1
    assert response.first_name == "Areeb"