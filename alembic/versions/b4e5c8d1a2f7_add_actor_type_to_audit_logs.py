"""add actor_type to audit logs

Revision ID: b4e5c8d1a2f7
Revises: cc69a82fdc7d
Create Date: 2026-08-26 11:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4e5c8d1a2f7"
down_revision: str | Sequence[str] | None = "cc69a82fdc7d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "audit_logs",
        sa.Column("actor_type", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("audit_logs", "actor_type")
