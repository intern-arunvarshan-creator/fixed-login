import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.audit import record_audit
from app.api.deps import get_current_admin
from app.core.constants import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MIN_PAGE,
    MIN_PAGE_SIZE,
)
from app.database import get_db
from app.models.enums import AuditAction, AuditResourceType, UserStatus, UserStatusFilter
from app.models.platform_admin import PlatformAdmin
from app.models.user import User
from app.schemas.common import ApiResponse, Pagination
from app.schemas.user import (
    CODE_CREATED,
    CODE_DELETED,
    CODE_FETCHED,
    CODE_LISTED,
    CODE_UPDATED,
    MSG_CREATED,
    MSG_DELETED,
    MSG_FETCHED,
    MSG_LISTED,
    MSG_UPDATED,
    UserCreate,
    UserListData,
    UserRead,
    UserReplace,
    UserUpdate,
)
from app.services import user_service
from app.utils.pagination import total_pages

router = APIRouter(tags=["Users"])


@router.post("", response_model=ApiResponse[UserRead], status_code=201, summary="Create a user")
async def create_user(
    data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _admin: PlatformAdmin = Depends(get_current_admin),
) -> ApiResponse[UserRead]:
    """Create a new user with a name, email, and password."""
    user = await user_service.create_user(db, data)
    await record_audit(
        db,
        request,
        actor=_admin.username,
        action=AuditAction.USER_CREATE,
        resource_type=AuditResourceType.USER,
        resource_id=str(user.id),
        details={"email": user.email, "name": user.name},
    )
    return ApiResponse(code=CODE_CREATED, message=MSG_CREATED, data=user)


@router.get("", response_model=ApiResponse[UserListData], summary="List users")
async def list_users(
    page: int = Query(DEFAULT_PAGE, ge=MIN_PAGE),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE),
    search: str | None = Query(None, description="Search by name or email"),
    status: UserStatusFilter = Query(UserStatusFilter.ALL, description="Filter by user status"),
    db: AsyncSession = Depends(get_db),
    _admin: PlatformAdmin = Depends(get_current_admin),
) -> ApiResponse[UserListData]:
    """List users, paginated and optionally filtered by search text or status."""
    status_value = None if status == UserStatusFilter.ALL else UserStatus(status.value)
    users, total = await user_service.list_users(
        db, page=page, limit=limit, search=search, status=status_value
    )
    body = _to_user_list_data(users, page, limit, total)
    return ApiResponse(code=CODE_LISTED, message=MSG_LISTED, data=body)


@router.get("/{user_id}", response_model=ApiResponse[UserRead], summary="Get a user")
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: PlatformAdmin = Depends(get_current_admin),
) -> ApiResponse[UserRead]:
    """Fetch a single user by id."""
    user = await user_service.get_user(db, user_id)
    return ApiResponse(code=CODE_FETCHED, message=MSG_FETCHED, data=user)


@router.put("/{user_id}", response_model=ApiResponse[UserRead], summary="Fully replace a user")
async def replace_user(
    user_id: uuid.UUID,
    data: UserReplace,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _admin: PlatformAdmin = Depends(get_current_admin),
) -> ApiResponse[UserRead]:
    """Replace a user's name, email, and password; status is left unchanged."""
    user = await user_service.replace_user(db, user_id, data)
    await record_audit(
        db,
        request,
        actor=_admin.username,
        action=AuditAction.USER_REPLACE,
        resource_type=AuditResourceType.USER,
        resource_id=str(user.id),
        details={"email": user.email},
    )
    return ApiResponse(code=CODE_UPDATED, message=MSG_UPDATED, data=user)


@router.patch("/{user_id}", response_model=ApiResponse[UserRead], summary="Partially update a user")
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _admin: PlatformAdmin = Depends(get_current_admin),
) -> ApiResponse[UserRead]:
    """Partially update a user's name, email, or status."""
    user = await user_service.update_user(db, user_id, data)
    await record_audit(
        db,
        request,
        actor=_admin.username,
        action=AuditAction.USER_UPDATE,
        resource_type=AuditResourceType.USER,
        resource_id=str(user.id),
        details={"changed_fields": sorted(data.model_dump(exclude_unset=True).keys())},
    )
    return ApiResponse(code=CODE_UPDATED, message=MSG_UPDATED, data=user)


@router.delete("/{user_id}", response_model=ApiResponse[None], summary="Delete a user")
async def delete_user(
    user_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _admin: PlatformAdmin = Depends(get_current_admin),
) -> ApiResponse[None]:
    """Delete a user by id."""
    await user_service.delete_user(db, user_id)
    await record_audit(
        db,
        request,
        actor=_admin.username,
        action=AuditAction.USER_DELETE,
        resource_type=AuditResourceType.USER,
        resource_id=str(user_id),
    )
    return ApiResponse(code=CODE_DELETED, message=MSG_DELETED, data=None)


def _to_user_list_data(users: list[User], page: int, limit: int, total: int) -> UserListData:
    return UserListData(
        data=[UserRead.model_validate(u) for u in users],
        pagination=Pagination(
            page=page,
            limit=limit,
            total_items=total,
            total_pages=total_pages(total, limit),
        ),
    )
