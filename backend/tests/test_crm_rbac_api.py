from fastapi.testclient import TestClient


def create_account(
    client: TestClient,
    *,
    full_name: str,
    email: str,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 201
    return response.json()


def login_account(
    client: TestClient,
    *,
    email: str,
) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 200
    return response.json()["access_token"]


def use_token(
    client: TestClient,
    token: str,
) -> None:
    client.headers["Authorization"] = (
        f"Bearer {token}"
    )


def test_manager_can_manage_core_crm_records(
    authenticated_client: TestClient,
) -> None:
    manager = create_account(
        authenticated_client,
        full_name="CRM Manager",
        email="crm-manager@example.com",
    )

    role_response = authenticated_client.patch(
        f"/api/v1/users/{manager['id']}",
        json={
            "role": "Manager",
        },
    )

    assert role_response.status_code == 200

    manager_token = login_account(
        authenticated_client,
        email="crm-manager@example.com",
    )

    use_token(
        authenticated_client,
        manager_token,
    )

    company_response = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Manager CRM Company",
        },
    )

    assert company_response.status_code == 201
    company_id = company_response.json()["id"]

    contact_response = authenticated_client.post(
        "/api/v1/contacts",
        json={
            "first_name": "Manager",
            "last_name": "Contact",
            "company_id": company_id,
        },
    )

    assert contact_response.status_code == 201
    contact_id = contact_response.json()["id"]

    lead_response = authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "Manager Lead",
            "company_id": company_id,
            "contact_id": contact_id,
        },
    )

    assert lead_response.status_code == 201
    lead_id = lead_response.json()["id"]

    assert authenticated_client.patch(
        f"/api/v1/contacts/{contact_id}",
        json={
            "job_title": "Decision Maker",
        },
    ).status_code == 200

    assert authenticated_client.patch(
        f"/api/v1/leads/{lead_id}",
        json={
            "stage": "Qualified",
        },
    ).status_code == 200

    assert authenticated_client.delete(
        f"/api/v1/leads/{lead_id}"
    ).status_code == 204

    assert authenticated_client.delete(
        f"/api/v1/contacts/{contact_id}"
    ).status_code == 204

    assert authenticated_client.delete(
        f"/api/v1/companies/{company_id}"
    ).status_code == 204


def test_member_can_read_but_cannot_modify_core_crm(
    authenticated_client: TestClient,
) -> None:
    company = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Member Read Company",
        },
    ).json()

    contact = authenticated_client.post(
        "/api/v1/contacts",
        json={
            "first_name": "Readable",
            "last_name": "Contact",
            "company_id": company["id"],
        },
    ).json()

    lead = authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "Readable Lead",
            "company_id": company["id"],
            "contact_id": contact["id"],
        },
    ).json()

    create_account(
        authenticated_client,
        full_name="CRM Member",
        email="crm-member@example.com",
    )

    member_token = login_account(
        authenticated_client,
        email="crm-member@example.com",
    )

    use_token(
        authenticated_client,
        member_token,
    )

    assert authenticated_client.get(
        "/api/v1/companies"
    ).status_code == 200

    assert authenticated_client.get(
        "/api/v1/contacts"
    ).status_code == 200

    assert authenticated_client.get(
        "/api/v1/leads"
    ).status_code == 200

    forbidden_responses = [
        authenticated_client.post(
            "/api/v1/companies",
            json={
                "name": "Forbidden Company",
            },
        ),
        authenticated_client.patch(
            f"/api/v1/companies/{company['id']}",
            json={
                "industry": "Forbidden",
            },
        ),
        authenticated_client.delete(
            f"/api/v1/companies/{company['id']}"
        ),
        authenticated_client.post(
            "/api/v1/contacts",
            json={
                "first_name": "Forbidden",
            },
        ),
        authenticated_client.patch(
            f"/api/v1/contacts/{contact['id']}",
            json={
                "job_title": "Forbidden",
            },
        ),
        authenticated_client.delete(
            f"/api/v1/contacts/{contact['id']}"
        ),
        authenticated_client.post(
            "/api/v1/leads",
            json={
                "title": "Forbidden Lead",
                "company_id": company["id"],
            },
        ),
        authenticated_client.patch(
            f"/api/v1/leads/{lead['id']}",
            json={
                "stage": "Won",
            },
        ),
        authenticated_client.delete(
            f"/api/v1/leads/{lead['id']}"
        ),
    ]

    assert all(
        response.status_code == 403
        for response in forbidden_responses
    )

    assert forbidden_responses[0].json() == {
        "detail": (
            "You do not have permission "
            "to perform this action"
        )
    }