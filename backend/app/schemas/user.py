from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
)


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=128)

    @field_validator("full_name", mode="before")
    @classmethod
    def clean_full_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class UserRead(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)