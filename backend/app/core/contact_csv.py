import csv
import io
from collections.abc import Sequence
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.company_csv import (
    MAX_CSV_FILE_SIZE_BYTES,
    MAX_CSV_ROWS,
)

from app.models.company import Company
from app.models.contact import Contact
from app.schemas.contact import ContactCreate
from app.schemas.csv_transfer import (
    CsvImportResult,
    CsvPreviewResult,
    CsvRowPreview,
)


CONTACT_CSV_COLUMNS = [
    "first_name",
    "last_name",
    "email",
    "phone",
    "job_title",
    "company_id",
]


def _clean_cell(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    stripped_value = value.strip()
    return stripped_value or None


def _normalize_key_value(
    value: object,
) -> str:
    if value is None:
        return ""

    return str(value).strip().casefold()


def _contact_key(
    contact: Contact | ContactCreate,
) -> tuple[str, ...]:
    return tuple(
        _normalize_key_value(
            getattr(contact, column)
        )
        for column in CONTACT_CSV_COLUMNS
    )


def _validation_messages(
    error: ValidationError,
) -> list[str]:
    messages: list[str] = []

    for item in error.errors():
        location = ".".join(
            str(part)
            for part in item["loc"]
        )
        message = item["msg"]

        if location:
            messages.append(
                f"{location}: {message}"
            )
        else:
            messages.append(message)

    return messages


def _error_preview(
    message: str,
    *,
    columns: list[str] | None = None,
) -> CsvPreviewResult:
    return CsvPreviewResult(
        entity="contacts",
        columns=columns or CONTACT_CSV_COLUMNS,
        total_rows=0,
        valid_rows=0,
        invalid_rows=1,
        can_import=False,
        rows=[
            CsvRowPreview(
                row_number=1,
                values={},
                errors=[message],
            )
        ],
    )


def parse_contact_csv(
    db: Session,
    content: bytes,
) -> tuple[
    list[ContactCreate],
    CsvPreviewResult,
]:
    if not content:
        return [], _error_preview(
            "The CSV file is empty."
        )

    if len(content) > MAX_CSV_FILE_SIZE_BYTES:
        return [], _error_preview(
            "The CSV file exceeds the 2 MB limit."
        )

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return [], _error_preview(
            "The CSV file must use UTF-8 encoding."
        )

    try:
        reader = csv.DictReader(
            io.StringIO(
                text,
                newline="",
            )
        )
    except csv.Error as error:
        return [], _error_preview(
            f"Unable to parse CSV: {error}"
        )

    raw_fieldnames = reader.fieldnames

    if raw_fieldnames is None:
        return [], _error_preview(
            "The CSV header row is missing."
        )

    columns = [
        field.strip().lower()
        for field in raw_fieldnames
    ]

    header_errors: list[str] = []

    if len(columns) != len(set(columns)):
        header_errors.append(
            "CSV column names cannot be duplicated."
        )

    missing_columns = (
        set(CONTACT_CSV_COLUMNS)
        - set(columns)
    )
    unsupported_columns = (
        set(columns)
        - set(CONTACT_CSV_COLUMNS)
    )

    if missing_columns:
        header_errors.append(
            "Missing columns: "
            + ", ".join(
                sorted(missing_columns)
            )
            + "."
        )

    if unsupported_columns:
        header_errors.append(
            "Unsupported columns: "
            + ", ".join(
                sorted(unsupported_columns)
            )
            + "."
        )

    if header_errors:
        return [], CsvPreviewResult(
            entity="contacts",
            columns=columns,
            total_rows=0,
            valid_rows=0,
            invalid_rows=1,
            can_import=False,
            rows=[
                CsvRowPreview(
                    row_number=1,
                    values={},
                    errors=header_errors,
                )
            ],
        )

    reader.fieldnames = columns

    existing_contacts = db.scalars(
        select(Contact)
    ).all()

    existing_keys = {
        _contact_key(contact)
        for contact in existing_contacts
    }

    existing_company_ids = set(
        db.scalars(
            select(Company.id)
        ).all()
    )

    first_row_by_key: dict[
        tuple[str, ...],
        int,
    ] = {}

    valid_records: list[ContactCreate] = []
    preview_rows: list[CsvRowPreview] = []
    total_rows = 0

    try:
        for physical_row_number, raw_row in enumerate(
            reader,
            start=2,
        ):
            values = {
                column: _clean_cell(
                    raw_row.get(column)
                )
                for column in CONTACT_CSV_COLUMNS
            }

            extra_values: Any = raw_row.get(None)

            if (
                all(
                    value is None
                    for value in values.values()
                )
                and not extra_values
            ):
                continue

            total_rows += 1
            row_errors: list[str] = []

            if total_rows > MAX_CSV_ROWS:
                row_errors.append(
                    "The CSV file exceeds the "
                    "1,000-row limit."
                )

                preview_rows.append(
                    CsvRowPreview(
                        row_number=physical_row_number,
                        values=values,
                        errors=row_errors,
                    )
                )
                break

            if extra_values:
                row_errors.append(
                    "The row contains more values "
                    "than the header defines."
                )

            record: ContactCreate | None = None

            try:
                record = ContactCreate.model_validate(
                    values
                )
            except ValidationError as error:
                row_errors.extend(
                    _validation_messages(error)
                )

            if record is not None:
                if (
                    record.company_id is not None
                    and record.company_id
                    not in existing_company_ids
                ):
                    row_errors.append(
                        "Company "
                        f"#{record.company_id} "
                        "does not exist."
                    )

                record_key = _contact_key(record)

                if record_key in existing_keys:
                    row_errors.append(
                        "This contact already exists."
                    )

                duplicate_row_number = (
                    first_row_by_key.get(record_key)
                )

                if duplicate_row_number is not None:
                    row_errors.append(
                        "This row duplicates CSV row "
                        f"{duplicate_row_number}."
                    )
                else:
                    first_row_by_key[
                        record_key
                    ] = physical_row_number

            if (
                record is not None
                and not row_errors
            ):
                valid_records.append(record)

            preview_rows.append(
                CsvRowPreview(
                    row_number=physical_row_number,
                    values=values,
                    errors=row_errors,
                )
            )
    except csv.Error as error:
        preview_rows.append(
            CsvRowPreview(
                row_number=max(
                    reader.line_num,
                    1,
                ),
                values={},
                errors=[
                    f"Unable to parse CSV: {error}"
                ],
            )
        )

    if total_rows == 0:
        return [], _error_preview(
            "The CSV file contains no data rows.",
            columns=columns,
        )

    invalid_rows = sum(
        bool(row.errors)
        for row in preview_rows
    )

    preview = CsvPreviewResult(
        entity="contacts",
        columns=CONTACT_CSV_COLUMNS,
        total_rows=total_rows,
        valid_rows=len(valid_records),
        invalid_rows=invalid_rows,
        can_import=(
            total_rows > 0
            and invalid_rows == 0
        ),
        rows=preview_rows,
    )

    return valid_records, preview


def preview_contact_csv(
    db: Session,
    content: bytes,
) -> CsvPreviewResult:
    _, preview = parse_contact_csv(
        db,
        content,
    )

    return preview


def import_contact_csv(
    db: Session,
    content: bytes,
) -> CsvImportResult:
    records, preview = parse_contact_csv(
        db,
        content,
    )

    if not preview.can_import:
        return CsvImportResult(
            imported_count=0,
            preview=preview,
        )

    contacts = [
        Contact(**record.model_dump())
        for record in records
    ]

    db.add_all(contacts)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return CsvImportResult(
        imported_count=len(contacts),
        preview=preview,
    )


def export_contact_csv(
    contacts: Sequence[Contact],
) -> bytes:
    output = io.StringIO(
        newline=""
    )

    writer = csv.DictWriter(
        output,
        fieldnames=CONTACT_CSV_COLUMNS,
        lineterminator="\n",
    )

    writer.writeheader()

    for contact in contacts:
        writer.writerow(
            {
                column: (
                    getattr(contact, column)
                    if getattr(
                        contact,
                        column,
                    )
                    is not None
                    else ""
                )
                for column in CONTACT_CSV_COLUMNS
            }
        )

    return output.getvalue().encode(
        "utf-8-sig"
    )