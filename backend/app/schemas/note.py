from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class NoteCreate(BaseModel):
    body: str = Field(min_length=1)
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

    @field_validator("body")
    @classmethod
    def strip_body(cls, value: str) -> str:
        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("Note body cannot be blank")

        return stripped_value

    @model_validator(mode="after")
    def validate_related_entity(self) -> "NoteCreate":
        related_ids = (
            self.company_id,
            self.contact_id,
            self.lead_id,
        )

        if sum(
            value is not None
            for value in related_ids
        ) != 1:
            raise ValueError(
                "A note must relate to exactly one "
                "company, contact, or lead"
            )

        return self


class NoteUpdate(BaseModel):
    body: str | None = None
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

    @field_validator("body")
    @classmethod
    def validate_body(
        cls,
        value: str | None,
    ) -> str:
        if value is None:
            raise ValueError(
                "Note body cannot be null"
            )

        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError(
                "Note body cannot be blank"
            )

        return stripped_value

    @model_validator(mode="after")
    def validate_provided_relationships(
        self,
    ) -> "NoteUpdate":
        provided_related_ids = [
            value
            for field, value in (
                ("company_id", self.company_id),
                ("contact_id", self.contact_id),
                ("lead_id", self.lead_id),
            )
            if field in self.model_fields_set
            and value is not None
        ]

        if len(provided_related_ids) > 1:
            raise ValueError(
                "A note must relate to exactly one "
                "company, contact, or lead"
            )

        return self


class NoteRead(NoteCreate):
    id: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )