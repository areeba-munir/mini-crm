from typing import Any

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.models.activity_log import (
    ActivityAction,
    ActivityLog,
)
from app.models.company import Company
from app.models.contact import Contact
from app.models.lead import Lead
from app.models.meeting import Meeting
from app.models.note import Note
from app.models.task import Task


AUDITABLE_MODELS = (
    Company,
    Contact,
    Lead,
    Task,
    Meeting,
    Note,
)


def get_column_names(record: object) -> list[str]:
    state = inspect(record)

    return [
        attribute.key
        for attribute in state.mapper.column_attrs
    ]


def get_changed_column_names(
    record: object,
) -> list[str]:
    state = inspect(record)

    return [
        attribute.key
        for attribute in state.mapper.column_attrs
        if state.attrs[
            attribute.key
        ].history.has_changes()
    ]


@event.listens_for(Session, "before_flush")
def collect_activity_changes(
    session: Session,
    flush_context: object,
    instances: object,
) -> None:
    del flush_context, instances

    actor_id = session.info.get(
        "activity_actor_id"
    )

    if not isinstance(actor_id, int):
        return

    pending_changes: list[
        dict[str, Any]
    ] = []

    for record in session.new:
        if isinstance(record, AUDITABLE_MODELS):
            pending_changes.append(
                {
                    "record": record,
                    "action": (
                        ActivityAction.CREATED
                    ),
                    "fields": get_column_names(
                        record
                    ),
                }
            )

    for record in session.dirty:
        if not isinstance(
            record,
            AUDITABLE_MODELS,
        ):
            continue

        if not session.is_modified(
            record,
            include_collections=False,
        ):
            continue

        changed_fields = (
            get_changed_column_names(record)
        )

        if changed_fields:
            pending_changes.append(
                {
                    "record": record,
                    "action": (
                        ActivityAction.UPDATED
                    ),
                    "fields": changed_fields,
                }
            )

    for record in session.deleted:
        if isinstance(record, AUDITABLE_MODELS):
            pending_changes.append(
                {
                    "record": record,
                    "action": (
                        ActivityAction.DELETED
                    ),
                    "fields": [],
                }
            )

    if pending_changes:
        session.info[
            "pending_activity_changes"
        ] = pending_changes


@event.listens_for(
    Session,
    "after_flush_postexec",
)
def create_activity_logs(
    session: Session,
    flush_context: object,
) -> None:
    del flush_context

    pending_changes = session.info.pop(
        "pending_activity_changes",
        [],
    )

    actor_id = session.info.get(
        "activity_actor_id"
    )

    if (
        not pending_changes
        or not isinstance(actor_id, int)
    ):
        return

    for change in pending_changes:
        record = change["record"]
        action = change["action"]
        fields = change["fields"]

        if not isinstance(
            action,
            ActivityAction,
        ):
            continue

        entity_type = type(record).__name__
        entity_id = getattr(
            record,
            "id",
            None,
        )

        identifier = (
            f" #{entity_id}"
            if isinstance(entity_id, int)
            else ""
        )

        activity_log = ActivityLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=(
                entity_id
                if isinstance(entity_id, int)
                else None
            ),
            description=(
                f"{action.value} "
                f"{entity_type}{identifier}"
            ),
            details={
                "fields": fields,
            },
        )

        session.add(activity_log)