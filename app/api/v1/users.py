"""User CRUD routes."""

import uuid

from fastapi import APIRouter, Depends, Query, Request

from app.api.audit import record_audit
from app.api.deps import require_permission
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
from app.schemas.common import ApiResponse, ListData, Pagination
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
async def create_user(
    data: UserCreate,
    request: Request,
    _admin: PlatformAdmin = Depends(require_permission(PermissionName.USER_CREATE)),
) -> ApiResponse[UserRead]:
    """Create a new user with a name, email, and password."""
    user = await user_service.create_user(data)
    resp = ApiResponse[UserRead](code=CODE_CREATED, message=MSG_CREATED, data=user)
    await record_audit(
        request=request,
        actor=_admin.username,
        action=AuditAction.USER_CREATE,
        resource_type=AuditResourceType.USER,
        resource_id=str(user.id),
        details={"email": user.email, "name": user.name},
        payload=data.model_dump(mode="json"),
        response=resp.model_dump(mode="json"),
    )
    return resp


@router.get("", response_model=ApiResponse[ListData[UserRead]], summary="List users")
async def list_users(
    page: int = Query(DEFAULT_PAGE, ge=MIN_PAGE),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE),
    search: str | None = Query(None, description="Search by name or email"),
    status: UserStatusFilter = Query(UserStatusFilter.ALL, description="Filter by user status"),
    _admin: PlatformAdmin = Depends(require_permission(PermissionName.USER_READ)),
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
        data=ListData[UserRead](
            data=[UserRead.model_validate(u) for u in users],
            pagination=Pagination.from_total(page, limit, total),
        ),
    )


@router.get("/{user_id}", response_model=ApiResponse[UserRead], summary="Get a user")
async def get_user(
    user_id: uuid.UUID,
    _admin: PlatformAdmin = Depends(require_permission(PermissionName.USER_READ)),
) -> ApiResponse[UserRead]:
    """Fetch a single user by id."""
    user = await user_service.get_user(user_id)
    return ApiResponse(code=CODE_FETCHED, message=MSG_FETCHED, data=user)


@router.put("/{user_id}", response_model=ApiResponse[UserRead], summary="Fully replace a user")
async def replace_user(
    user_id: uuid.UUID,
    data: UserReplace,
    request: Request,
    _admin: PlatformAdmin = Depends(require_permission(PermissionName.USER_REPLACE)),
) -> ApiResponse[UserRead]:
    """Replace a user's name, email, and password; status is left unchanged."""
    user = await user_service.replace_user(user_id=user_id, data=data)
    resp = ApiResponse[UserRead](code=CODE_UPDATED, message=MSG_UPDATED, data=user)
    await record_audit(
        request=request,
        actor=_admin.username,
        action=AuditAction.USER_REPLACE,
        resource_type=AuditResourceType.USER,
        resource_id=str(user.id),
        details={"email": user.email},
        payload=data.model_dump(mode="json"),
        response=resp.model_dump(mode="json"),
    )
    return resp


@router.patch("/{user_id}", response_model=ApiResponse[UserRead], summary="Partially update a user")
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    request: Request,
    _admin: PlatformAdmin = Depends(require_permission(PermissionName.USER_UPDATE)),
) -> ApiResponse[UserRead]:
    """Partially update a user's name, email, or status."""
    user = await user_service.update_user(user_id=user_id, data=data)
    resp = ApiResponse[UserRead](code=CODE_UPDATED, message=MSG_UPDATED, data=user)
    await record_audit(
        request=request,
        actor=_admin.username,
        action=AuditAction.USER_UPDATE,
        resource_type=AuditResourceType.USER,
        resource_id=str(user.id),
        details={"changed_fields": sorted(data.model_dump(exclude_unset=True).keys())},
        payload=data.model_dump(mode="json", exclude_unset=True),
        response=resp.model_dump(mode="json"),
    )
    return resp


@router.delete("/{user_id}", response_model=ApiResponse[None], summary="Delete a user")
async def delete_user(
    user_id: uuid.UUID,
    request: Request,
    _admin: PlatformAdmin = Depends(require_permission(PermissionName.USER_DELETE)),
) -> ApiResponse[None]:
    """Delete a user by id."""
    await user_service.delete_user(user_id)
    resp = ApiResponse[None](code=CODE_DELETED, message=MSG_DELETED, data=None)
    await record_audit(
        request=request,
        actor=_admin.username,
        action=AuditAction.USER_DELETE,
        resource_type=AuditResourceType.USER,
        resource_id=str(user_id),
        response=resp.model_dump(mode="json"),
    )
    return resp
