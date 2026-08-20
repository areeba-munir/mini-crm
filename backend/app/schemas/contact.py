from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class ContactCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    job_title: str | None = Field(default=None, max_length=150)
    company_id: int | None = Field(default=None, ge=1)

    @field_validator("first_name", mode="before")
    @classmethod
    def clean_first_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(
        cls,
        value: EmailStr | None,
    ) -> str | None:
        if value is None:
            return None

        return str(value).lower()


class ContactUpdate(BaseModel):
    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    job_title: str | None = Field(default=None, max_length=150)
    company_id: int | None = Field(default=None, ge=1)

    @field_validator("first_name", mode="before")
    @classmethod
    def clean_first_name(cls, value: object) -> object:
        if value is None:
            raise ValueError("First name cannot be null")

        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(
        cls,
        value: EmailStr | None,
    ) -> str | None:
        if value is None:
            return None

        return str(value).lower()


class ContactRead(ContactCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)