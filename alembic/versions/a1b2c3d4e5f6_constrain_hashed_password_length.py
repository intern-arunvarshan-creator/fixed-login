"""constrain hashed_password columns to the fixed bcrypt output length

Revision ID: a1b2c3d4e5f6
Revises: e2f3a4b5c6d7
Create Date: 2026-08-28 01:00:00.000000

"""

from collections.abc import Sequence

import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "e2f3a4b5c6d7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Constrain hashed_password to bcrypt's fixed 60-character output length."""
    for table in ("users", "platform_admins", "password_history"):
        op.alter_column(
            table,
            "hashed_password",
            existing_type=sqlmodel.sql.sqltypes.AutoString(),
            type_=sqlmodel.sql.sqltypes.AutoString(length=60),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Restore the unbounded hashed_password columns."""
    for table in ("users", "platform_admins", "password_history"):
        op.alter_column(
            table,
            "hashed_password",
            existing_type=sqlmodel.sql.sqltypes.AutoString(length=60),
            type_=sqlmodel.sql.sqltypes.AutoString(),
            existing_nullable=False,
        )
