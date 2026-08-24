"""add user roles

Revision ID: 37921543693b
Revises: 98320e298e00
Create Date: 2026-08-24 13:50:01.371663
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "37921543693b"
down_revision: str | Sequence[str] | None = (
    "98320e298e00"
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


user_role_enum = postgresql.ENUM(
    "Admin",
    "Manager",
    "Member",
    name="user_role",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    user_role_enum.create(
        bind,
        checkfirst=True,
    )

    op.add_column(
        "users",
        sa.Column(
            "role",
            user_role_enum,
            nullable=False,
            server_default=sa.text("'Member'"),
        ),
    )

    op.create_index(
        op.f("ix_users_role"),
        "users",
        ["role"],
        unique=False,
    )

    # Preserve access for accounts created before
    # role-based permissions were introduced.
    op.execute(
        sa.text(
            "UPDATE users SET role = 'Admin'"
        )
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_users_role"),
        table_name="users",
    )

    op.drop_column(
        "users",
        "role",
    )

    bind = op.get_bind()

    user_role_enum.drop(
        bind,
        checkfirst=True,
    )