from fastapi.testclient import TestClient


def test_create_company( authenticated_client: TestClient) -> None:
    response =  authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Automated Test Company",
            "industry": "Software",
        },
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["name"] == "Automated Test Company"
    assert response_data["industry"] == "Software"
    assert isinstance(response_data["id"], int)
    assert response_data["created_at"] is not None
    assert response_data["updated_at"] is not None

def test_list_companies(authenticated_client: TestClient) -> None:
    authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Beta Company"},
    )
    authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Alpha Company"},
    )

    response = authenticated_client.get("/api/v1/companies")

    assert response.status_code == 200

    company_names = [
        company["name"]
        for company in response.json()
    ]

    assert company_names == [
        "Alpha Company",
        "Beta Company",
    ]
def test_get_company(authenticated_client: TestClient) -> None:
    create_response = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Detail Test Company"},
    )
    company_id = create_response.json()["id"]

    response = authenticated_client.get(
        f"/api/v1/companies/{company_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == company_id
    assert response.json()["name"] == "Detail Test Company"


def test_get_missing_company_returns_404(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get("/api/v1/companies/999999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Company not found",
    }

def test_update_company(authenticated_client: TestClient) -> None:
    create_response = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Update Test Company",
            "industry": "Old Industry",
        },
    )
    company_id = create_response.json()["id"]

    response = authenticated_client.patch(
        f"/api/v1/companies/{company_id}",
        json={"industry": "New Industry"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Update Test Company"
    assert response.json()["industry"] == "New Industry"

    get_response = authenticated_client.get(
        f"/api/v1/companies/{company_id}"
    )

    assert get_response.json()["industry"] == "New Industry"


def test_update_company_rejects_blank_name(
    authenticated_client: TestClient,
) -> None:
    create_response = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Keep This Name"},
    )
    company_id = create_response.json()["id"]

    response = authenticated_client.patch(
        f"/api/v1/companies/{company_id}",
        json={"name": "   "},
    )

    assert response.status_code == 422

    get_response = authenticated_client.get(
        f"/api/v1/companies/{company_id}"
    )

    assert get_response.json()["name"] == "Keep This Name"
def test_delete_company(authenticated_client: TestClient) -> None:
    create_response = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Delete Test Company"},
    )
    company_id = create_response.json()["id"]

    delete_response = authenticated_client.delete(
        f"/api/v1/companies/{company_id}"
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = authenticated_client.get(
        f"/api/v1/companies/{company_id}"
    )

    assert get_response.status_code == 404


def test_delete_missing_company_returns_404(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.delete(
        "/api/v1/companies/999999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Company not found",
    }

def test_company_endpoints_require_authentication(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/companies")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated",
    }