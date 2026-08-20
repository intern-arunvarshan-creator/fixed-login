import uuid
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from app.models.enums import UserStatus
from app.models.user import User


async def create_user(db: AsyncSession, user: User) -> User:
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def list_users(
    db: AsyncSession,
    *,
    page: int = DEFAULT_PAGE,
    limit: int = DEFAULT_PAGE_SIZE,
    search: str | None = None,
    status: UserStatus | None = None,
) -> tuple[list[User], int]:
    filters = []
    if search:
        pattern = f"%{search}%"
        filters.append(or_(col(User.name).ilike(pattern), col(User.email).ilike(pattern)))
    if status is not None:
        filters.append(col(User.status) == status)

    total = await db.scalar(select(func.count()).select_from(User).where(*filters))
    result = await db.execute(
        select(User)
        .where(*filters)
        .order_by(col(User.created_at))
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return list(result.scalars().all()), total or 0


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(col(User.email) == email))
    return result.scalar_one_or_none()


async def update_user(db: AsyncSession, user: User, data: dict[str, Any]) -> User:
    for field, value in data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    await db.delete(user)
    await db.commit()
