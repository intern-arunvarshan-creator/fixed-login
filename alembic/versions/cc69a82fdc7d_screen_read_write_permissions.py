"""screen read write permissions

Revision ID: cc69a82fdc7d
Revises: 21490779c2f5
Create Date: 2026-08-25 15:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cc69a82fdc7d"
down_revision: str | Sequence[str] | None = "21490779c2f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Replace name-based permissions with per-screen read/write grants."""
    op.create_table(
        "screens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_screens_code"), "screens", ["code"], unique=True)

    # permissions and role_permissions hold only seed data (see seed_rbac), so
    # they are dropped and recreated rather than backfilled in-place.
    op.drop_table("role_permissions")
    op.drop_table("permissions")

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Uuid(), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column(
            "screen_code",
            sqlmodel.sql.sqltypes.AutoString(length=50),
            sa.ForeignKey("screens.code"),
            nullable=False,
        ),
        sa.Column("read", sa.Boolean(), nullable=False),
        sa.Column("write", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("role_id", "screen_code"),
    )


def downgrade() -> None:
    """Restore the name-based permissions catalog."""
    op.drop_table("role_permissions")
    op.drop_index(op.f("ix_screens_code"), table_name="screens")
    op.drop_table("screens")

    op.create_table(
        "permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_permissions_name"), "permissions", ["name"], unique=True)

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Uuid(), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("permission_id", sa.Uuid(), sa.ForeignKey("permissions.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )
