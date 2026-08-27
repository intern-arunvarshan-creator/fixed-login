"""Password history (all SQL)."""

import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlmodel import col

from app.database.session import get_session
from app.models.password_history import PasswordHistory


async def add(admin_id: uuid.UUID, hashed_password: str, created_at: datetime) -> PasswordHistory:
    db = get_session()
    row = PasswordHistory(
        platform_admin_id=admin_id, hashed_password=hashed_password, created_at=created_at
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def recent_for_admin(admin_id: uuid.UUID, limit: int) -> list[PasswordHistory]:
    result = await get_session().execute(
        select(PasswordHistory)
        .where(col(PasswordHistory.platform_admin_id) == admin_id)
        .order_by(col(PasswordHistory.created_at).desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def trim(admin_id: uuid.UUID, keep: int) -> None:
    """Delete all but the ``keep`` most recent entries for an admin."""
    db = get_session()
    rows = await recent_for_admin(admin_id, limit=keep)
    keep_ids = {row.id for row in rows}
    if not keep_ids:
        return
    await db.execute(
        delete(PasswordHistory).where(
            col(PasswordHistory.platform_admin_id) == admin_id,
            col(PasswordHistory.id).not_in(keep_ids),
        )
    )
    await db.commit()
