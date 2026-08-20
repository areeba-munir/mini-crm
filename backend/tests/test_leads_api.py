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

def test_list_leads_returns_empty_list(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/leads"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_leads_returns_newest_first(
    authenticated_client: TestClient,
) -> None:
    company_response = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Lead List Company",
        },
    )
    company_id = company_response.json()["id"]

    authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "First Lead",
            "company_id": company_id,
        },
    )
    authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "Second Lead",
            "company_id": company_id,
        },
    )

    response = authenticated_client.get(
        "/api/v1/leads"
    )

    assert response.status_code == 200
    assert [
        lead["title"] for lead in response.json()
    ] == [
        "Second Lead",
        "First Lead",
    ]


def test_get_lead(
    authenticated_client: TestClient,
) -> None:
    company_response = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Lead Detail Company",
        },
    )
    company_id = company_response.json()["id"]

    create_response = authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "Lead Detail Test",
            "company_id": company_id,
            "stage": "Qualified",
        },
    )
    lead_id = create_response.json()["id"]

    response = authenticated_client.get(
        f"/api/v1/leads/{lead_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == lead_id
    assert response.json()["title"] == "Lead Detail Test"
    assert response.json()["stage"] == "Qualified"


def test_get_missing_lead_returns_404(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/leads/999999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Lead not found",
    }

def test_update_lead_fields(
    authenticated_client: TestClient,
) -> None:
    company_response = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Lead Update Company"},
    )
    company_id = company_response.json()["id"]

    create_response = authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "Original Lead",
            "company_id": company_id,
        },
    )
    lead_id = create_response.json()["id"]

    response = authenticated_client.patch(
        f"/api/v1/leads/{lead_id}",
        json={
            "title": "Updated Lead",
            "stage": "Qualified",
            "description": "Updated description",
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Lead"
    assert response.json()["stage"] == "Qualified"
    assert (
        response.json()["description"]
        == "Updated description"
    )


def test_update_lead_can_change_company_when_contact_unlinked(
    authenticated_client: TestClient,
) -> None:
    first_company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Original Lead Company"},
    ).json()

    second_company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "New Lead Company"},
    ).json()

    contact = authenticated_client.post(
        "/api/v1/contacts",
        json={
            "first_name": "Areeb",
            "company_id": first_company["id"],
        },
    ).json()

    lead = authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "Movable Lead",
            "company_id": first_company["id"],
            "contact_id": contact["id"],
        },
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/leads/{lead['id']}",
        json={
            "company_id": second_company["id"],
            "contact_id": None,
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["company_id"]
        == second_company["id"]
    )
    assert response.json()["contact_id"] is None


def test_update_lead_rejects_missing_company(
    authenticated_client: TestClient,
) -> None:
    company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Valid Lead Company"},
    ).json()

    lead = authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "Lead Company Validation",
            "company_id": company["id"],
        },
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/leads/{lead['id']}",
        json={"company_id": 999999},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Company not found",
    }


def test_update_lead_rejects_missing_contact(
    authenticated_client: TestClient,
) -> None:
    company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Contact Validation Company"},
    ).json()

    lead = authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "Lead Contact Validation",
            "company_id": company["id"],
        },
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/leads/{lead['id']}",
        json={"contact_id": 999999},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Contact not found",
    }


def test_update_lead_rejects_contact_from_other_company(
    authenticated_client: TestClient,
) -> None:
    first_company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Lead Company One"},
    ).json()

    second_company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Lead Company Two"},
    ).json()

    contact = authenticated_client.post(
        "/api/v1/contacts",
        json={
            "first_name": "Areeb",
            "company_id": first_company["id"],
        },
    ).json()

    lead = authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "Relationship Update Lead",
            "company_id": first_company["id"],
            "contact_id": contact["id"],
        },
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/leads/{lead['id']}",
        json={"company_id": second_company["id"]},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "Contact must belong to "
            "the lead company"
        ),
    }


def test_update_lead_returns_404_when_missing(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.patch(
        "/api/v1/leads/999999",
        json={"stage": "Contacted"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Lead not found",
    }
def test_delete_lead(
    authenticated_client: TestClient,
) -> None:
    company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Lead Delete Company"},
    ).json()

    lead = authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "Temporary Lead",
            "company_id": company["id"],
        },
    ).json()

    delete_response = authenticated_client.delete(
        f"/api/v1/leads/{lead['id']}"
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = authenticated_client.get(
        f"/api/v1/leads/{lead['id']}"
    )

    assert get_response.status_code == 404


def test_delete_missing_lead_returns_404(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.delete(
        "/api/v1/leads/999999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Lead not found",
    }

def test_list_leads_filters_by_stage(
    authenticated_client: TestClient,
) -> None:
    company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Pipeline Filter Company"},
    ).json()

    for title, stage in [
        ("New Lead", "New"),
        ("Qualified Lead", "Qualified"),
        ("Won Lead", "Won"),
    ]:
        authenticated_client.post(
            "/api/v1/leads",
            json={
                "title": title,
                "company_id": company["id"],
                "stage": stage,
            },
        )

    response = authenticated_client.get(
        "/api/v1/leads",
        params={"stage": "Qualified"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Qualified Lead"
    assert response.json()[0]["stage"] == "Qualified"


def test_list_leads_rejects_invalid_stage_filter(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/leads",
        params={"stage": "Invalid"},
    )

    assert response.status_code == 422