from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.meeting import (
    meeting_contact_participants,
    meeting_user_participants,
)


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

def test_list_meetings_returns_empty_list(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/meetings"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_meetings_filters_status_and_company(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    first_company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "First Meeting Company"},
    ).json()

    second_company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Second Meeting Company"},
    ).json()

    for title, meeting_status, company_id in [
        (
            "Scheduled First",
            "Scheduled",
            first_company["id"],
        ),
        (
            "Completed First",
            "Completed",
            first_company["id"],
        ),
        (
            "Completed Second",
            "Completed",
            second_company["id"],
        ),
    ]:
        authenticated_client.post(
            "/api/v1/meetings",
            json={
                "title": title,
                "starts_at": (
                    "2026-08-25T10:00:00Z"
                ),
                "ends_at": (
                    "2026-08-25T11:00:00Z"
                ),
                "organizer_id": current_user["id"],
                "company_id": company_id,
                "status": meeting_status,
            },
        )

    response = authenticated_client.get(
        "/api/v1/meetings",
        params={
            "status": "Completed",
            "company_id": first_company["id"],
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert (
        response.json()[0]["title"]
        == "Completed First"
    )


def test_list_meetings_filters_date_range(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    for day in [25, 26, 27]:
        authenticated_client.post(
            "/api/v1/meetings",
            json={
                "title": f"Meeting {day}",
                "starts_at": (
                    f"2026-08-{day}T10:00:00Z"
                ),
                "ends_at": (
                    f"2026-08-{day}T11:00:00Z"
                ),
                "organizer_id": current_user["id"],
            },
        )

    response = authenticated_client.get(
        "/api/v1/meetings",
        params={
            "starts_from": (
                "2026-08-26T00:00:00Z"
            ),
            "starts_to": (
                "2026-08-26T23:59:59Z"
            ),
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Meeting 26"


def test_get_meeting_includes_participants(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    contact = authenticated_client.post(
        "/api/v1/contacts",
        json={"first_name": "Meeting Client"},
    ).json()

    meeting = authenticated_client.post(
        "/api/v1/meetings",
        json={
            "title": "Meeting Detail",
            "starts_at": "2026-08-25T10:00:00Z",
            "ends_at": "2026-08-25T11:00:00Z",
            "organizer_id": current_user["id"],
            "user_participant_ids": [
                current_user["id"]
            ],
            "contact_participant_ids": [
                contact["id"]
            ],
        },
    ).json()

    response = authenticated_client.get(
        f"/api/v1/meetings/{meeting['id']}"
    )

    assert response.status_code == 200
    assert response.json()["user_participant_ids"] == [
        current_user["id"]
    ]
    assert response.json()[
        "contact_participant_ids"
    ] == [contact["id"]]


def test_get_missing_meeting_returns_404(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/meetings/999999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Meeting not found",
    }


def test_list_meetings_rejects_invalid_date_range(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/meetings",
        params={
            "starts_from": (
                "2026-08-27T00:00:00Z"
            ),
            "starts_to": (
                "2026-08-26T00:00:00Z"
            ),
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "starts_to cannot be earlier "
            "than starts_from"
        ),
    }

def test_update_meeting_fields(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    meeting = authenticated_client.post(
        "/api/v1/meetings",
        json={
            "title": "Original Meeting",
            "starts_at": "2026-08-25T10:00:00Z",
            "ends_at": "2026-08-25T11:00:00Z",
            "organizer_id": current_user["id"],
        },
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/meetings/{meeting['id']}",
        json={
            "title": "Updated Meeting",
            "status": "Completed",
            "location": "Conference Room",
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Meeting"
    assert response.json()["status"] == "Completed"
    assert (
        response.json()["location"]
        == "Conference Room"
    )


def test_update_meeting_validates_combined_time_range(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    meeting = authenticated_client.post(
        "/api/v1/meetings",
        json={
            "title": "Time Validation Meeting",
            "starts_at": "2026-08-25T10:00:00Z",
            "ends_at": "2026-08-25T11:00:00Z",
            "organizer_id": current_user["id"],
        },
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/meetings/{meeting['id']}",
        json={
            "starts_at": "2026-08-25T12:00:00Z",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Meeting end must be after start",
    }


def test_update_meeting_replaces_participants(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    first_contact = authenticated_client.post(
        "/api/v1/contacts",
        json={"first_name": "First Participant"},
    ).json()

    second_contact = authenticated_client.post(
        "/api/v1/contacts",
        json={"first_name": "Second Participant"},
    ).json()

    meeting = authenticated_client.post(
        "/api/v1/meetings",
        json={
            "title": "Participant Update Meeting",
            "starts_at": "2026-08-25T10:00:00Z",
            "ends_at": "2026-08-25T11:00:00Z",
            "organizer_id": current_user["id"],
            "user_participant_ids": [
                current_user["id"]
            ],
            "contact_participant_ids": [
                first_contact["id"]
            ],
        },
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/meetings/{meeting['id']}",
        json={
            "user_participant_ids": [],
            "contact_participant_ids": [
                second_contact["id"]
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["user_participant_ids"] == []
    assert response.json()[
        "contact_participant_ids"
    ] == [second_contact["id"]]


def test_update_meeting_rejects_missing_organizer(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    meeting = authenticated_client.post(
        "/api/v1/meetings",
        json={
            "title": "Organizer Validation Meeting",
            "starts_at": "2026-08-25T10:00:00Z",
            "ends_at": "2026-08-25T11:00:00Z",
            "organizer_id": current_user["id"],
        },
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/meetings/{meeting['id']}",
        json={"organizer_id": 999999},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Organizer not found",
    }


def test_update_meeting_rejects_missing_company(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    meeting = authenticated_client.post(
        "/api/v1/meetings",
        json={
            "title": "Company Validation Meeting",
            "starts_at": "2026-08-25T10:00:00Z",
            "ends_at": "2026-08-25T11:00:00Z",
            "organizer_id": current_user["id"],
        },
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/meetings/{meeting['id']}",
        json={"company_id": 999999},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Company not found",
    }


def test_update_meeting_rejects_missing_user_participant(
    authenticated_client: TestClient,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    meeting = authenticated_client.post(
        "/api/v1/meetings",
        json={
            "title": "Participant Validation Meeting",
            "starts_at": "2026-08-25T10:00:00Z",
            "ends_at": "2026-08-25T11:00:00Z",
            "organizer_id": current_user["id"],
        },
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/meetings/{meeting['id']}",
        json={"user_participant_ids": [999999]},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": (
            "One or more user participants "
            "were not found"
        ),
    }


def test_update_meeting_returns_404_when_missing(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.patch(
        "/api/v1/meetings/999999",
        json={"status": "Cancelled"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Meeting not found",
    }
def test_delete_meeting_removes_participant_rows(
    authenticated_client: TestClient,
    db_session: Session,
) -> None:
    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    contact = authenticated_client.post(
        "/api/v1/contacts",
        json={"first_name": "Delete Participant"},
    ).json()

    meeting = authenticated_client.post(
        "/api/v1/meetings",
        json={
            "title": "Temporary Meeting",
            "starts_at": "2026-08-25T10:00:00Z",
            "ends_at": "2026-08-25T11:00:00Z",
            "organizer_id": current_user["id"],
            "user_participant_ids": [
                current_user["id"]
            ],
            "contact_participant_ids": [
                contact["id"]
            ],
        },
    ).json()

    delete_response = authenticated_client.delete(
        f"/api/v1/meetings/{meeting['id']}"
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = authenticated_client.get(
        f"/api/v1/meetings/{meeting['id']}"
    )

    assert get_response.status_code == 404

    user_rows = db_session.scalar(
        select(func.count())
        .select_from(meeting_user_participants)
        .where(
            meeting_user_participants.c.meeting_id
            == meeting["id"]
        )
    )
    contact_rows = db_session.scalar(
        select(func.count())
        .select_from(
            meeting_contact_participants
        )
        .where(
            meeting_contact_participants.c.meeting_id
            == meeting["id"]
        )
    )

    assert user_rows == 0
    assert contact_rows == 0


def test_delete_missing_meeting_returns_404(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.delete(
        "/api/v1/meetings/999999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Meeting not found",
    }