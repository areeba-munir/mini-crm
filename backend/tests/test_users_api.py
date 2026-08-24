from fastapi.testclient import TestClient


def register_user(
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


def login_user(
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


def test_first_user_is_admin_and_later_user_is_member(
    client: TestClient,
) -> None:
    first_user = register_user(
        client,
        full_name="First User",
        email="first-user@example.com",
    )

    second_user = register_user(
        client,
        full_name="Second User",
        email="second-user@example.com",
    )

    assert first_user["role"] == "Admin"
    assert second_user["role"] == "Member"


def test_admin_can_list_users(
    authenticated_client: TestClient,
) -> None:
    register_user(
        authenticated_client,
        full_name="Team Member",
        email="team-member@example.com",
    )

    response = authenticated_client.get(
        "/api/v1/users"
    )

    assert response.status_code == 200

    users = response.json()

    assert len(users) == 2
    assert users[0]["role"] == "Admin"
    assert users[1]["role"] == "Member"


def test_admin_can_change_role_and_status(
    authenticated_client: TestClient,
) -> None:
    member = register_user(
        authenticated_client,
        full_name="Managed User",
        email="managed-user@example.com",
    )

    role_response = authenticated_client.patch(
        f"/api/v1/users/{member['id']}",
        json={
            "role": "Manager",
        },
    )

    assert role_response.status_code == 200
    assert role_response.json()["role"] == "Manager"

    status_response = authenticated_client.patch(
        f"/api/v1/users/{member['id']}",
        json={
            "is_active": False,
        },
    )

    assert status_response.status_code == 200
    assert status_response.json()["is_active"] is False


def test_member_cannot_manage_users(
    authenticated_client: TestClient,
) -> None:
    admin = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    member = register_user(
        authenticated_client,
        full_name="Restricted Member",
        email="restricted-member@example.com",
    )

    member_token = login_user(
        authenticated_client,
        email="restricted-member@example.com",
    )

    authenticated_client.headers[
        "Authorization"
    ] = f"Bearer {member_token}"

    list_response = authenticated_client.get(
        "/api/v1/users"
    )

    update_response = authenticated_client.patch(
        f"/api/v1/users/{admin['id']}",
        json={
            "role": "Member",
        },
    )

    assert list_response.status_code == 403
    assert update_response.status_code == 403
    assert member["role"] == "Member"


def test_admin_cannot_remove_own_role(
    authenticated_client: TestClient,
) -> None:
    admin = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/users/{admin['id']}",
        json={
            "role": "Member",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            "You cannot remove your own "
            "administrator role"
        )
    }


def test_admin_cannot_deactivate_self(
    authenticated_client: TestClient,
) -> None:
    admin = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/users/{admin['id']}",
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            "You cannot deactivate your "
            "own account"
        )
    }


def test_user_management_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/users"
    )

    assert response.status_code == 401