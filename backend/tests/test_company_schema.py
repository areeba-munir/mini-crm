import pytest
from pydantic import ValidationError
from datetime import UTC, datetime

from app.models.company import Company

from app.schemas.company import CompanyCreate, CompanyRead


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