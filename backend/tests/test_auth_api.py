from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    decode_access_token,
    verify_password,
)
from app.models.user import User


def test_register_user(
    client: TestClient,
    db_session: Session,
) -> None:
    plain_password = "StrongPass123!"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "  Alex Morgan  ",
            "email": "ALEX@EXAMPLE.COM",
            "password": plain_password,
        },
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["full_name"] == "Alex Morgan"
    assert response_data["email"] == "alex@example.com"
    assert response_data["is_active"] is True
    assert "password" not in response_data
    assert "password_hash" not in response_data

    stored_user = db_session.scalar(
        select(User).where(
            User.email == "alex@example.com"
        )
    )

    assert stored_user is not None
    assert stored_user.password_hash != plain_password
    assert verify_password(
        plain_password,
        stored_user.password_hash,
    )


def test_register_rejects_duplicate_email(
    client: TestClient,
) -> None:
    first_response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "First User",
            "email": "USER@EXAMPLE.COM",
            "password": "StrongPass123!",
        },
    )

    second_response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Second User",
            "email": "user@example.com",
            "password": "AnotherPass123!",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Email is already registered",
    }


def test_register_rejects_invalid_data(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "A",
            "email": "invalid-email",
            "password": "short",
        },
    )

    assert response.status_code == 422

def test_login_returns_access_token(
    client: TestClient,
) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Login Test User",
            "email": "login@example.com",
            "password": "StrongPass123!",
        },
    )
    user_id = register_response.json()["id"]

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "LOGIN@EXAMPLE.COM",
            "password": "StrongPass123!",
        },
    )

    assert login_response.status_code == 200

    response_data = login_response.json()

    assert response_data["token_type"] == "bearer"
    assert response_data["access_token"]

    token_payload = decode_access_token(
        response_data["access_token"]
    )

    assert token_payload["sub"] == str(user_id)

def test_login_rejects_wrong_password(
    client: TestClient,
) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Wrong Password User",
            "email": "wrong-password@example.com",
            "password": "StrongPass123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "wrong-password@example.com",
            "password": "IncorrectPass123!",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Incorrect email or password",
    }
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_rejects_unknown_email(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "missing@example.com",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Incorrect email or password",
    }

def test_read_current_user(
    client: TestClient,
) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Current User",
            "email": "current@example.com",
            "password": "StrongPass123!",
        },
    )
    user_id = register_response.json()["id"]

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "current@example.com",
            "password": "StrongPass123!",
        },
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == user_id
    assert response.json()["email"] == "current@example.com"
    assert "password_hash" not in response.json()


def test_read_current_user_requires_token(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_read_current_user_rejects_invalid_token(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials",
    }