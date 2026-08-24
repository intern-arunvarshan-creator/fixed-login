"""add url payload response to audit logs

Revision ID: 6735d368b960
Revises: 4132696c4f09
Create Date: 2026-08-24 14:44:17.564191

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6735d368b960"
down_revision: str | Sequence[str] | None = "4132696c4f09"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "audit_logs",
        sa.Column("url", sqlmodel.sql.sqltypes.AutoString(length=2048), nullable=True),
    )
    op.add_column("audit_logs", sa.Column("payload", sa.JSON(), nullable=True))
    op.add_column("audit_logs", sa.Column("response", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("audit_logs", "response")
    op.drop_column("audit_logs", "payload")
    op.drop_column("audit_logs", "url")
