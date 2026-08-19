import pytest
from pydantic import ValidationError
from datetime import UTC, datetime

from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate


def test_company_create_strips_name_whitespace() -> None:
    company = CompanyCreate(name="  Acme Ltd  ")

    assert company.name == "Acme Ltd"


def test_company_create_rejects_blank_name() -> None:
    with pytest.raises(ValidationError):
        CompanyCreate(name="   ")

def test_company_read_accepts_sqlalchemy_model() -> None:
    now = datetime.now(UTC)
    company = Company(
        id=1,
        name="Acme Ltd",
        created_at=now,
        updated_at=now,
    )

    response = CompanyRead.model_validate(company)

    assert response.id == 1
    assert response.name == "Acme Ltd"
    assert response.created_at == now

def test_company_update_includes_only_provided_fields() -> None:
    update = CompanyUpdate(industry="Business Software")

    assert update.model_dump(exclude_unset=True) == {
        "industry": "Business Software",
    }


def test_company_update_rejects_blank_name() -> None:
    with pytest.raises(ValidationError):
        CompanyUpdate(name="   ")


def test_company_update_rejects_null_name() -> None:
    with pytest.raises(ValidationError):
        CompanyUpdate(name=None)