from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)

from app.models.user import UserRole


class UserCreate(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=200,
    )
    email: EmailStr
    password: SecretStr = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("full_name", mode="before")
    @classmethod
    def clean_full_name(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(
        cls,
        value: EmailStr,
    ) -> str:
        return str(value).lower()


class UserUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    email: EmailStr | None = None

    @field_validator("full_name", mode="before")
    @classmethod
    def clean_full_name(
        cls,
        value: object,
    ) -> object:
        if value is None:
            raise ValueError(
                "Full name cannot be null"
            )

        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(
        cls,
        value: EmailStr | None,
    ) -> str:
        if value is None:
            raise ValueError(
                "Email cannot be null"
            )

        return str(value).lower()

    @model_validator(mode="after")
    def require_update_field(self) -> "UserUpdate":
        if not self.model_fields_set:
            raise ValueError(
                "Provide at least one profile field"
            )

        return self


class UserPasswordChange(BaseModel):
    current_password: SecretStr = Field(
        min_length=8,
        max_length=128,
    )
    new_password: SecretStr = Field(
        min_length=8,
        max_length=128,
    )

    @model_validator(mode="after")
    def passwords_must_differ(
        self,
    ) -> "UserPasswordChange":
        if (
            self.current_password.get_secret_value()
            == self.new_password.get_secret_value()
        ):
            raise ValueError(
                "New password must be different "
                "from the current password"
            )

        return self


class UserAdminUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator(
        "role",
        "is_active",
        mode="before",
    )
    @classmethod
    def fields_cannot_be_null(
        cls,
        value: object,
    ) -> object:
        if value is None:
            raise ValueError(
                "Administrative fields cannot be null"
            )

        return value

    @model_validator(mode="after")
    def require_update_field(
        self,
    ) -> "UserAdminUpdate":
        if not self.model_fields_set:
            raise ValueError(
                "Provide at least one administrative field"
            )

        return self


class UserRead(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )