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

def test_list_tasks_returns_empty_list(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/tasks"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_filters_status_and_priority(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    for title, task_status, priority in [
        ("Pending High", "Pending", "High"),
        ("Completed High", "Completed", "High"),
        ("Pending Low", "Pending", "Low"),
    ]:
        authenticated_client.post(
            "/api/v1/tasks",
            json={
                "title": title,
                "assigned_to_id": current_user["id"],
                "status": task_status,
                "priority": priority,
            },
        )

    response = authenticated_client.get(
        "/api/v1/tasks",
        params={
            "status": "Pending",
            "priority": "High",
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Pending High"


def test_get_task(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    task = authenticated_client.post(
        "/api/v1/tasks",
        json={
            "title": "Task Detail Test",
            "assigned_to_id": current_user["id"],
        },
    ).json()

    response = authenticated_client.get(
        f"/api/v1/tasks/{task['id']}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == task["id"]
    assert response.json()["title"] == "Task Detail Test"


def test_get_missing_task_returns_404(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/tasks/999999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Task not found",
    }

def test_update_task_fields(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    task = authenticated_client.post(
        "/api/v1/tasks",
        json={
            "title": "Original Task",
            "assigned_to_id": current_user["id"],
        },
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={
            "title": "Updated Task",
            "priority": "High",
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Task"
    assert response.json()["priority"] == "High"


def test_update_task_sets_completed_at(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    task = authenticated_client.post(
        "/api/v1/tasks",
        json={
            "title": "Complete this task",
            "assigned_to_id": current_user["id"],
        },
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"status": "Completed"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Completed"
    assert response.json()["completed_at"] is not None


def test_update_task_clears_completed_at_when_reopened(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    task = authenticated_client.post(
        "/api/v1/tasks",
        json={
            "title": "Reopen this task",
            "assigned_to_id": current_user["id"],
            "status": "Completed",
        },
    ).json()

    assert task["completed_at"] is not None

    response = authenticated_client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"status": "In Progress"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "In Progress"
    assert response.json()["completed_at"] is None


def test_update_task_can_switch_related_entity(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Task Relationship Company"},
    ).json()

    contact = authenticated_client.post(
        "/api/v1/contacts",
        json={
            "first_name": "Areeb",
            "company_id": company["id"],
        },
    ).json()

    task = authenticated_client.post(
        "/api/v1/tasks",
        json={
            "title": "Switch relationship",
            "assigned_to_id": current_user["id"],
            "company_id": company["id"],
        },
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={
            "company_id": None,
            "contact_id": contact["id"],
        },
    )

    assert response.status_code == 200
    assert response.json()["company_id"] is None
    assert response.json()["contact_id"] == contact["id"]


def test_update_task_rejects_multiple_related_entities(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Invalid Task Relationship"},
    ).json()

    contact = authenticated_client.post(
        "/api/v1/contacts",
        json={
            "first_name": "Areeb",
            "company_id": company["id"],
        },
    ).json()

    task = authenticated_client.post(
        "/api/v1/tasks",
        json={
            "title": "Invalid update task",
            "assigned_to_id": current_user["id"],
            "company_id": company["id"],
        },
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"contact_id": contact["id"]},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "A task may relate to at most one "
            "company, contact, or lead"
        ),
    }


def test_update_task_rejects_missing_assigned_user(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    task = authenticated_client.post(
        "/api/v1/tasks",
        json={
            "title": "Reassignment task",
            "assigned_to_id": current_user["id"],
        },
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"assigned_to_id": 999999},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Assigned user not found",
    }


def test_update_task_returns_404_when_missing(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.patch(
        "/api/v1/tasks/999999",
        json={"priority": "High"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Task not found",
    }