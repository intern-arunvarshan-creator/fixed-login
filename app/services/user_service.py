import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from app.core.security import hash_password
from app.exceptions.errors import email_already_registered, user_not_found
from app.models.enums import UserStatus
from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import UserCreate, UserReplace, UserUpdate


async def _ensure_email_available(
    db: AsyncSession,
    email: str,
    *,
    exclude_id: uuid.UUID | None = None,
) -> None:
    existing = await user_repository.get_user_by_email(db, email)
    if existing is not None and (exclude_id is None or existing.id != exclude_id):
        raise email_already_registered()


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    await _ensure_email_available(db, data.email)
    user = User(
        name=data.name,
        email=data.email,
        status=data.status,
        hashed_password=hash_password(data.password),
    )
    return await user_repository.create_user(db, user)


async def list_users(
    db: AsyncSession,
    *,
    page: int = DEFAULT_PAGE,
    limit: int = DEFAULT_PAGE_SIZE,
    search: str | None = None,
    status: UserStatus | None = None,
) -> tuple[list[User], int]:
    return await user_repository.list_users(
        db, page=page, limit=limit, search=search, status=status
    )


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await user_repository.get_user(db, user_id)
    if user is None:
        raise user_not_found()
    return user


async def update_user(db: AsyncSession, user_id: uuid.UUID, data: UserUpdate) -> User:
    user = await get_user(db, user_id)
    payload = data.model_dump(exclude_unset=True, exclude_none=True)
    if "email" in payload:
        await _ensure_email_available(db, payload["email"], exclude_id=user_id)
    return await user_repository.update_user(db, user, payload)


async def replace_user(db: AsyncSession, user_id: uuid.UUID, data: UserReplace) -> User:
    user = await get_user(db, user_id)
    await _ensure_email_available(db, data.email, exclude_id=user_id)
    payload = {
        "name": data.name,
        "email": data.email,
        "hashed_password": hash_password(data.password),
    }
    return await user_repository.update_user(db, user, payload)


async def delete_user(db: AsyncSession, user_id: uuid.UUID) -> None:
    user = await get_user(db, user_id)
    await user_repository.delete_user(db, user)
