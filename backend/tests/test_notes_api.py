from fastapi.testclient import TestClient

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