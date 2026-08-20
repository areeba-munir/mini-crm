from fastapi.testclient import TestClient


def test_create_general_task(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    response = authenticated_client.post(
        "/api/v1/tasks",
        json={
            "title": "Call customer",
            "assigned_to_id": current_user["id"],
        },
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["title"] == "Call customer"
    assert response_data["status"] == "Pending"
    assert response_data["priority"] == "Medium"
    assert (
        response_data["assigned_to_id"]
        == current_user["id"]
    )
    assert (
        response_data["created_by_id"]
        == current_user["id"]
    )
    assert response_data["completed_at"] is None


def test_create_completed_task_sets_completed_at(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    response = authenticated_client.post(
        "/api/v1/tasks",
        json={
            "title": "Already completed task",
            "assigned_to_id": current_user["id"],
            "status": "Completed",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "Completed"
    assert response.json()["completed_at"] is not None


def test_create_task_related_to_company(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Task Company"},
    ).json()

    response = authenticated_client.post(
        "/api/v1/tasks",
        json={
            "title": "Company follow-up",
            "assigned_to_id": current_user["id"],
            "company_id": company["id"],
        },
    )

    assert response.status_code == 201
    assert response.json()["company_id"] == company["id"]
    assert response.json()["contact_id"] is None
    assert response.json()["lead_id"] is None


def test_create_task_rejects_missing_assigned_user(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.post(
        "/api/v1/tasks",
        json={
            "title": "Missing assignee",
            "assigned_to_id": 999999,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Assigned user not found",
    }


def test_create_task_rejects_missing_company(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    response = authenticated_client.post(
        "/api/v1/tasks",
        json={
            "title": "Missing company",
            "assigned_to_id": current_user["id"],
            "company_id": 999999,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Company not found",
    }


def test_create_task_rejects_multiple_related_entities(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    response = authenticated_client.post(
        "/api/v1/tasks",
        json={
            "title": "Invalid relationships",
            "assigned_to_id": current_user["id"],
            "company_id": 1,
            "contact_id": 1,
        },
    )

    assert response.status_code == 422


def test_task_endpoints_require_authentication(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Unauthorized task",
            "assigned_to_id": 1,
        },
    )

    assert response.status_code == 401