import csv
from io import StringIO

import pytest
from fastapi.testclient import TestClient


CONTACT_COLUMNS = [
    "first_name",
    "last_name",
    "email",
    "phone",
    "job_title",
    "company_id",
]


def build_contact_csv(
    rows: list[dict[str, str]],
) -> bytes:
    output = StringIO(newline="")

    writer = csv.DictWriter(
        output,
        fieldnames=CONTACT_COLUMNS,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)

    return output.getvalue().encode("utf-8-sig")


def csv_upload(
    content: bytes,
    *,
    filename: str = "contacts.csv",
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


def test_preview_import_and_export_contact_csv(
    authenticated_client: TestClient,
) -> None:
    company_response = authenticated_client.post(
        "/api/v1/companies",
        json={
            "name": "Contact CSV Company",
        },
    )

    assert company_response.status_code == 201
    company_id = company_response.json()["id"]

    content = build_contact_csv(
        [
            {
                "first_name": "  Bob  ",
                "last_name": "Builder",
                "email": "BOB@EXAMPLE.COM",
                "phone": "555-0200",
                "job_title": "Engineer",
                "company_id": str(company_id),
            },
            {
                "first_name": "Alice",
                "last_name": "",
                "email": "",
                "phone": "",
                "job_title": "",
                "company_id": "",
            },
        ]
    )

    preview_response = authenticated_client.post(
        "/api/v1/contacts/import/preview",
        files=csv_upload(content),
    )

    assert preview_response.status_code == 200

    preview = preview_response.json()

    assert preview["entity"] == "contacts"
    assert preview["columns"] == CONTACT_COLUMNS
    assert preview["total_rows"] == 2
    assert preview["valid_rows"] == 2
    assert preview["invalid_rows"] == 0
    assert preview["can_import"] is True
    assert preview["rows"][0]["row_number"] == 2
    assert (
        preview["rows"][0]["values"]["first_name"]
        == "Bob"
    )

    import_response = authenticated_client.post(
        "/api/v1/contacts/import",
        files=csv_upload(content),
    )

    assert import_response.status_code == 200
    assert (
        import_response.json()["imported_count"]
        == 2
    )

    list_response = authenticated_client.get(
        "/api/v1/contacts"
    )

    assert list_response.status_code == 200

    contacts = list_response.json()

    assert [
        contact["first_name"]
        for contact in contacts
    ] == [
        "Alice",
        "Bob",
    ]

    bob = next(
        contact
        for contact in contacts
        if contact["first_name"] == "Bob"
    )

    assert bob["email"] == "bob@example.com"
    assert bob["company_id"] == company_id

    export_response = authenticated_client.get(
        "/api/v1/contacts/export"
    )

    assert export_response.status_code == 200
    assert export_response.headers[
        "content-type"
    ].startswith("text/csv")
    assert (
        "contacts.csv"
        in export_response.headers[
            "content-disposition"
        ]
    )

    exported_text = export_response.content.decode(
        "utf-8-sig"
    )
    reader = csv.DictReader(StringIO(exported_text))
    exported_rows = list(reader)

    assert reader.fieldnames == CONTACT_COLUMNS
    assert [
        row["first_name"]
        for row in exported_rows
    ] == [
        "Alice",
        "Bob",
    ]
    assert (
        exported_rows[1]["company_id"]
        == str(company_id)
    )


def test_missing_company_prevents_entire_contact_import(
    authenticated_client: TestClient,
) -> None:
    content = build_contact_csv(
        [
            {
                "first_name": "Valid",
                "last_name": "Contact",
                "email": "valid@example.com",
                "phone": "",
                "job_title": "",
                "company_id": "",
            },
            {
                "first_name": "Missing",
                "last_name": "Company",
                "email": "missing@example.com",
                "phone": "",
                "job_title": "",
                "company_id": "999999",
            },
        ]
    )

    response = authenticated_client.post(
        "/api/v1/contacts/import",
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
        "/api/v1/contacts"
    )

    assert list_response.status_code == 200
    assert list_response.json() == []


def test_invalid_email_is_rejected_in_contact_csv(
    authenticated_client: TestClient,
) -> None:
    content = build_contact_csv(
        [
            {
                "first_name": "Invalid",
                "last_name": "Email",
                "email": "not-an-email",
                "phone": "",
                "job_title": "",
                "company_id": "",
            }
        ]
    )

    response = authenticated_client.post(
        "/api/v1/contacts/import/preview",
        files=csv_upload(content),
    )

    assert response.status_code == 200

    preview = response.json()

    assert preview["can_import"] is False
    assert preview["valid_rows"] == 0
    assert preview["invalid_rows"] == 1
    assert preview["rows"][0]["row_number"] == 2
    assert preview["rows"][0]["errors"]


def test_existing_contact_prevents_entire_import(
    authenticated_client: TestClient,
) -> None:
    create_response = authenticated_client.post(
        "/api/v1/contacts",
        json={
            "first_name": "Existing",
            "last_name": "Contact",
            "email": "existing@example.com",
            "phone": None,
            "job_title": None,
            "company_id": None,
        },
    )

    assert create_response.status_code == 201

    content = build_contact_csv(
        [
            {
                "first_name": "Existing",
                "last_name": "Contact",
                "email": "existing@example.com",
                "phone": "",
                "job_title": "",
                "company_id": "",
            },
            {
                "first_name": "Should Not",
                "last_name": "Import",
                "email": "new@example.com",
                "phone": "",
                "job_title": "",
                "company_id": "",
            },
        ]
    )

    response = authenticated_client.post(
        "/api/v1/contacts/import",
        files=csv_upload(content),
    )

    assert response.status_code == 200

    result = response.json()

    assert result["imported_count"] == 0
    assert result["preview"]["can_import"] is False

    list_response = authenticated_client.get(
        "/api/v1/contacts"
    )

    assert [
        contact["first_name"]
        for contact in list_response.json()
    ] == ["Existing"]


def test_contact_csv_requires_csv_extension(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.post(
        "/api/v1/contacts/import/preview",
        files=csv_upload(
            build_contact_csv([]),
            filename="contacts.txt",
        ),
    )

    assert response.status_code == 422


def test_manager_can_use_contact_csv_endpoints(
    authenticated_client: TestClient,
) -> None:
    manager = register_account(
        authenticated_client,
        full_name="Contact CSV Manager",
        email="contact-csv-manager@example.com",
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
        email="contact-csv-manager@example.com",
    )

    authenticated_client.headers[
        "Authorization"
    ] = f"Bearer {manager_token}"

    content = build_contact_csv(
        [
            {
                "first_name": "Manager",
                "last_name": "Import",
                "email": "manager-import@example.com",
                "phone": "",
                "job_title": "",
                "company_id": "",
            }
        ]
    )

    preview_response = authenticated_client.post(
        "/api/v1/contacts/import/preview",
        files=csv_upload(content),
    )
    import_response = authenticated_client.post(
        "/api/v1/contacts/import",
        files=csv_upload(content),
    )
    export_response = authenticated_client.get(
        "/api/v1/contacts/export"
    )

    assert preview_response.status_code == 200
    assert import_response.status_code == 200
    assert export_response.status_code == 200


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/contacts/export"),
        (
            "POST",
            "/api/v1/contacts/import/preview",
        ),
        ("POST", "/api/v1/contacts/import"),
    ],
)
def test_member_cannot_use_contact_csv_endpoints(
    authenticated_client: TestClient,
    method: str,
    path: str,
) -> None:
    register_account(
        authenticated_client,
        full_name="Contact CSV Member",
        email="contact-csv-member@example.com",
    )

    member_token = login_account(
        authenticated_client,
        email="contact-csv-member@example.com",
    )

    authenticated_client.headers[
        "Authorization"
    ] = f"Bearer {member_token}"

    arguments: dict[str, object] = {}

    if method == "POST":
        arguments["files"] = csv_upload(
            build_contact_csv([])
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
        ("GET", "/api/v1/contacts/export"),
        (
            "POST",
            "/api/v1/contacts/import/preview",
        ),
        ("POST", "/api/v1/contacts/import"),
    ],
)
def test_contact_csv_endpoints_require_authentication(
    client: TestClient,
    method: str,
    path: str,
) -> None:
    arguments: dict[str, object] = {}

    if method == "POST":
        arguments["files"] = csv_upload(
            build_contact_csv([])
        )

    response = client.request(
        method,
        path,
        **arguments,
    )

    assert response.status_code == 401