"""platform admin login by email

Revision ID: f624f5f2faad
Revises: ef8d79552169
Create Date: 2026-08-21 11:10:21.196989

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f624f5f2faad"
down_revision: str | Sequence[str] | None = "ef8d79552169"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rebuild ``platform_admins`` keyed by id with email/status — re-seed afterward."""
    op.drop_table("platform_admins")
    op.create_table(
        "platform_admins",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("username", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("hashed_password", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("status", sa.Enum("active", "inactive", name="admin_status"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_platform_admins_email"), "platform_admins", ["email"], unique=True)
    op.create_index(
        op.f("ix_platform_admins_username"), "platform_admins", ["username"], unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_platform_admins_username"), table_name="platform_admins")
    op.drop_index(op.f("ix_platform_admins_email"), table_name="platform_admins")
    op.drop_table("platform_admins")
    sa.Enum(name="admin_status").drop(op.get_bind(), checkfirst=True)
    op.create_table(
        "platform_admins",
        sa.Column("username", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("hashed_password", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("username"),
    )
