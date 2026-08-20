from datetime import date, datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.models.lead import LeadStage


class LeadCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
    )
    company_id: int = Field(ge=1)
    contact_id: int | None = Field(
        default=None,
        ge=1,
    )
    stage: LeadStage = LeadStage.NEW
    estimated_value: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    source: str | None = Field(
        default=None,
        max_length=100,
    )
    expected_close_date: date | None = None
    description: str | None = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("Title cannot be blank")

        return stripped_value

    @field_validator("source", "description")
    @classmethod
    def strip_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        stripped_value = value.strip()
        return stripped_value or None


class LeadUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        max_length=200,
    )
    company_id: int | None = Field(
        default=None,
        ge=1,
    )
    contact_id: int | None = Field(
        default=None,
        ge=1,
    )
    stage: LeadStage | None = None
    estimated_value: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    source: str | None = Field(
        default=None,
        max_length=100,
    )
    expected_close_date: date | None = None
    description: str | None = None

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: str | None,
    ) -> str:
        if value is None:
            raise ValueError("Title cannot be null")

        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("Title cannot be blank")

        return stripped_value

    @field_validator("company_id")
    @classmethod
    def validate_company_id(
        cls,
        value: int | None,
    ) -> int:
        if value is None:
            raise ValueError("Company cannot be null")

        return value

    @field_validator("stage")
    @classmethod
    def validate_stage(
        cls,
        value: LeadStage | None,
    ) -> LeadStage:
        if value is None:
            raise ValueError("Stage cannot be null")

        return value

    @field_validator("source", "description")
    @classmethod
    def strip_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        stripped_value = value.strip()
        return stripped_value or None


class LeadRead(LeadCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )