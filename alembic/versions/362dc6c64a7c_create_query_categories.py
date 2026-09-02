"""create query categories

Revision ID: 362dc6c64a7c
Revises: 077418c76968
Create Date: 2026-09-02 17:35:36.775772

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "362dc6c64a7c"
down_revision: Union[str, Sequence[str], None] = "077418c76968"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Use the already-existing PostgreSQL enum type.
    status_type = postgresql.ENUM(
        "active",
        "inactive",
        name="status",
        create_type=False,
    )

    op.create_table(
        "query_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("module", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),

        sa.Column(
            "status",
            status_type,
            server_default=sa.text("'active'::status"),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("updated_by", sa.Uuid(), nullable=False),

        sa.ForeignKeyConstraint(
            ["created_by"],
            ["platform_admins.id"],
        ),

        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["platform_admins.id"],
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "idx_query_categories_module",
        "query_categories",
        ["module"],
        unique=False,
    )

    op.create_index(
        "idx_query_categories_status",
        "query_categories",
        ["status"],
        unique=False,
    )

    op.create_index(
        "idx_query_categories_type",
        "query_categories",
        ["type"],
        unique=False,
    )

    op.create_index(
        "ix_query_categories_key",
        "query_categories",
        ["key"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_query_categories_key",
        table_name="query_categories",
    )

    op.drop_index(
        "idx_query_categories_type",
        table_name="query_categories",
    )

    op.drop_index(
        "idx_query_categories_status",
        table_name="query_categories",
    )

    op.drop_index(
        "idx_query_categories_module",
        table_name="query_categories",
    )

    op.drop_table("query_categories")