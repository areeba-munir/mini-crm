import csv
import io
from collections.abc import Sequence
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session



from collections.abc import Sequence
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Path,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_manager,
    get_current_user,
)
from app.core.company_csv import (
    MAX_CSV_FILE_SIZE_BYTES,
)
from app.core.contact_csv import (
    export_contact_csv,
    import_contact_csv,
    preview_contact_csv,
)
from app.crud.company import (
    get_company as get_company_record,
)
from app.crud.contact import (
    create_contact as create_contact_record,
    delete_contact as delete_contact_record,
    get_contact as get_contact_record,
    list_contacts as list_contact_records,
    update_contact as update_contact_record,
)
from app.db.session import get_db
from app.models.contact import Contact
from app.schemas.contact import (
    ContactCreate,
    ContactRead,
    ContactUpdate,
)
from app.schemas.csv_transfer import (
    CsvImportResult,
    CsvPreviewResult,
)


router = APIRouter(
    prefix="/contacts",
    tags=["Contacts"],
    dependencies=[
        Depends(get_current_user),
    ],
)


def _read_csv_upload(
    upload: UploadFile,
) -> bytes:
    filename = upload.filename or ""

    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "The uploaded file must use "
                "the .csv extension"
            ),
        )

    try:
        return upload.file.read(
            MAX_CSV_FILE_SIZE_BYTES + 1
        )
    finally:
        upload.file.close()


@router.get(
    "",
    response_model=list[ContactRead],
)
def get_contacts(
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[Contact]:
    return list_contact_records(db)


@router.get(
    "/export",
    dependencies=[
        Depends(get_current_manager),
    ],
)
def export_contacts(
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    contacts = list_contact_records(db)

    return Response(
        content=export_contact_csv(contacts),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                'attachment; filename="contacts.csv"'
            ),
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post(
    "/import/preview",
    response_model=CsvPreviewResult,
    dependencies=[
        Depends(get_current_manager),
    ],
)
def preview_contacts_import(
    upload: Annotated[
        UploadFile,
        File(),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> CsvPreviewResult:
    content = _read_csv_upload(upload)

    return preview_contact_csv(
        db,
        content,
    )


@router.post(
    "/import",
    response_model=CsvImportResult,
    dependencies=[
        Depends(get_current_manager),
    ],
)
def import_contacts(
    upload: Annotated[
        UploadFile,
        File(),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> CsvImportResult:
    content = _read_csv_upload(upload)

    return import_contact_csv(
        db,
        content,
    )


@router.post(
    "",
    response_model=ContactRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(get_current_manager),
    ],
)
def create_contact(
    contact_data: ContactCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Contact:
    if (
        contact_data.company_id is not None
        and get_company_record(
            db,
            contact_data.company_id,
        )
        is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return create_contact_record(
        db,
        contact_data,
    )


@router.get(
    "/{contact_id}",
    response_model=ContactRead,
)
def get_contact(
    contact_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
) -> Contact:
    contact = get_contact_record(
        db,
        contact_id,
    )

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    return contact


@router.patch(
    "/{contact_id}",
    response_model=ContactRead,
    dependencies=[
        Depends(get_current_manager),
    ],
)
def update_contact(
    contact_id: Annotated[int, Path(ge=1)],
    contact_data: ContactUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> Contact:
    contact = get_contact_record(
        db,
        contact_id,
    )

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    company_id_was_provided = (
        "company_id"
        in contact_data.model_fields_set
    )

    if (
        company_id_was_provided
        and contact_data.company_id is not None
        and get_company_record(
            db,
            contact_data.company_id,
        )
        is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return update_contact_record(
        db,
        contact,
        contact_data,
    )


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(get_current_manager),
    ],
)
def delete_contact(
    contact_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    contact = get_contact_record(
        db,
        contact_id,
    )

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    delete_contact_record(
        db,
        contact,
    )