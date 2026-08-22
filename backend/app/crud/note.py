from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate


def create_note(
    db: Session,
    note_data: NoteCreate,
    author_id: int,
) -> Note:
    note = Note(
        **note_data.model_dump(),
        author_id=author_id,
    )

    db.add(note)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(note)
    return note


def list_notes(
    db: Session,
) -> Sequence[Note]:
    statement = select(Note).order_by(
        Note.created_at.desc(),
        Note.id.desc(),
    )

    return db.scalars(statement).all()


def get_note(
    db: Session,
    note_id: int,
) -> Note | None:
    return db.get(Note, note_id)


def update_note(
    db: Session,
    note: Note,
    note_data: NoteUpdate,
) -> Note:
    update_data = note_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(note, field, value)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(note)
    return note


def delete_note(
    db: Session,
    note: Note,
) -> None:
    db.delete(note)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise