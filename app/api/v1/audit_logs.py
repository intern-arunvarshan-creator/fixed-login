"""Audit log listing routes."""

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
    AuditActionFilter,
    AuditResourceType,
    AuditResourceTypeFilter,
    PermissionName,
    resolve_filter,
)
from app.models.platform_admin import PlatformAdmin
from app.schemas.audit import CODE_LISTED, MSG_LISTED, AuditLogRead
from app.schemas.common import ApiResponse, ListData, build_list_data
from app.services import audit_service

router = APIRouter(tags=["Audit"])


@router.get(
    "/audit-logs",
    response_model=ApiResponse[ListData[AuditLogRead]],
    summary="List audit logs",
)
@audit(
    action=AuditAction.AUDIT_READ,
    resource_type=AuditResourceType.AUDIT,
)
async def list_audit_logs(
    request: Request,
    page: int = Query(DEFAULT_PAGE, ge=MIN_PAGE),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE),
    actor: str | None = Query(None, description="Filter by actor (email)"),
    action: AuditActionFilter = Query(AuditActionFilter.ALL, description="Filter by audit action"),
    resource_type: AuditResourceTypeFilter = Query(
        AuditResourceTypeFilter.ALL, description="Filter by resource type"
    ),
    admin: PlatformAdmin = Depends(get_current_admin),
    _: None = Depends(require_permission(PermissionName.AUDIT_READ)),
) -> ApiResponse[ListData[AuditLogRead]]:
    """List audit log entries, paginated and filterable by actor, action, or resource type."""
    entries, total = await audit_service.list_audit_logs(
        page=page,
        limit=limit,
        actor=actor,
        action=resolve_filter(action, AuditAction),
        resource_type=resolve_filter(resource_type, AuditResourceType),
    )
    return ApiResponse(
        code=CODE_LISTED,
        message=MSG_LISTED,
        data=build_list_data(AuditLogRead, entries, page=page, limit=limit, total=total),
    )
