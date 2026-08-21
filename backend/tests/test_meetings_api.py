from fastapi.testclient import TestClient


def test_create_minimal_meeting(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    response = authenticated_client.post(
        "/api/v1/meetings",
        json={
            "title": "Project discussion",
            "starts_at": "2026-08-25T10:00:00Z",
            "ends_at": "2026-08-25T11:00:00Z",
            "organizer_id": current_user["id"],
        },
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["title"] == "Project discussion"
    assert response_data["status"] == "Scheduled"
    assert (
        response_data["organizer_id"]
        == current_user["id"]
    )
    assert response_data["user_participant_ids"] == []
    assert response_data["contact_participant_ids"] == []


def test_create_meeting_with_participants(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Meeting Company"},
    ).json()

    contact = authenticated_client.post(
        "/api/v1/contacts",
        json={
            "first_name": "Client",
            "company_id": company["id"],
        },
    ).json()

    response = authenticated_client.post(
        "/api/v1/meetings",
        json={
            "title": "Client meeting",
            "starts_at": "2026-08-25T10:00:00Z",
            "ends_at": "2026-08-25T11:00:00Z",
            "organizer_id": current_user["id"],
            "company_id": company["id"],
            "user_participant_ids": [
                current_user["id"]
            ],
            "contact_participant_ids": [
                contact["id"]
            ],
        },
    )

    assert response.status_code == 201
    assert response.json()["company_id"] == company["id"]
    assert response.json()["user_participant_ids"] == [
        current_user["id"]
    ]
    assert response.json()["contact_participant_ids"] == [
        contact["id"]
    ]


def test_create_meeting_rejects_missing_organizer(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.post(
        "/api/v1/meetings",
        json={
            "title": "Missing organizer",
            "starts_at": "2026-08-25T10:00:00Z",
            "ends_at": "2026-08-25T11:00:00Z",
            "organizer_id": 999999,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Organizer not found",
    }


def test_create_meeting_rejects_missing_company(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    response = authenticated_client.post(
        "/api/v1/meetings",
        json={
            "title": "Missing company",
            "starts_at": "2026-08-25T10:00:00Z",
            "ends_at": "2026-08-25T11:00:00Z",
            "organizer_id": current_user["id"],
            "company_id": 999999,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Company not found",
    }


def test_create_meeting_rejects_missing_user_participant(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    response = authenticated_client.post(
        "/api/v1/meetings",
        json={
            "title": "Missing user participant",
            "starts_at": "2026-08-25T10:00:00Z",
            "ends_at": "2026-08-25T11:00:00Z",
            "organizer_id": current_user["id"],
            "user_participant_ids": [999999],
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": (
            "One or more user participants "
            "were not found"
        ),
    }


def test_create_meeting_rejects_missing_contact_participant(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    response = authenticated_client.post(
        "/api/v1/meetings",
        json={
            "title": "Missing contact participant",
            "starts_at": "2026-08-25T10:00:00Z",
            "ends_at": "2026-08-25T11:00:00Z",
            "organizer_id": current_user["id"],
            "contact_participant_ids": [999999],
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": (
            "One or more contact participants "
            "were not found"
        ),
    }


def test_create_meeting_rejects_invalid_time_range(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    response = authenticated_client.post(
        "/api/v1/meetings",
        json={
            "title": "Invalid meeting time",
            "starts_at": "2026-08-25T11:00:00Z",
            "ends_at": "2026-08-25T10:00:00Z",
            "organizer_id": current_user["id"],
        },
    )

    assert response.status_code == 422


def test_meeting_endpoints_require_authentication(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/meetings",
        json={
            "title": "Unauthorized meeting",
            "starts_at": "2026-08-25T10:00:00Z",
            "ends_at": "2026-08-25T11:00:00Z",
            "organizer_id": 1,
        },
    )

    assert response.status_code == 401