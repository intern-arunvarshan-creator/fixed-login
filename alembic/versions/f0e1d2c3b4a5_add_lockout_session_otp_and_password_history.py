"""add lockout, session pointer, otp state, and password history

Revision ID: f0e1d2c3b4a5
Revises: 1baaea471287
Create Date: 2026-08-28 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f0e1d2c3b4a5"
down_revision: str | Sequence[str] | None = "1baaea471287"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add lockout/session columns to platform_admins and the OTP/history tables."""
    op.add_column(
        "platform_admins",
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("platform_admins", sa.Column("locked_until", sa.DateTime(), nullable=True))
    op.add_column(
        "platform_admins",
        sa.Column(
            "current_refresh_jti",
            sqlmodel.sql.sqltypes.AutoString(length=36),
            nullable=True,
        ),
    )

    op.create_table(
        "password_reset_otps",
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.Column("window_started_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("email"),
    )

    op.create_table(
        "password_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "platform_admin_id", sa.Uuid(), sa.ForeignKey("platform_admins.id"), nullable=False
        ),
        sa.Column("hashed_password", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_password_history_platform_admin_id"),
        "password_history",
        ["platform_admin_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_password_history_platform_admin_id"), table_name="password_history")
    op.drop_table("password_history")
    op.drop_table("password_reset_otps")
    op.drop_column("platform_admins", "current_refresh_jti")
    op.drop_column("platform_admins", "locked_until")
    op.drop_column("platform_admins", "failed_login_attempts")
