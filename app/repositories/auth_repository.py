import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.models.platform_admin import PlatformAdmin


async def get_admin_by_email(db: AsyncSession, email: str) -> PlatformAdmin | None:
    result = await db.execute(select(PlatformAdmin).where(col(PlatformAdmin.email) == email))
    return result.scalar_one_or_none()


async def get_admin_by_id(db: AsyncSession, admin_id: uuid.UUID) -> PlatformAdmin | None:
    return await db.get(PlatformAdmin, admin_id)
