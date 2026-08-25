"""User CRUD routes."""

import uuid

from fastapi import APIRouter, Depends, Query, Request

from app.api.audit import audit
from app.api.deps import get_current_admin, require_permission
from app.core.constants import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MIN_PAGE,
    MIN_PAGE_SIZE,
)
from app.models.enums import (
    AuditAction,
    AuditResourceType,
    PermissionName,
    UserStatus,
    UserStatusFilter,
    resolve_filter,
)
from app.models.platform_admin import PlatformAdmin
from app.schemas.common import ApiResponse, ListData, build_list_data
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
    UserRead,
    UserReplace,
    UserUpdate,
)
from app.services import user_service

router = APIRouter(tags=["Users"])


@router.post("", response_model=ApiResponse[UserRead], status_code=201, summary="Create a user")
@audit(
    action=AuditAction.USER_CREATE,
    resource_type=AuditResourceType.USER,
    resource_id=lambda ctx: str(ctx.result.data.id),
    details=lambda ctx: {"email": ctx.result.data.email, "name": ctx.result.data.name},
)
async def create_user(
    data: UserCreate,
    request: Request,
    admin: PlatformAdmin = Depends(get_current_admin),
    _: None = Depends(require_permission(PermissionName.USER_CREATE)),
) -> ApiResponse[UserRead]:
    """Create a new user with a name, email, and password."""
    user = await user_service.create_user(data)
    return ApiResponse(code=CODE_CREATED, message=MSG_CREATED, data=user)


@router.get("", response_model=ApiResponse[ListData[UserRead]], summary="List users")
async def list_users(
    page: int = Query(DEFAULT_PAGE, ge=MIN_PAGE),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE),
    search: str | None = Query(None, description="Search by name or email"),
    status: UserStatusFilter = Query(UserStatusFilter.ALL, description="Filter by user status"),
    _: None = Depends(require_permission(PermissionName.USER_READ)),
) -> ApiResponse[ListData[UserRead]]:
    """List users, paginated and optionally filtered by search text or status."""
    users, total = await user_service.list_users(
        page=page,
        limit=limit,
        search=search,
        status=resolve_filter(status, UserStatus),
    )
    return ApiResponse(
        code=CODE_LISTED,
        message=MSG_LISTED,
        data=build_list_data(UserRead, users, page=page, limit=limit, total=total),
    )


@router.get("/{user_id}", response_model=ApiResponse[UserRead], summary="Get a user")
async def get_user(
    user_id: uuid.UUID,
    _: None = Depends(require_permission(PermissionName.USER_READ)),
) -> ApiResponse[UserRead]:
    """Fetch a single user by id."""
    user = await user_service.get_user(user_id)
    return ApiResponse(code=CODE_FETCHED, message=MSG_FETCHED, data=user)


@router.put("/{user_id}", response_model=ApiResponse[UserRead], summary="Fully replace a user")
@audit(
    action=AuditAction.USER_REPLACE,
    resource_type=AuditResourceType.USER,
    resource_id=lambda ctx: str(ctx.result.data.id),
    details=lambda ctx: {"email": ctx.result.data.email},
)
async def replace_user(
    user_id: uuid.UUID,
    data: UserReplace,
    request: Request,
    admin: PlatformAdmin = Depends(get_current_admin),
    _: None = Depends(require_permission(PermissionName.USER_REPLACE)),
) -> ApiResponse[UserRead]:
    """Replace a user's name, email, and password; status is left unchanged."""
    user = await user_service.replace_user(user_id=user_id, data=data)
    return ApiResponse(code=CODE_UPDATED, message=MSG_UPDATED, data=user)


@router.patch("/{user_id}", response_model=ApiResponse[UserRead], summary="Partially update a user")
@audit(
    action=AuditAction.USER_UPDATE,
    resource_type=AuditResourceType.USER,
    resource_id=lambda ctx: str(ctx.result.data.id),
    details=lambda ctx: {"changed_fields": sorted(ctx.body.model_dump(exclude_unset=True).keys())},
)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    request: Request,
    admin: PlatformAdmin = Depends(get_current_admin),
    _: None = Depends(require_permission(PermissionName.USER_UPDATE)),
) -> ApiResponse[UserRead]:
    """Partially update a user's name, email, or status."""
    user = await user_service.update_user(user_id=user_id, data=data)
    return ApiResponse(code=CODE_UPDATED, message=MSG_UPDATED, data=user)


@router.delete("/{user_id}", response_model=ApiResponse[None], summary="Delete a user")
@audit(
    action=AuditAction.USER_DELETE,
    resource_type=AuditResourceType.USER,
    resource_id=lambda ctx: str(ctx.args["user_id"]),
)
async def delete_user(
    user_id: uuid.UUID,
    request: Request,
    admin: PlatformAdmin = Depends(get_current_admin),
    _: None = Depends(require_permission(PermissionName.USER_DELETE)),
) -> ApiResponse[None]:
    """Delete a user by id."""
    await user_service.delete_user(user_id)
    return ApiResponse(code=CODE_DELETED, message=MSG_DELETED, data=None)
