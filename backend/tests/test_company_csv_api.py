import csv
from io import StringIO

import pytest
from fastapi.testclient import TestClient


COMPANY_COLUMNS = [
    "name",
    "industry",
    "website",
    "email",
    "phone",
    "address",
]


def build_company_csv(
    rows: list[dict[str, str]],
    *,
    columns: list[str] | None = None,
) -> bytes:
    output = StringIO(newline="")

    writer = csv.DictWriter(
        output,
        fieldnames=columns or COMPANY_COLUMNS,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)

    return output.getvalue().encode("utf-8-sig")


def csv_upload(
    content: bytes,
    *,
    filename: str = "companies.csv",
) -> dict[str, tuple[str, bytes, str]]:
    return {
        "upload": (
            filename,
            content,
            "text/csv",
        )
    }


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


def test_preview_company_csv(
    authenticated_client: TestClient,
) -> None:
    content = build_company_csv(
        [
            {
                "name": "  Alpha Industries  ",
                "industry": "Technology",
                "website": "",
                "email": "alpha@example.com",
                "phone": "",
                "address": "Alpha Street",
            },
            {
                "name": "Beta Group",
                "industry": "",
                "website": "https://example.com",
                "email": "",
                "phone": "555-0100",
                "address": "",
            },
        ]
    )

    response = authenticated_client.post(
        "/api/v1/companies/import/preview",
        files=csv_upload(content),
    )

    assert response.status_code == 200

    preview = response.json()

    assert preview["entity"] == "companies"
    assert preview["columns"] == COMPANY_COLUMNS
    assert preview["total_rows"] == 2
    assert preview["valid_rows"] == 2
    assert preview["invalid_rows"] == 0
    assert preview["can_import"] is True

    assert [
        row["row_number"]
        for row in preview["rows"]
    ] == [2, 3]

    assert (
        preview["rows"][0]["values"]["name"]
        == "Alpha Industries"
    )
    assert (
        preview["rows"][0]["values"]["website"]
        is None
    )
    assert preview["rows"][0]["errors"] == []


def test_import_and_export_company_csv(
    authenticated_client: TestClient,
) -> None:
    content = build_company_csv(
        [
            {
                "name": "CSV Beta",
                "industry": "Finance",
                "website": "",
                "email": "beta@example.com",
                "phone": "555-0200",
                "address": "",
            },
            {
                "name": "CSV Alpha",
                "industry": "Technology",
                "website": "https://alpha.example.com",
                "email": "alpha@example.com",
                "phone": "",
                "address": "Alpha Avenue",
            },
        ]
    )

    import_response = authenticated_client.post(
        "/api/v1/companies/import",
        files=csv_upload(content),
    )

    assert import_response.status_code == 200

    result = import_response.json()

    assert result["imported_count"] == 2
    assert result["preview"]["can_import"] is True
    assert result["preview"]["valid_rows"] == 2

    list_response = authenticated_client.get(
        "/api/v1/companies"
    )

    assert list_response.status_code == 200

    companies = list_response.json()

    assert [
        company["name"]
        for company in companies
    ] == [
        "CSV Alpha",
        "CSV Beta",
    ]

    export_response = authenticated_client.get(
        "/api/v1/companies/export"
    )

    assert export_response.status_code == 200
    assert export_response.headers[
        "content-type"
    ].startswith("text/csv")
    assert (
        "companies.csv"
        in export_response.headers[
            "content-disposition"
        ]
    )

    exported_text = export_response.content.decode(
        "utf-8-sig"
    )
    reader = csv.DictReader(StringIO(exported_text))
    exported_rows = list(reader)

    assert reader.fieldnames == COMPANY_COLUMNS
    assert [
        row["name"]
        for row in exported_rows
    ] == [
        "CSV Alpha",
        "CSV Beta",
    ]

    assert exported_rows[0] == {
        "name": "CSV Alpha",
        "industry": "Technology",
        "website": "https://alpha.example.com",
        "email": "alpha@example.com",
        "phone": "",
        "address": "Alpha Avenue",
    }


def test_invalid_company_csv_is_not_partially_imported(
    authenticated_client: TestClient,
) -> None:
    content = build_company_csv(
        [
            {
                "name": "Valid Company",
                "industry": "Technology",
                "website": "",
                "email": "",
                "phone": "",
                "address": "",
            },
            {
                "name": "   ",
                "industry": "Finance",
                "website": "",
                "email": "",
                "phone": "",
                "address": "",
            },
        ]
    )

    response = authenticated_client.post(
        "/api/v1/companies/import",
        files=csv_upload(content),
    )

    assert response.status_code == 200

    result = response.json()
    preview = result["preview"]

    assert result["imported_count"] == 0
    assert preview["total_rows"] == 2
    assert preview["valid_rows"] == 1
    assert preview["invalid_rows"] == 1
    assert preview["can_import"] is False
    assert preview["rows"][1]["row_number"] == 3
    assert preview["rows"][1]["errors"]

    list_response = authenticated_client.get(
        "/api/v1/companies"
    )

    assert list_response.status_code == 200
    assert list_response.json() == []


