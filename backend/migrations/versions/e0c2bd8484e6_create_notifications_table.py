"""create notifications table

Revision ID: e0c2bd8484e6
Revises: 2ad9e7164dd6
Create Date: 2026-08-27 22:00:37.752911
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e0c2bd8484e6"
down_revision: Union[str, Sequence[str], None] = "2ad9e7164dd6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create notifications."""
    op.create_table(
        "notifications",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "recipient_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "notification_type",
            sa.Enum(
                "Task Assigned",
                "Meeting Invitation",
                "System",
                name="notification_type",
            ),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "message",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "link",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "is_read",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "read_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["recipient_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_notifications_created_at"),
        "notifications",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notifications_is_read"),
        "notifications",
        ["is_read"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notifications_notification_type"),
        "notifications",
        ["notification_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notifications_recipient_id"),
        "notifications",
        ["recipient_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove notifications and their enum type."""
    op.drop_index(
        op.f("ix_notifications_recipient_id"),
        table_name="notifications",
    )
    op.drop_index(
        op.f("ix_notifications_notification_type"),
        table_name="notifications",
    )
    op.drop_index(
        op.f("ix_notifications_is_read"),
        table_name="notifications",
    )
    op.drop_index(
        op.f("ix_notifications_created_at"),
        table_name="notifications",
    )

    op.drop_table("notifications")

    sa.Enum(
        "Task Assigned",
        "Meeting Invitation",
        "System",
        name="notification_type",
    ).drop(
        op.get_bind(),
        checkfirst=True,
    )