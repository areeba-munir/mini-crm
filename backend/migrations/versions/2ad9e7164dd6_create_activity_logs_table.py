"""create activity logs table

Revision ID: 2ad9e7164dd6
Revises: 37921543693b
Create Date: 2026-08-24 14:23:37.265841
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "2ad9e7164dd6"
down_revision: str | Sequence[str] | None = (
    "37921543693b"
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


activity_action_enum = postgresql.ENUM(
    "Created",
    "Updated",
    "Deleted",
    name="activity_action",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    activity_action_enum.create(
        bind,
        checkfirst=True,
    )

    op.create_table(
        "activity_logs",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "actor_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "action",
            activity_action_enum,
            nullable=False,
        ),
        sa.Column(
            "entity_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "entity_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "description",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "details",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_activity_logs_entity",
        "activity_logs",
        [
            "entity_type",
            "entity_id",
        ],
        unique=False,
    )

    op.create_index(
        op.f("ix_activity_logs_actor_id"),
        "activity_logs",
        ["actor_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_activity_logs_action"),
        "activity_logs",
        ["action"],
        unique=False,
    )

    op.create_index(
        op.f("ix_activity_logs_entity_type"),
        "activity_logs",
        ["entity_type"],
        unique=False,
    )

    op.create_index(
        op.f("ix_activity_logs_created_at"),
        "activity_logs",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_activity_logs_created_at"),
        table_name="activity_logs",
    )

    op.drop_index(
        op.f("ix_activity_logs_entity_type"),
        table_name="activity_logs",
    )

    op.drop_index(
        op.f("ix_activity_logs_action"),
        table_name="activity_logs",
    )

    op.drop_index(
        op.f("ix_activity_logs_actor_id"),
        table_name="activity_logs",
    )

    op.drop_index(
        "ix_activity_logs_entity",
        table_name="activity_logs",
    )

    op.drop_table("activity_logs")

    bind = op.get_bind()

    activity_action_enum.drop(
        bind,
        checkfirst=True,
    )