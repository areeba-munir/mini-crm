import csv
from io import StringIO

import pytest
from fastapi.testclient import TestClient


LEAD_COLUMNS = [
    "title",
    "company_id",
    "contact_id",
    "stage",
    "estimated_value",
    "source",
    "expected_close_date",
    "description",
]


def build_lead_csv(
    rows: list[dict[str, str]],
) -> bytes:
    output = StringIO(newline="")

    writer = csv.DictWriter(
        output,
        fieldnames=LEAD_COLUMNS,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)

    return output.getvalue().encode("utf-8-sig")


def csv_upload(
    content: bytes,
    *,
    filename: str = "leads.csv",
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


def create_company(
    client: TestClient,
    *,
    name: str,
) -> int:
    response = client.post(
        "/api/v1/companies",
        json={
            "name": name,
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def create_contact(
    client: TestClient,
    *,
    first_name: str,
    company_id: int,
) -> int:
    response = client.post(
        "/api/v1/contacts",
        json={
            "first_name": first_name,
            "company_id": company_id,
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def test_preview_import_and_export_lead_csv(
    authenticated_client: TestClient,
) -> None:
    company_id = create_company(
        authenticated_client,
        name="Lead CSV Company",
    )
    contact_id = create_contact(
        authenticated_client,
        first_name="Lead Contact",
        company_id=company_id,
    )

    content = build_lead_csv(
        [
            {
                "title": "  Enterprise Deal  ",
                "company_id": str(company_id),
                "contact_id": str(contact_id),
                "stage": "Qualified",
                "estimated_value": "12500.50",
                "source": "Referral",
                "expected_close_date": "2026-12-31",
                "description": "Important opportunity",
            },
            {
                "title": "New Deal",
                "company_id": str(company_id),
                "contact_id": "",
                "stage": "",
                "estimated_value": "",
                "source": "",
                "expected_close_date": "",
                "description": "",
            },
        ]
    )

    preview_response = authenticated_client.post(
        "/api/v1/leads/import/preview",
        files=csv_upload(content),
    )

    assert preview_response.status_code == 200

    preview = preview_response.json()

    assert preview["entity"] == "leads"
    assert preview["columns"] == LEAD_COLUMNS
    assert preview["total_rows"] == 2
    assert preview["valid_rows"] == 2
    assert preview["invalid_rows"] == 0
    assert preview["can_import"] is True
    assert (
        preview["rows"][0]["values"]["title"]
        == "Enterprise Deal"
    )

    import_response = authenticated_client.post(
        "/api/v1/leads/import",
        files=csv_upload(content),
    )

    assert import_response.status_code == 200
    assert (
        import_response.json()["imported_count"]
        == 2
    )

    list_response = authenticated_client.get(
        "/api/v1/leads"
    )

    assert list_response.status_code == 200

    leads_by_title = {
        lead["title"]: lead
        for lead in list_response.json()
    }

    assert set(leads_by_title) == {
        "Enterprise Deal",
        "New Deal",
    }

    enterprise_lead = leads_by_title[
        "Enterprise Deal"
    ]
    new_lead = leads_by_title["New Deal"]

    assert (
        enterprise_lead["company_id"]
        == company_id
    )
    assert (
        enterprise_lead["contact_id"]
        == contact_id
    )
    assert enterprise_lead["stage"] == "Qualified"
    assert (
        enterprise_lead["estimated_value"]
        == "12500.50"
    )
    assert (
        enterprise_lead["expected_close_date"]
        == "2026-12-31"
    )

    assert new_lead["stage"] == "New"
    assert new_lead["contact_id"] is None
    assert new_lead["estimated_value"] is None

    export_response = authenticated_client.get(
        "/api/v1/leads/export"
    )

    assert export_response.status_code == 200
    assert export_response.headers[
        "content-type"
    ].startswith("text/csv")
    assert (
        "leads.csv"
        in export_response.headers[
            "content-disposition"
        ]
    )

    exported_text = export_response.content.decode(
        "utf-8-sig"
    )
    reader = csv.DictReader(StringIO(exported_text))
    exported_rows = list(reader)

    assert reader.fieldnames == LEAD_COLUMNS

    exported_by_title = {
        row["title"]: row
        for row in exported_rows
    }

    assert (
        exported_by_title[
            "Enterprise Deal"
        ]["company_id"]
        == str(company_id)
    )
    assert (
        exported_by_title[
            "Enterprise Deal"
        ]["contact_id"]
        == str(contact_id)
    )
    assert (
        exported_by_title[
            "Enterprise Deal"
        ]["stage"]
        == "Qualified"
    )
    assert (
        exported_by_title[
            "Enterprise Deal"
        ]["expected_close_date"]
        == "2026-12-31"
    )


def test_missing_company_prevents_entire_lead_import(
    authenticated_client: TestClient,
) -> None:
    valid_company_id = create_company(
        authenticated_client,
        name="Valid Lead Company",
    )

    content = build_lead_csv(
        [
            {
                "title": "Valid Lead",
                "company_id": str(valid_company_id),
                "contact_id": "",
                "stage": "New",
                "estimated_value": "",
                "source": "",
                "expected_close_date": "",
                "description": "",
            },
            {
                "title": "Missing Company Lead",
                "company_id": "999999",
                "contact_id": "",
                "stage": "New",
                "estimated_value": "",
                "source": "",
                "expected_close_date": "",
                "description": "",
            },
        ]
    )

    response = authenticated_client.post(
        "/api/v1/leads/import",
        files=csv_upload(content),
    )

    assert response.status_code == 200

    result = response.json()

    assert result["imported_count"] == 0
    assert result["preview"]["can_import"] is False
    assert result["preview"]["valid_rows"] == 1
    assert result["preview"]["invalid_rows"] == 1
    assert result["preview"]["rows"][1]["errors"]

    list_response = authenticated_client.get(
        "/api/v1/leads"
    )

    assert list_response.status_code == 200
    assert list_response.json() == []


def test_contact_must_belong_to_lead_company(
    authenticated_client: TestClient,
) -> None:
    first_company_id = create_company(
        authenticated_client,
        name="First Lead Company",
    )
    second_company_id = create_company(
        authenticated_client,
        name="Second Lead Company",
    )
    contact_id = create_contact(
        authenticated_client,
        first_name="Wrong Company Contact",
        company_id=first_company_id,
    )

    content = build_lead_csv(
        [
            {
                "title": "Mismatched Contact Lead",
                "company_id": str(second_company_id),
                "contact_id": str(contact_id),
                "stage": "Contacted",
                "estimated_value": "500",
                "source": "",
                "expected_close_date": "",
                "description": "",
            }
        ]
    )

    response = authenticated_client.post(
        "/api/v1/leads/import/preview",
        files=csv_upload(content),
    )

    assert response.status_code == 200

    preview = response.json()

    assert preview["can_import"] is False
    assert preview["valid_rows"] == 0
    assert preview["invalid_rows"] == 1
    assert preview["rows"][0]["errors"]


def test_invalid_lead_values_are_rejected(
    authenticated_client: TestClient,
) -> None:
    company_id = create_company(
        authenticated_client,
        name="Invalid Lead Values Company",
    )

    content = build_lead_csv(
        [
            {
                "title": "Invalid Lead",
                "company_id": str(company_id),
                "contact_id": "",
                "stage": "Not A Stage",
                "estimated_value": "-10",
                "source": "",
                "expected_close_date": "invalid-date",
                "description": "",
            }
        ]
    )

    response = authenticated_client.post(
        "/api/v1/leads/import/preview",
        files=csv_upload(content),
    )

    assert response.status_code == 200

    preview = response.json()

    assert preview["can_import"] is False
    assert preview["valid_rows"] == 0
    assert preview["invalid_rows"] == 1
    assert preview["rows"][0]["row_number"] == 2
    assert len(preview["rows"][0]["errors"]) >= 3


def test_existing_lead_prevents_entire_import(
    authenticated_client: TestClient,
) -> None:
    company_id = create_company(
        authenticated_client,
        name="Duplicate Lead Company",
    )

    create_response = authenticated_client.post(
        "/api/v1/leads",
        json={
            "title": "Existing Lead",
            "company_id": company_id,
            "stage": "New",
        },
    )

    assert create_response.status_code == 201

    content = build_lead_csv(
        [
            {
                "title": "Existing Lead",
                "company_id": str(company_id),
                "contact_id": "",
                "stage": "New",
                "estimated_value": "",
                "source": "",
                "expected_close_date": "",
                "description": "",
            },
            {
                "title": "Should Not Import",
                "company_id": str(company_id),
                "contact_id": "",
                "stage": "Qualified",
                "estimated_value": "",
                "source": "",
                "expected_close_date": "",
                "description": "",
            },
        ]
    )

    response = authenticated_client.post(
        "/api/v1/leads/import",
        files=csv_upload(content),
    )

    assert response.status_code == 200

    result = response.json()

    assert result["imported_count"] == 0
    assert result["preview"]["can_import"] is False

    list_response = authenticated_client.get(
        "/api/v1/leads"
    )

    assert [
        lead["title"]
        for lead in list_response.json()
    ] == ["Existing Lead"]


def test_lead_csv_requires_csv_extension(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.post(
        "/api/v1/leads/import/preview",
        files=csv_upload(
            build_lead_csv([]),
            filename="leads.txt",
        ),
    )

    assert response.status_code == 422


def test_manager_can_use_lead_csv_endpoints(
    authenticated_client: TestClient,
) -> None:
    company_id = create_company(
        authenticated_client,
        name="Manager Lead CSV Company",
    )

    manager = register_account(
        authenticated_client,
        full_name="Lead CSV Manager",
        email="lead-csv-manager@example.com",
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
        email="lead-csv-manager@example.com",
    )

    authenticated_client.headers[
        "Authorization"
    ] = f"Bearer {manager_token}"

    content = build_lead_csv(
        [
            {
                "title": "Manager Imported Lead",
                "company_id": str(company_id),
                "contact_id": "",
                "stage": "New",
                "estimated_value": "",
                "source": "",
                "expected_close_date": "",
                "description": "",
            }
        ]
    )

    preview_response = authenticated_client.post(
        "/api/v1/leads/import/preview",
        files=csv_upload(content),
    )
    import_response = authenticated_client.post(
        "/api/v1/leads/import",
        files=csv_upload(content),
    )
    export_response = authenticated_client.get(
        "/api/v1/leads/export"
    )

    assert preview_response.status_code == 200
    assert import_response.status_code == 200
    assert export_response.status_code == 200


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/leads/export"),
        (
            "POST",
            "/api/v1/leads/import/preview",
        ),
        ("POST", "/api/v1/leads/import"),
    ],
)
def test_member_cannot_use_lead_csv_endpoints(
    authenticated_client: TestClient,
    method: str,
    path: str,
) -> None:
    register_account(
        authenticated_client,
        full_name="Lead CSV Member",
        email="lead-csv-member@example.com",
    )

    member_token = login_account(
        authenticated_client,
        email="lead-csv-member@example.com",
    )

    authenticated_client.headers[
        "Authorization"
    ] = f"Bearer {member_token}"

    arguments: dict[str, object] = {}

    if method == "POST":
        arguments["files"] = csv_upload(
            build_lead_csv([])
        )

    response = authenticated_client.request(
        method,
        path,
        **arguments,
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/leads/export"),
        (
            "POST",
            "/api/v1/leads/import/preview",
        ),
        ("POST", "/api/v1/leads/import"),
    ],
)
def test_lead_csv_endpoints_require_authentication(
    client: TestClient,
    method: str,
    path: str,
) -> None:
    arguments: dict[str, object] = {}

    if method == "POST":
        arguments["files"] = csv_upload(
            build_lead_csv([])
        )

    response = client.request(
        method,
        path,
        **arguments,
    )

    assert response.status_code == 401