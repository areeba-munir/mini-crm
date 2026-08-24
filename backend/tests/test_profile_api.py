from fastapi.testclient import TestClient


def test_update_current_user_profile(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.patch(
        "/api/v1/auth/me",
        json={
            "full_name": "  Updated User  ",
            "email": "UPDATED@EXAMPLE.COM",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["full_name"] == (
        "Updated User"
    )
    assert response_data["email"] == (
        "updated@example.com"
    )
    assert "password_hash" not in response_data

    current_user_response = (
        authenticated_client.get(
            "/api/v1/auth/me"
        )
    )

    assert current_user_response.status_code == 200
    assert (
        current_user_response.json()["full_name"]
        == "Updated User"
    )
    assert (
        current_user_response.json()["email"]
        == "updated@example.com"
    )


def test_update_current_user_name_only(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.patch(
        "/api/v1/auth/me",
        json={
            "full_name": "Profile Name",
        },
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == (
        "Profile Name"
    )
    assert response.json()["email"] == (
        "company-tests@example.com"
    )


def test_update_profile_rejects_empty_body(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.patch(
        "/api/v1/auth/me",
        json={},
    )

    assert response.status_code == 422


def test_update_profile_rejects_duplicate_email(
    authenticated_client: TestClient,
) -> None:
    register_response = authenticated_client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Existing User",
            "email": "existing@example.com",
            "password": "ExistingPass123!",
        },
    )

    assert register_response.status_code == 201

    response = authenticated_client.patch(
        "/api/v1/auth/me",
        json={
            "email": "EXISTING@EXAMPLE.COM",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Email is already registered",
    }


def test_change_current_user_password(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.patch(
        "/api/v1/auth/me/password",
        json={
            "current_password": "StrongPass123!",
            "new_password": "NewStrongPass456!",
        },
    )

    assert response.status_code == 204
    assert response.content == b""

    old_password_login = authenticated_client.post(
        "/api/v1/auth/login",
        data={
            "username": "company-tests@example.com",
            "password": "StrongPass123!",
        },
    )

    assert old_password_login.status_code == 401

    new_password_login = authenticated_client.post(
        "/api/v1/auth/login",
        data={
            "username": "company-tests@example.com",
            "password": "NewStrongPass456!",
        },
    )

    assert new_password_login.status_code == 200
    assert "access_token" in new_password_login.json()


def test_change_password_rejects_wrong_current_password(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.patch(
        "/api/v1/auth/me/password",
        json={
            "current_password": "WrongPass123!",
            "new_password": "NewStrongPass456!",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Current password is incorrect",
    }

    login_response = authenticated_client.post(
        "/api/v1/auth/login",
        data={
            "username": "company-tests@example.com",
            "password": "StrongPass123!",
        },
    )

    assert login_response.status_code == 200


def test_change_password_rejects_same_password(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.patch(
        "/api/v1/auth/me/password",
        json={
            "current_password": "StrongPass123!",
            "new_password": "StrongPass123!",
        },
    )

    assert response.status_code == 422


def test_profile_endpoints_require_authentication(
    client: TestClient,
) -> None:
    update_response = client.patch(
        "/api/v1/auth/me",
        json={
            "full_name": "Unauthorized User",
        },
    )

    password_response = client.patch(
        "/api/v1/auth/me/password",
        json={
            "current_password": "StrongPass123!",
            "new_password": "NewStrongPass456!",
        },
    )

    assert update_response.status_code == 401
    assert password_response.status_code == 401