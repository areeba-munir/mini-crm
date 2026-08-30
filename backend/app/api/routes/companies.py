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
    export_company_csv,
    import_company_csv,
    preview_company_csv,
)
from app.crud.company import (
    create_company as create_company_record,
    delete_company as delete_company_record,
    get_company as get_company_record,
    list_companies as list_company_records,
    update_company as update_company_record,
)
from app.db.session import get_db
from app.models.company import Company
from app.schemas.company import (
    CompanyCreate,
    CompanyRead,
    CompanyUpdate,
)
from app.schemas.csv_transfer import (
    CsvImportResult,
    CsvPreviewResult,
)


router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
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
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail="The uploaded file must use the .csv extension",
        )

    try:
        return upload.file.read(
            MAX_CSV_FILE_SIZE_BYTES + 1
        )
    finally:
        upload.file.close()


@router.get(
    "",
    response_model=list[CompanyRead],
)
def get_companies(
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[Company]:
    return list_company_records(db)


@router.get(
    "/export",
    dependencies=[
        Depends(get_current_manager),
    ],
)
def export_companies(
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    companies = list_company_records(db)
    content = export_company_csv(companies)

    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                'attachment; filename="companies.csv"'
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
def preview_companies_import(
    upload: Annotated[
        UploadFile,
        File(
            description=(
                "UTF-8 CSV file containing company records"
            )
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> CsvPreviewResult:
    content = _read_csv_upload(upload)

    return preview_company_csv(
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
def import_companies(
    upload: Annotated[
        UploadFile,
        File(
            description=(
                "Validated UTF-8 CSV file containing "
                "company records"
            )
        ),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> CsvImportResult:
    content = _read_csv_upload(upload)

    return import_company_csv(
        db,
        content,
    )


@router.post(
    "",
    response_model=CompanyRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(get_current_manager),
    ],
)
def create_company(
    company_data: CompanyCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Company:
    return create_company_record(
        db,
        company_data,
    )


@router.get(
    "/{company_id}",
    response_model=CompanyRead,
)
def get_company(
    company_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
) -> Company:
    company = get_company_record(
        db,
        company_id,
    )

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return company


@router.patch(
    "/{company_id}",
    response_model=CompanyRead,
    dependencies=[
        Depends(get_current_manager),
    ],
)
def update_company(
    company_id: Annotated[int, Path(ge=1)],
    company_data: CompanyUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> Company:
    company = get_company_record(
        db,
        company_id,
    )

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return update_company_record(
        db,
        company,
        company_data,
    )


@router.delete(
    "/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(get_current_manager),
    ],
)
def delete_company(
    company_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    company = get_company_record(
        db,
        company_id,
    )

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    delete_company_record(
        db,
        company,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )