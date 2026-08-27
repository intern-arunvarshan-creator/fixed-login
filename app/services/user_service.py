"""User business rules."""

import uuid

from app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE
from app.core.security import hash_password
from app.exceptions.exceptions import EmailExistsError, UserNotFoundError
from app.models.enums import AuditAction, AuditResourceType, Status
from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import UserCreate, UserReplace, UserUpdate
from app.services import audit_service


async def _ensure_email_available(
    email: str,
    exclude_id: uuid.UUID | None = None,
) -> None:
    existing = await user_repository.get_user_by_email(email)
    if existing is not None and (exclude_id is None or existing.id != exclude_id):
        raise EmailExistsError()


async def create_user(data: UserCreate) -> User:
    await _ensure_email_available(data.email)
    user = User(
        name=data.name,
        email=data.email,
        status=data.status,
        hashed_password=hash_password(data.password),
    )
    user = await user_repository.create_user(user)
    await audit_service.record(
        action=AuditAction.USER_CREATE,
        resource_type=AuditResourceType.USER,
        resource_id=str(user.id),
        details={"email": user.email, "name": user.name},
    )
    return user


async def list_users(
    page: int = DEFAULT_PAGE,
    limit: int = DEFAULT_PAGE_SIZE,
    search: str | None = None,
    status: Status | None = None,
) -> tuple[list[User], int]:
    return await user_repository.list_users(page=page, limit=limit, search=search, status=status)


async def get_user(user_id: uuid.UUID) -> User:
    user = await user_repository.get_user(user_id)
    if user is None:
        raise UserNotFoundError()
    return user


async def update_user(user_id: uuid.UUID, data: UserUpdate) -> User:
    user = await get_user(user_id)
    payload = data.model_dump(exclude_unset=True, exclude_none=True)
    if "email" in payload:
        await _ensure_email_available(email=payload["email"], exclude_id=user_id)
    user = await user_repository.update_user(user=user, data=payload)
    await audit_service.record(
        action=AuditAction.USER_UPDATE,
        resource_type=AuditResourceType.USER,
        resource_id=str(user.id),
        details=data.model_dump(exclude_unset=True, exclude_none=True, mode="json"),
    )
    return user


async def replace_user(user_id: uuid.UUID, data: UserReplace) -> User:
    user = await get_user(user_id)
    await _ensure_email_available(email=data.email, exclude_id=user_id)
    payload = {
        "name": data.name,
        "email": data.email,
        "hashed_password": hash_password(data.password),
    }
    user = await user_repository.update_user(user=user, data=payload)
    await audit_service.record(
        action=AuditAction.USER_REPLACE,
        resource_type=AuditResourceType.USER,
        resource_id=str(user.id),
        details={"email": data.email, "name": data.name},
    )
    return user


async def delete_user(user_id: uuid.UUID) -> None:
    user = await get_user(user_id)
    await user_repository.delete_user(user)
    await audit_service.record(
        action=AuditAction.USER_DELETE,
        resource_type=AuditResourceType.USER,
        resource_id=str(user_id),
    )
