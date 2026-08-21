from datetime import datetime, timezone

from pydantic import (
    AnyHttpUrl,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    field_validator,
    model_validator,
)

from app.models.meeting import MeetingStatus


_url_adapter = TypeAdapter(AnyHttpUrl)


class MeetingCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
    )
    description: str | None = None
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    location: str | None = Field(
        default=None,
        max_length=500,
    )
    meeting_link: str | None = Field(
        default=None,
        max_length=500,
    )
    notes: str | None = None
    status: MeetingStatus = MeetingStatus.SCHEDULED
    organizer_id: int = Field(ge=1)
    company_id: int | None = Field(
        default=None,
        ge=1,
    )
    user_participant_ids: list[int] = Field(
        default_factory=list
    )
    contact_participant_ids: list[int] = Field(
        default_factory=list
    )

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("Title cannot be blank")

        return stripped_value

    @field_validator(
        "description",
        "location",
        "notes",
    )
    @classmethod
    def strip_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        stripped_value = value.strip()
        return stripped_value or None

    @field_validator("meeting_link")
    @classmethod
    def validate_meeting_link(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        stripped_value = value.strip()

        if not stripped_value:
            return None

        return str(
            _url_adapter.validate_python(
                stripped_value
            )
        )

    @field_validator("starts_at", "ends_at")
    @classmethod
    def normalize_datetime(
        cls,
        value: datetime,
    ) -> datetime:
        return value.astimezone(timezone.utc)

    @field_validator(
        "user_participant_ids",
        "contact_participant_ids",
    )
    @classmethod
    def validate_participant_ids(
        cls,
        values: list[int],
    ) -> list[int]:
        if any(value < 1 for value in values):
            raise ValueError(
                "Participant IDs must be positive"
            )

        if len(values) != len(set(values)):
            raise ValueError(
                "Participant IDs cannot be duplicated"
            )

        return values

    @model_validator(mode="after")
    def validate_time_range(self) -> "MeetingCreate":
        if self.ends_at <= self.starts_at:
            raise ValueError(
                "Meeting end must be after start"
            )

        return self


class MeetingUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        max_length=200,
    )
    description: str | None = None
    starts_at: AwareDatetime | None = None
    ends_at: AwareDatetime | None = None
    location: str | None = Field(
        default=None,
        max_length=500,
    )
    meeting_link: str | None = Field(
        default=None,
        max_length=500,
    )
    notes: str | None = None
    status: MeetingStatus | None = None
    organizer_id: int | None = Field(
        default=None,
        ge=1,
    )
    company_id: int | None = Field(
        default=None,
        ge=1,
    )
    user_participant_ids: list[int] | None = None
    contact_participant_ids: list[int] | None = None

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

    @field_validator("starts_at", "ends_at")
    @classmethod
    def normalize_datetime(
        cls,
        value: datetime | None,
    ) -> datetime:
        if value is None:
            raise ValueError(
                "Meeting time cannot be null"
            )

        return value.astimezone(timezone.utc)

    @field_validator("status", "organizer_id")
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

    @field_validator(
        "description",
        "location",
        "notes",
    )
    @classmethod
    def strip_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        stripped_value = value.strip()
        return stripped_value or None

    @field_validator("meeting_link")
    @classmethod
    def validate_meeting_link(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        stripped_value = value.strip()

        if not stripped_value:
            return None

        return str(
            _url_adapter.validate_python(
                stripped_value
            )
        )

    @field_validator(
        "user_participant_ids",
        "contact_participant_ids",
    )
    @classmethod
    def validate_participant_ids(
        cls,
        values: list[int] | None,
    ) -> list[int]:
        if values is None:
            raise ValueError(
                "Use an empty list to remove participants"
            )

        if any(value < 1 for value in values):
            raise ValueError(
                "Participant IDs must be positive"
            )

        if len(values) != len(set(values)):
            raise ValueError(
                "Participant IDs cannot be duplicated"
            )

        return values

    @model_validator(mode="after")
    def validate_time_range(self) -> "MeetingUpdate":
        if (
            "starts_at" in self.model_fields_set
            and "ends_at" in self.model_fields_set
            and self.starts_at is not None
            and self.ends_at is not None
            and self.ends_at <= self.starts_at
        ):
            raise ValueError(
                "Meeting end must be after start"
            )

        return self


class MeetingRead(MeetingCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )