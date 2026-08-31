from pydantic import BaseModel, Field


class CsvRowPreview(BaseModel):
    row_number: int = Field(ge=1)
    values: dict[str, str | None]
    errors: list[str] = Field(
        default_factory=list
    )


class CsvPreviewResult(BaseModel):
    entity: str
    columns: list[str]
    total_rows: int = Field(ge=0)
    valid_rows: int = Field(ge=0)
    invalid_rows: int = Field(ge=0)
    can_import: bool
    rows: list[CsvRowPreview]


class CsvImportResult(BaseModel):
    imported_count: int = Field(ge=0)
    preview: CsvPreviewResult