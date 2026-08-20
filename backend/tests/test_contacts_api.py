from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.contact import Contact


def test_create_contact_without_company(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.post(
        "/api/v1/contacts",
        json={
            "first_name": "Areeb",
            "email": "areeb@example.com",
        },
    )

    assert response.status_code == 201
    assert response.json()["first_name"] == "Areeb"
    assert response.json()["company_id"] is None


def test_create_contact_with_company(
    authenticated_client: TestClient,
    db_session: Session,
) -> None:
    company_response = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Relationship Test Company",
        },
    )
    company_id = company_response.json()["id"]

    contact_response = authenticated_client.post(
        "/api/v1/contacts",
        json={
            "first_name": "Areeb",
            "last_name": "Ahmed",
            "company_id": company_id,
        },
    )

    assert contact_response.status_code == 201
    assert contact_response.json()["company_id"] == company_id

    contact_id = contact_response.json()["id"]
    stored_contact = db_session.get(Contact, contact_id)

    assert stored_contact is not None
    assert stored_contact.company is not None
    assert stored_contact.company.name == (
        "Relationship Test Company"
    )
    assert stored_contact in stored_contact.company.contacts


def test_create_contact_rejects_missing_company(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.post(
        "/api/v1/contacts",
        json={
            "first_name": "Areeb",
            "company_id": 999999,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Company not found",
    }


def test_contact_endpoints_require_authentication(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/contacts",
        json={
            "first_name": "Areeb",
        },
    )

    assert response.status_code == 401