from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Path,
    Query,
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
from app.core.lead_csv import (
    export_lead_csv,
    import_lead_csv,
    preview_lead_csv,
)
from app.crud.company import (
    get_company as get_company_record,
)
from app.crud.contact import (
    get_contact as get_contact_record,
)
from app.crud.lead import (
    LeadSort,
    create_lead as create_lead_record,
    delete_lead as delete_lead_record,
    get_lead as get_lead_record,
    list_leads as list_lead_records,
    update_lead as update_lead_record,
)
from app.db.session import get_db
from app.models.lead import Lead, LeadStage
from app.schemas.csv_transfer import (
    CsvImportResult,
    CsvPreviewResult,
)
from app.schemas.lead import (
    LeadCreate,
    LeadRead,
    LeadUpdate,
)


router = APIRouter(
    prefix="/leads",
    tags=["Leads"],
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
    response_model=list[LeadRead],
)
def get_leads(
    db: Annotated[Session, Depends(get_db)],
    stage: Annotated[
        LeadStage | None,
        Query(),
    ] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=200,
        ),
    ] = None,
    company_id: Annotated[
        int | None,
        Query(ge=1),
    ] = None,
    contact_id: Annotated[
        int | None,
        Query(ge=1),
    ] = None,
    min_estimated_value: Annotated[
        Decimal | None,
        Query(ge=0),
    ] = None,
    max_estimated_value: Annotated[
        Decimal | None,
        Query(ge=0),
    ] = None,
    expected_close_from: Annotated[
        date | None,
        Query(),
    ] = None,
    expected_close_to: Annotated[
        date | None,
        Query(),
    ] = None,
    sort_by: Annotated[
        LeadSort,
        Query(),
    ] = "newest",
) -> Sequence[Lead]:
    if (
        min_estimated_value is not None
        and max_estimated_value is not None
        and min_estimated_value
        > max_estimated_value
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=(
                "Minimum estimated value cannot "
                "exceed maximum estimated value"
            ),
        )

    if (
        expected_close_from is not None
        and expected_close_to is not None
        and expected_close_from
        > expected_close_to
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=(
                "Expected-close start date cannot "
                "be after end date"
            ),
        )

    return list_lead_records(
        db,
        stage=stage,
        search=q,
        company_id=company_id,
        contact_id=contact_id,
        min_estimated_value=(
            min_estimated_value
        ),
        max_estimated_value=(
            max_estimated_value
        ),
        expected_close_from=(
            expected_close_from
        ),
        expected_close_to=expected_close_to,
        sort_by=sort_by,
    )


@router.get(
    "/export",
    dependencies=[
        Depends(get_current_manager),
    ],
)
def export_leads(
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    leads = list_lead_records(db)

    return Response(
        content=export_lead_csv(leads),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                'attachment; filename="leads.csv"'
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
def preview_leads_import(
    upload: Annotated[
        UploadFile,
        File(),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> CsvPreviewResult:
    content = _read_csv_upload(upload)

    return preview_lead_csv(
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
def import_leads(
    upload: Annotated[
        UploadFile,
        File(),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> CsvImportResult:
    content = _read_csv_upload(upload)

    return import_lead_csv(
        db,
        content,
    )


@router.post(
    "",
    response_model=LeadRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(get_current_manager),
    ],
)
def create_lead(
    lead_data: LeadCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Lead:
    company = get_company_record(
        db,
        lead_data.company_id,
    )

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    if lead_data.contact_id is not None:
        contact = get_contact_record(
            db,
            lead_data.contact_id,
        )

        if contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found",
            )

        if (
            contact.company_id
            != lead_data.company_id
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_CONTENT
                ),
                detail=(
                    "Contact must belong to "
                    "the lead company"
                ),
            )

    return create_lead_record(
        db,
        lead_data,
    )


@router.get(
    "/{lead_id}",
    response_model=LeadRead,
)
def get_lead(
    lead_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
) -> Lead:
    lead = get_lead_record(
        db,
        lead_id,
    )

    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    return lead


@router.patch(
    "/{lead_id}",
    response_model=LeadRead,
    dependencies=[
        Depends(get_current_manager),
    ],
)
def update_lead(
    lead_id: Annotated[int, Path(ge=1)],
    lead_data: LeadUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> Lead:
    lead = get_lead_record(
        db,
        lead_id,
    )

    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    company_id = (
        lead_data.company_id
        if "company_id"
        in lead_data.model_fields_set
        else lead.company_id
    )

    if (
        get_company_record(
            db,
            company_id,
        )
        is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    contact_id = (
        lead_data.contact_id
        if "contact_id"
        in lead_data.model_fields_set
        else lead.contact_id
    )

    if contact_id is not None:
        contact = get_contact_record(
            db,
            contact_id,
        )

        if contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found",
            )

        if contact.company_id != company_id:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_CONTENT
                ),
                detail=(
                    "Contact must belong to "
                    "the lead company"
                ),
            )

    return update_lead_record(
        db,
        lead,
        lead_data,
    )


@router.delete(
    "/{lead_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(get_current_manager),
    ],
)
def delete_lead(
    lead_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    lead = get_lead_record(
        db,
        lead_id,
    )

    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    delete_lead_record(
        db,
        lead,
    )