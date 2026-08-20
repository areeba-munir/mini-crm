from datetime import datetime

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models.task import (
    TaskPriority,
    TaskStatus,
)


class TaskCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
    )
    description: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    due_at: AwareDatetime | None = None
    assigned_to_id: int = Field(ge=1)
    company_id: int | None = Field(
        default=None,
        ge=1,
    )
    contact_id: int | None = Field(
        default=None,
        ge=1,
    )
    lead_id: int | None = Field(
        default=None,
        ge=1,
    )

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("Title cannot be blank")

        return stripped_value

    @field_validator("description")
    @classmethod
    def strip_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        stripped_value = value.strip()
        return stripped_value or None

    @model_validator(mode="after")
    def validate_related_entity(self) -> "TaskCreate":
        related_ids = (
            self.company_id,
            self.contact_id,
            self.lead_id,
        )

        if sum(
            value is not None
            for value in related_ids
        ) > 1:
            raise ValueError(
                "A task may relate to at most one "
                "company, contact, or lead"
            )

        return self


class TaskUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        max_length=200,
    )
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_at: AwareDatetime | None = None
    assigned_to_id: int | None = Field(
        default=None,
        ge=1,
    )
    company_id: int | None = Field(
        default=None,
        ge=1,
    )
    contact_id: int | None = Field(
        default=None,
        ge=1,
    )
    lead_id: int | None = Field(
        default=None,
        ge=1,
    )

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

    @field_validator(
        "status",
        "priority",
        "assigned_to_id",
    )
    @classmethod
    def required_fields_cannot_be_null(
        cls,
        value: object,
    ) -> object:
        if value is None:
            raise ValueError(
                "Required field cannot be null"
            )

        return value

    @field_validator("description")
    @classmethod
    def strip_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        stripped_value = value.strip()
        return stripped_value or None

    @model_validator(mode="after")
    def validate_related_entity(self) -> "TaskUpdate":
        related_ids = (
            self.company_id,
            self.contact_id,
            self.lead_id,
        )

        provided_related_ids = [
            value
            for field, value in zip(
                (
                    "company_id",
                    "contact_id",
                    "lead_id",
                ),
                related_ids,
                strict=True,
            )
            if field in self.model_fields_set
            and value is not None
        ]

        if len(provided_related_ids) > 1:
            raise ValueError(
                "A task may relate to at most one "
                "company, contact, or lead"
            )

        return self


class TaskRead(TaskCreate):
    id: int
    created_by_id: int
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )