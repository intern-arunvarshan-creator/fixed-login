from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.audit import record_audit
from app.database.database import get_db
from app.exceptions.errors import ApiError
from app.models.enums import AuditAction, AuditResourceType
from app.schemas.auth import (
    CODE_LOGIN_OK,
    CODE_REFRESH_OK,
    MSG_LOGIN_OK,
    MSG_REFRESH_OK,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.common import ApiResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login", response_model=ApiResponse[TokenResponse], summary="Log in and obtain tokens"
)
async def login(
    credentials: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    try:
        token = await auth_service.login(db, credentials)
    except ApiError:
        await _audit_login(db, request, credentials, success=False)
        raise
    await _audit_login(db, request, credentials, success=True)
    return ApiResponse(code=CODE_LOGIN_OK, message=MSG_LOGIN_OK, data=token)


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
    summary="Exchange a refresh token for new tokens",
)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    token = await auth_service.refresh(db, payload)
    return ApiResponse(code=CODE_REFRESH_OK, message=MSG_REFRESH_OK, data=token)


async def _audit_login(
    db: AsyncSession, request: Request, credentials: LoginRequest, *, success: bool
) -> None:
    await record_audit(
        db,
        request,
        actor=credentials.username,
        action=AuditAction.LOGIN_SUCCESS if success else AuditAction.LOGIN_FAILURE,
        resource_type=AuditResourceType.AUTH,
        resource_id=credentials.username,
    )
