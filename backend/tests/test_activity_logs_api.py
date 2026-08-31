from fastapi.testclient import TestClient


def register_account(
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


def test_company_changes_create_activity_logs(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    create_response = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Activity Company",
        },
    )

    assert create_response.status_code == 201
    company_id = create_response.json()["id"]

    update_response = authenticated_client.patch(
        f"/api/v1/companies/{company_id}",
        json={
            "industry": "Activity Industry",
        },
    )

    assert update_response.status_code == 200

    delete_response = authenticated_client.delete(
        f"/api/v1/companies/{company_id}"
    )

    assert delete_response.status_code == 204

    response = authenticated_client.get(
        "/api/v1/activities",
        params={
            "entity_type": "Company",
        },
    )

    assert response.status_code == 200

    activities = response.json()

    assert len(activities) == 3
    assert [
        activity["action"]
        for activity in activities
    ] == [
        "Deleted",
        "Updated",
        "Created",
    ]

    assert all(
        activity["entity_type"] == "Company"
        for activity in activities
    )

    assert all(
        activity["entity_id"] == company_id
        for activity in activities
    )

    assert all(
        activity["actor_id"] == current_user["id"]
        for activity in activities
    )

    assert all(
        activity["actor"]["full_name"]
        == current_user["full_name"]
        for activity in activities
    )

    update_activity = activities[1]

    assert "industry" in (
        update_activity["details"]["fields"]
    )


def test_activity_logs_support_action_filter(
    authenticated_client: TestClient,
) -> None:
    authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Filtered Activity Company",
        },
    )

    response = authenticated_client.get(
        "/api/v1/activities",
        params={
            "action": "Created",
        },
    )

    assert response.status_code == 200

    activities = response.json()

    assert len(activities) == 1
    assert activities[0]["action"] == "Created"


def test_manager_can_view_activity_logs(
    authenticated_client: TestClient,
) -> None:
    manager = register_account(
        authenticated_client,
        full_name="Activity Manager",
        email="activity-manager@example.com",
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
        email="activity-manager@example.com",
    )

    authenticated_client.headers[
        "Authorization"
    ] = f"Bearer {manager_token}"

    response = authenticated_client.get(
        "/api/v1/activities"
    )

    assert response.status_code == 200


def test_member_cannot_view_activity_logs(
    authenticated_client: TestClient,
) -> None:
    register_account(
        authenticated_client,
        full_name="Activity Member",
        email="activity-member@example.com",
    )

    member_token = login_account(
        authenticated_client,
        email="activity-member@example.com",
    )

    authenticated_client.headers[
        "Authorization"
    ] = f"Bearer {member_token}"

    response = authenticated_client.get(
        "/api/v1/activities"
    )

    assert response.status_code == 403


def test_activity_logs_require_authentication(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/activities"
    )

    assert response.status_code == 401