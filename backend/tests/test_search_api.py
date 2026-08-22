from fastapi.testclient import TestClient


def test_search_groups_case_insensitive_results(
    authenticated_client: TestClient,
) -> None:
    company = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Northstar Labs",
            "industry": "Software",
        },
    ).json()

    contact = authenticated_client.post(
        "/api/v1/contacts",
        json={
            "first_name": "Alex",
            "email": "alex@northstar.example",
            "company_id": company["id"],
        },
    ).json()

    lead = authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "Northstar Expansion",
            "company_id": company["id"],
        },
    ).json()

    response = authenticated_client.get(
        "/api/v1/search",
        params={"q": "NORTHSTAR"},
    )

    assert response.status_code == 200

    results = response.json()

    assert [
        item["id"] for item in results["companies"]
    ] == [company["id"]]
    assert [
        item["id"] for item in results["contacts"]
    ] == [contact["id"]]
    assert [
        item["id"] for item in results["leads"]
    ] == [lead["id"]]


def test_search_returns_empty_groups(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/search",
        params={"q": "nothingmatches"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "companies": [],
        "contacts": [],
        "leads": [],
    }


def test_search_applies_limit_per_entity(
    authenticated_client: TestClient,
) -> None:
    for suffix in ("Alpha", "Beta", "Gamma"):
        authenticated_client.post(
            "/api/v1/companies",
            json={
                "name": f"LimitMatch {suffix}",
            },
        )

    response = authenticated_client.get(
        "/api/v1/search",
        params={
            "q": "LimitMatch",
            "limit": 2,
        },
    )

    assert response.status_code == 200
    assert len(response.json()["companies"]) == 2


def test_search_rejects_short_or_blank_query(
    authenticated_client: TestClient,
) -> None:
    short_response = authenticated_client.get(
        "/api/v1/search",
        params={"q": "a"},
    )
    blank_response = authenticated_client.get(
        "/api/v1/search",
        params={"q": "   "},
    )

    assert short_response.status_code == 422
    assert blank_response.status_code == 422


def test_search_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/search",
        params={"q": "north"},
    )

    assert response.status_code == 401