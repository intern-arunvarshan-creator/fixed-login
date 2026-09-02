"""add query_categories table

Revision ID: 077418c76968
Revises: d08a5d22d172
Create Date: 2026-09-02 14:50:53.161044

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "077418c76968"
down_revision: Union[str, Sequence[str], None] = "d08a5d22d172"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # timestamps: server_default fills existing rows
    op.add_column(
        "query_categories",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "query_categories",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # created_by / updated_by: add nullable → backfill → set NOT NULL
    op.add_column(
        "query_categories",
        sa.Column("created_by", sa.Integer(), nullable=True),
    )
    op.add_column(
        "query_categories",
        sa.Column("updated_by", sa.Integer(), nullable=True),
    )
    op.execute(
        "UPDATE query_categories SET created_by = 1 WHERE created_by IS NULL"
    )
    op.execute(
        "UPDATE query_categories SET updated_by = 1 WHERE updated_by IS NULL"
    )
    op.alter_column("query_categories", "created_by", nullable=False)
    op.alter_column("query_categories", "updated_by", nullable=False)

    # indexes only (do not change status/description types here)
    op.create_index(
        "idx_query_categories_type",
        "query_categories",
        ["type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_query_categories_key"),
        "query_categories",
        ["key"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_query_categories_key"), table_name="query_categories")
    op.drop_index("idx_query_categories_type", table_name="query_categories")
    op.drop_column("query_categories", "updated_by")
    op.drop_column("query_categories", "created_by")
    op.drop_column("query_categories", "updated_at")
    op.drop_column("query_categories", "created_at")
    # ### end Alembic commands ###
