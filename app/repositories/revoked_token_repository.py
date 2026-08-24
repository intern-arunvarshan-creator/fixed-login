"""Revoked-token blacklist (all SQL)."""

from datetime import datetime

from sqlalchemy import select
from sqlmodel import col

from app.database.session import get_session
from app.models.revoked_token import RevokedToken


async def revoke(jti: str, expires_at: datetime) -> RevokedToken:
    db = get_session()
    entry = RevokedToken(jti=jti, expires_at=expires_at)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def is_revoked(jti: str) -> bool:
    result = await get_session().execute(
        select(RevokedToken).where(col(RevokedToken.jti) == jti)
    )
    return result.scalar_one_or_none() is not None
