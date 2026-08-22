from fastapi.testclient import TestClient


def test_cors_allows_configured_frontend(
    client: TestClient,
) -> None:
    response = client.options(
        "/api/v1/companies",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers[
            "access-control-allow-origin"
        ]
        == "http://localhost:3000"
    )


def test_cors_rejects_unconfigured_origin(
    client: TestClient,
) -> None:
    response = client.options(
        "/api/v1/companies",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert (
        "access-control-allow-origin"
        not in response.headers
    )