def test_manager_can_manage_companies(
    authenticated_client: TestClient,
) -> None:
    register_response = authenticated_client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Company Manager",
            "email": "company-manager@example.com",
            "password": "StrongPass123!",
        },
    )

    assert register_response.status_code == 201

    manager_id = register_response.json()["id"]

    role_response = authenticated_client.patch(
        f"/api/v1/users/{manager_id}",
        json={
            "role": "Manager",
        },
    )

    assert role_response.status_code == 200

    login_response = authenticated_client.post(
        "/api/v1/auth/login",
        data={
            "username": "company-manager@example.com",
            "password": "StrongPass123!",
        },
    )

    assert login_response.status_code == 200

    manager_token = login_response.json()[
        "access_token"
    ]

    authenticated_client.headers[
        "Authorization"
    ] = f"Bearer {manager_token}"

    create_response = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Manager Company",
        },
    )

    assert create_response.status_code == 201

    company_id = create_response.json()["id"]

    update_response = authenticated_client.patch(
        f"/api/v1/companies/{company_id}",
        json={
            "industry": "Managed Industry",
        },
    )

    assert update_response.status_code == 200

    delete_response = authenticated_client.delete(
        f"/api/v1/companies/{company_id}"
    )

    assert delete_response.status_code == 204


def test_member_has_read_only_company_access(
    authenticated_client: TestClient,
) -> None:
    company_response = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Read Only Company",
        },
    )

    assert company_response.status_code == 201

    company_id = company_response.json()["id"]

    register_response = authenticated_client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Company Member",
            "email": "company-member@example.com",
            "password": "StrongPass123!",
        },
    )

    assert register_response.status_code == 201
    assert register_response.json()["role"] == "Member"

    login_response = authenticated_client.post(
        "/api/v1/auth/login",
        data={
            "username": "company-member@example.com",
            "password": "StrongPass123!",
        },
    )

    assert login_response.status_code == 200

    member_token = login_response.json()[
        "access_token"
    ]

    authenticated_client.headers[
        "Authorization"
    ] = f"Bearer {member_token}"

    list_response = authenticated_client.get(
        "/api/v1/companies"
    )

    detail_response = authenticated_client.get(
        f"/api/v1/companies/{company_id}"
    )

    create_response = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Forbidden Company",
        },
    )

    update_response = authenticated_client.patch(
        f"/api/v1/companies/{company_id}",
        json={
            "industry": "Forbidden Industry",
        },
    )

    delete_response = authenticated_client.delete(
        f"/api/v1/companies/{company_id}"
    )

    assert list_response.status_code == 200
    assert detail_response.status_code == 200
    assert create_response.status_code == 403
    assert update_response.status_code == 403
    assert delete_response.status_code == 403

    assert create_response.json() == {
        "detail": (
            "You do not have permission "
            "to perform this action"
        )
    }