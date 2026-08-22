from fastapi.testclient import TestClient
def create_second_user_headers(
    client: TestClient,
) -> dict[str, str]:
    email = "second-note-user@example.com"
    password = "SecondNotePass123!"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Second Note User",
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()[
        "access_token"
    ]

    return {
        "Authorization": f"Bearer {access_token}",
    }

def test_list_notes_returns_empty_list(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/notes"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_notes_returns_saved_notes_newest_first(
    authenticated_client: TestClient,
) -> None:
    company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Note List Company"},
    ).json()

    authenticated_client.post(
        "/api/v1/notes",
        json={
            "body": "First note",
            "company_id": company["id"],
        },
    )
    authenticated_client.post(
        "/api/v1/notes",
        json={
            "body": "Second note",
            "company_id": company["id"],
        },
    )

    response = authenticated_client.get(
        "/api/v1/notes"
    )

    assert response.status_code == 200
    assert [
        note["body"] for note in response.json()
    ] == [
        "Second note",
        "First note",
    ]


def test_get_note(
    authenticated_client: TestClient,
) -> None:
    company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Note Detail Company"},
    ).json()

    note = authenticated_client.post(
        "/api/v1/notes",
        json={
            "body": "Important customer information",
            "company_id": company["id"],
        },
    ).json()

    response = authenticated_client.get(
        f"/api/v1/notes/{note['id']}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == note["id"]
    assert (
        response.json()["body"]
        == "Important customer information"
    )


def test_get_missing_note_returns_404(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/notes/999999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Note not found",
    }

def test_update_own_note(
    authenticated_client: TestClient,
) -> None:
    company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Note Update Company"},
    ).json()

    note = authenticated_client.post(
        "/api/v1/notes",
        json={
            "body": "Original note",
            "company_id": company["id"],
        },
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/notes/{note['id']}",
        json={"body": "Updated note"},
    )

    assert response.status_code == 200
    assert response.json()["body"] == "Updated note"
    assert response.json()["author_id"] == note["author_id"]


def test_update_other_users_note_returns_403(
    authenticated_client: TestClient,
) -> None:
    company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Protected Note Company"},
    ).json()

    note = authenticated_client.post(
        "/api/v1/notes",
        json={
            "body": "Author-owned note",
            "company_id": company["id"],
        },
    ).json()

    second_user_headers = create_second_user_headers(
        authenticated_client
    )

    response = authenticated_client.patch(
        f"/api/v1/notes/{note['id']}",
        json={"body": "Unauthorized update"},
        headers=second_user_headers,
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You may only modify your own notes",
    }


def test_update_note_can_switch_relationship(
    authenticated_client: TestClient,
) -> None:
    company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Note Relationship Company"},
    ).json()

    contact = authenticated_client.post(
        "/api/v1/contacts",
        json={
            "first_name": "Areeb",
            "company_id": company["id"],
        },
    ).json()

    note = authenticated_client.post(
        "/api/v1/notes",
        json={
            "body": "Relationship note",
            "company_id": company["id"],
        },
    ).json()

    response = authenticated_client.patch(
        f"/api/v1/notes/{note['id']}",
        json={
            "company_id": None,
            "contact_id": contact["id"],
        },
    )

    assert response.status_code == 200
    assert response.json()["company_id"] is None
    assert response.json()["contact_id"] == contact["id"]


def test_delete_own_note(
    authenticated_client: TestClient,
) -> None:
    company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Note Delete Company"},
    ).json()

    note = authenticated_client.post(
        "/api/v1/notes",
        json={
            "body": "Temporary note",
            "company_id": company["id"],
        },
    ).json()

    delete_response = authenticated_client.delete(
        f"/api/v1/notes/{note['id']}"
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = authenticated_client.get(
        f"/api/v1/notes/{note['id']}"
    )

    assert get_response.status_code == 404


def test_delete_other_users_note_returns_403(
    authenticated_client: TestClient,
) -> None:
    company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Protected Delete Company"},
    ).json()

    note = authenticated_client.post(
        "/api/v1/notes",
        json={
            "body": "Protected note",
            "company_id": company["id"],
        },
    ).json()

    second_user_headers = create_second_user_headers(
        authenticated_client
    )

    response = authenticated_client.delete(
        f"/api/v1/notes/{note['id']}",
        headers=second_user_headers,
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You may only modify your own notes",
    }


def test_update_missing_note_returns_404(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.patch(
        "/api/v1/notes/999999",
        json={"body": "Missing note"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Note not found",
    }