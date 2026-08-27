"""consolidate status enum and add status to roles and screens

Revision ID: 1baaea471287
Revises: b4e5c8d1a2f7
Create Date: 2026-08-27 18:01:57.861635

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1baaea471287"
down_revision: str | Sequence[str] | None = "b4e5c8d1a2f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The single shared enum all four resource tables use.
STATUS = postgresql.ENUM("active", "inactive", name="status", create_type=False)


def upgrade() -> None:
    """Upgrade schema."""
    postgresql.ENUM("active", "inactive", name="status").create(op.get_bind(), checkfirst=True)

    op.alter_column(
        "platform_admins",
        "status",
        existing_type=postgresql.ENUM("active", "inactive", name="admin_status"),
        type_=STATUS,
        existing_nullable=False,
        postgresql_using="status::text::status",
    )
    op.alter_column(
        "users",
        "status",
        existing_type=postgresql.ENUM("active", "inactive", name="user_status"),
        type_=STATUS,
        existing_nullable=False,
        postgresql_using="status::text::status",
    )

    # Server defaults backfill existing seeded rows; they are dropped below so
    # the columns match the model (Python-side defaults only).
    op.add_column("roles", sa.Column("status", STATUS, nullable=False, server_default="active"))
    op.add_column(
        "roles",
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.add_column("screens", sa.Column("status", STATUS, nullable=False, server_default="active"))
    op.add_column(
        "screens",
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.alter_column("roles", "status", server_default=None)
    op.alter_column("roles", "updated_at", server_default=None)
    op.alter_column("screens", "status", server_default=None)
    op.alter_column("screens", "updated_at", server_default=None)

    postgresql.ENUM("active", "inactive", name="admin_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM("active", "inactive", name="user_status").drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    """Downgrade schema."""
    postgresql.ENUM("active", "inactive", name="admin_status").create(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM("active", "inactive", name="user_status").create(op.get_bind(), checkfirst=True)

    op.alter_column(
        "platform_admins",
        "status",
        existing_type=postgresql.ENUM("active", "inactive", name="status"),
        type_=postgresql.ENUM("active", "inactive", name="admin_status"),
        existing_nullable=False,
        postgresql_using="status::text::admin_status",
    )
    op.alter_column(
        "users",
        "status",
        existing_type=postgresql.ENUM("active", "inactive", name="status"),
        type_=postgresql.ENUM("active", "inactive", name="user_status"),
        existing_nullable=False,
        postgresql_using="status::text::user_status",
    )

    op.drop_column("screens", "updated_at")
    op.drop_column("screens", "status")
    op.drop_column("roles", "updated_at")
    op.drop_column("roles", "status")

    postgresql.ENUM("active", "inactive", name="status").drop(op.get_bind(), checkfirst=True)