def test_existing_duplicate_prevents_entire_import(
    authenticated_client: TestClient,
) -> None:
    create_response = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Existing Company",
            "industry": "Technology",
            "website": None,
            "email": "existing@example.com",
            "phone": None,
            "address": None,
        },
    )

    assert create_response.status_code == 201

    content = build_company_csv(
        [
            {
                "name": "Existing Company",
                "industry": "Technology",
                "website": "",
                "email": "existing@example.com",
                "phone": "",
                "address": "",
            },
            {
                "name": "Should Not Import",
                "industry": "Finance",
                "website": "",
                "email": "",
                "phone": "",
                "address": "",
            },
        ]
    )

    response = authenticated_client.post(
        "/api/v1/companies/import",
        files=csv_upload(content),
    )

    assert response.status_code == 200

    result = response.json()

    assert result["imported_count"] == 0
    assert result["preview"]["can_import"] is False
    assert result["preview"]["invalid_rows"] == 1
    assert result["preview"]["rows"][0]["errors"]

    list_response = authenticated_client.get(
        "/api/v1/companies"
    )

    names = [
        company["name"]
        for company in list_response.json()
    ]

    assert names == ["Existing Company"]
    assert "Should Not Import" not in names


def test_duplicate_rows_inside_csv_are_rejected(
    authenticated_client: TestClient,
) -> None:
    duplicate_row = {
        "name": "Repeated Company",
        "industry": "Retail",
        "website": "",
        "email": "",
        "phone": "",
        "address": "",
    }

    content = build_company_csv(
        [
            duplicate_row,
            duplicate_row,
        ]
    )

    response = authenticated_client.post(
        "/api/v1/companies/import/preview",
        files=csv_upload(content),
    )

    assert response.status_code == 200

    preview = response.json()

    assert preview["can_import"] is False
    assert preview["invalid_rows"] == 1
    assert preview["rows"][1]["row_number"] == 3
    assert preview["rows"][1]["errors"]


def test_company_csv_rejects_invalid_headers(
    authenticated_client: TestClient,
) -> None:
    content = build_company_csv(
        [
            {
                "name": "Header Company",
                "industry": "Technology",
            }
        ],
        columns=[
            "name",
            "industry",
        ],
    )

    response = authenticated_client.post(
        "/api/v1/companies/import/preview",
        files=csv_upload(content),
    )

    assert response.status_code == 200

    preview = response.json()

    assert preview["can_import"] is False
    assert preview["valid_rows"] == 0
    assert preview["invalid_rows"] > 0


def test_company_csv_requires_csv_extension(
    authenticated_client: TestClient,
) -> None:
    content = build_company_csv([])

    response = authenticated_client.post(
        "/api/v1/companies/import/preview",
        files=csv_upload(
            content,
            filename="companies.txt",
        ),
    )

    assert response.status_code == 422


def test_manager_can_use_company_csv_endpoints(
    authenticated_client: TestClient,
) -> None:
    manager = register_account(
        authenticated_client,
        full_name="CSV Manager",
        email="csv-manager@example.com",
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
        email="csv-manager@example.com",
    )

    authenticated_client.headers[
        "Authorization"
    ] = f"Bearer {manager_token}"

    content = build_company_csv(
        [
            {
                "name": "Manager CSV Company",
                "industry": "",
                "website": "",
                "email": "",
                "phone": "",
                "address": "",
            }
        ]
    )

    preview_response = authenticated_client.post(
        "/api/v1/companies/import/preview",
        files=csv_upload(content),
    )
    import_response = authenticated_client.post(
        "/api/v1/companies/import",
        files=csv_upload(content),
    )
    export_response = authenticated_client.get(
        "/api/v1/companies/export"
    )

    assert preview_response.status_code == 200
    assert import_response.status_code == 200
    assert export_response.status_code == 200


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/companies/export"),
        (
            "POST",
            "/api/v1/companies/import/preview",
        ),
        ("POST", "/api/v1/companies/import"),
    ],
)
def test_member_cannot_use_company_csv_endpoints(
    authenticated_client: TestClient,
    method: str,
    path: str,
) -> None:
    register_account(
        authenticated_client,
        full_name="CSV Member",
        email="csv-member@example.com",
    )

    member_token = login_account(
        authenticated_client,
        email="csv-member@example.com",
    )

    authenticated_client.headers[
        "Authorization"
    ] = f"Bearer {member_token}"

    request_arguments: dict[str, object] = {}

    if method == "POST":
        request_arguments["files"] = csv_upload(
            build_company_csv([])
        )

    response = authenticated_client.request(
        method,
        path,
        **request_arguments,
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/companies/export"),
        (
            "POST",
            "/api/v1/companies/import/preview",
        ),
        ("POST", "/api/v1/companies/import"),
    ],
)
def test_company_csv_endpoints_require_authentication(
    client: TestClient,
    method: str,
    path: str,
) -> None:
    request_arguments: dict[str, object] = {}

    if method == "POST":
        request_arguments["files"] = csv_upload(
            build_company_csv([])
        )

    response = client.request(
        method,
        path,
        **request_arguments,
    )

    assert response.status_code == 401