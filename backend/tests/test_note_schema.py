from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.note import Note
from app.schemas.note import (
    NoteCreate,
    NoteRead,
    NoteUpdate,
)


def test_note_create_normalizes_body() -> None:
    note = NoteCreate(
        body="  Important client information  ",
        company_id=1,
    )

    assert note.body == "Important client information"
    assert note.company_id == 1


def test_note_create_requires_related_entity() -> None:
    with pytest.raises(ValidationError):
        NoteCreate(
            body="General note without relationship",
        )


def test_note_create_rejects_multiple_relationships(
) -> None:
    with pytest.raises(ValidationError):
        NoteCreate(
            body="Invalid relationship note",
            company_id=1,
            contact_id=2,
        )


def test_note_create_rejects_blank_body() -> None:
    with pytest.raises(ValidationError):
        NoteCreate(
            body="   ",
            lead_id=1,
        )


def test_note_update_includes_only_provided_fields(
) -> None:
    update = NoteUpdate(
        body="Updated information",
    )

    assert update.model_dump(exclude_unset=True) == {
        "body": "Updated information",
    }


def test_note_update_can_move_relationship() -> None:
    update = NoteUpdate(
        company_id=None,
        lead_id=3,
    )

    assert update.model_dump(exclude_unset=True) == {
        "company_id": None,
        "lead_id": 3,
    }


def test_note_read_accepts_sqlalchemy_model() -> None:
    now = datetime.now(timezone.utc)

    note_model = Note(
        id=1,
        body="Important information",
        author_id=2,
        company_id=3,
        contact_id=None,
        lead_id=None,
        created_at=now,
        updated_at=now,
    )

    note = NoteRead.model_validate(note_model)

    assert note.id == 1
    assert note.author_id == 2
    assert note.company_id == 3