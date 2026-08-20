from fastapi.testclient import TestClient


def test_create_lead_without_contact(
    authenticated_client: TestClient,
) -> None:
    company_response = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Lead Test Company",
        },
    )
    company_id = company_response.json()["id"]

    response = authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "Website Redesign",
            "company_id": company_id,
            "estimated_value": "2500.00",
        },
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["title"] == "Website Redesign"
    assert response_data["company_id"] == company_id
    assert response_data["contact_id"] is None
    assert response_data["stage"] == "New"


def test_create_lead_with_company_contact(
    authenticated_client: TestClient,
) -> None:
    company_response = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Lead Relationship Company",
        },
    )
    company_id = company_response.json()["id"]

    contact_response = authenticated_client.post(
        "/api/v1/contacts",
        json={
            "first_name": "Areeb",
            "company_id": company_id,
        },
    )
    contact_id = contact_response.json()["id"]

    response = authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "CRM Implementation",
            "company_id": company_id,
            "contact_id": contact_id,
            "stage": "Contacted",
        },
    )

    assert response.status_code == 201
    assert response.json()["company_id"] == company_id
    assert response.json()["contact_id"] == contact_id
    assert response.json()["stage"] == "Contacted"


def test_create_lead_rejects_missing_company(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "Missing Company Lead",
            "company_id": 999999,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Company not found",
    }


def test_create_lead_rejects_missing_contact(
    authenticated_client: TestClient,
) -> None:
    company_response = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Missing Contact Company",
        },
    )
    company_id = company_response.json()["id"]

    response = authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "Missing Contact Lead",
            "company_id": company_id,
            "contact_id": 999999,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Contact not found",
    }


def test_create_lead_rejects_contact_from_other_company(
    authenticated_client: TestClient,
) -> None:
    first_company_response = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "First Lead Company",
        },
    )
    first_company_id = first_company_response.json()["id"]

    second_company_response = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Second Lead Company",
        },
    )
    second_company_id = second_company_response.json()["id"]

    contact_response = authenticated_client.post(
        "/api/v1/contacts",
        json={
            "first_name": "Areeb",
            "company_id": first_company_id,
        },
    )
    contact_id = contact_response.json()["id"]

    response = authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "Invalid Relationship Lead",
            "company_id": second_company_id,
            "contact_id": contact_id,
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "Contact must belong to "
            "the lead company"
        ),
    }


def test_lead_endpoints_require_authentication(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/leads",
        json={
            "title": "Unauthorized Lead",
            "company_id": 1,
        },
    )

    assert response.status_code == 401