from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.models.platform_admin import PlatformAdmin


async def get_admin_by_username(db: AsyncSession, username: str) -> PlatformAdmin | None:
    result = await db.execute(select(PlatformAdmin).where(col(PlatformAdmin.username) == username))
    return result.scalar_one_or_none()
