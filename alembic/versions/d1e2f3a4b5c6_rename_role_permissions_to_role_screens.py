"""rename role_permissions to role_screens

Revision ID: d1e2f3a4b5c6
Revises: b1a2c3d4e5f6
Create Date: 2026-08-28 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: str | Sequence[str] | None = "b1a2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rename the role→screen grant table to match its join-table convention."""
    op.rename_table("role_permissions", "role_screens")


def downgrade() -> None:
    """Rename it back."""
    op.rename_table("role_screens", "role_permissions")
