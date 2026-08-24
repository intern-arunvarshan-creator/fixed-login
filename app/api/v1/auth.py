"""Auth routes: login, token refresh, forgot password, and logout."""

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.api.audit import record_audit
from app.api.deps import bearer_scheme, get_current_admin
from app.exceptions.errors import ApiError, not_authenticated
from app.models.enums import AuditAction, AuditResourceType
from app.models.platform_admin import PlatformAdmin
from app.schemas.auth import (
    CODE_LOGIN_OK,
    CODE_LOGOUT_OK,
    CODE_OTP_SENT,
    CODE_OTP_VERIFIED,
    CODE_PASSWORD_UPDATED,
    CODE_REFRESH_OK,
    MSG_LOGIN_OK,
    MSG_LOGOUT_OK,
    MSG_OTP_SENT,
    MSG_OTP_VERIFIED,
    MSG_PASSWORD_UPDATED,
    MSG_REFRESH_OK,
    GenerateOtpRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UpdatePasswordRequest,
    VerifyOtpRequest,
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
) -> ApiResponse[TokenResponse]:
    """Authenticate a platform admin and return access and refresh tokens."""
    try:
        token = await auth_service.login(credentials)
    except ApiError:
        await _audit_login(request=request, credentials=credentials, success=False)
        raise
    await _audit_login(request=request, credentials=credentials, success=True)
    return ApiResponse(code=CODE_LOGIN_OK, message=MSG_LOGIN_OK, data=token)


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
    summary="Exchange a refresh token for new tokens",
)
async def refresh(payload: RefreshRequest) -> ApiResponse[TokenResponse]:
    """Exchange a valid refresh token for a new access and refresh token pair."""
    token = await auth_service.refresh(payload)
    return ApiResponse(code=CODE_REFRESH_OK, message=MSG_REFRESH_OK, data=token)


@router.post(
    "/generate-otp",
    response_model=ApiResponse[None],
    summary="Request a password reset OTP",
)
async def generate_otp(payload: GenerateOtpRequest) -> ApiResponse[None]:
    """Validate that the admin account exists and is active before an OTP is issued."""
    await auth_service.generate_otp(payload)
    return ApiResponse(code=CODE_OTP_SENT, message=MSG_OTP_SENT, data=None)


@router.post(
    "/verify-otp",
    response_model=ApiResponse[None],
    summary="Verify the password reset OTP",
)
async def verify_otp(payload: VerifyOtpRequest) -> ApiResponse[None]:
    """Verify the OTP sent for the given email."""
    await auth_service.verify_otp(payload)
    return ApiResponse(code=CODE_OTP_VERIFIED, message=MSG_OTP_VERIFIED, data=None)


@router.post(
    "/update-password",
    response_model=ApiResponse[None],
    summary="Set a new password",
)
async def update_password(payload: UpdatePasswordRequest, request: Request) -> ApiResponse[None]:
    """Set a new password for the admin identified by email."""
    admin = await auth_service.update_password(payload)
    await record_audit(
        request=request,
        actor=admin.username,
        action=AuditAction.PASSWORD_RESET_SUCCESS,
        resource_type=AuditResourceType.AUTH,
        resource_id=admin.email,
    )
    return ApiResponse(code=CODE_PASSWORD_UPDATED, message=MSG_PASSWORD_UPDATED, data=None)


@router.post(
    "/logout",
    response_model=ApiResponse[None],
    summary="Log out the current admin",
)
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    admin: PlatformAdmin = Depends(get_current_admin),
) -> ApiResponse[None]:
    """Log out the current admin, revoking both the access token and its linked refresh token."""
    if credentials is None:
        raise not_authenticated()
    await auth_service.logout(access_token=credentials.credentials)
    await record_audit(
        request=request,
        actor=admin.username,
        action=AuditAction.LOGOUT,
        resource_type=AuditResourceType.AUTH,
        resource_id=admin.email,
    )
    return ApiResponse(code=CODE_LOGOUT_OK, message=MSG_LOGOUT_OK, data=None)


async def _audit_login(request: Request, credentials: LoginRequest, success: bool) -> None:
    await record_audit(
        request=request,
        actor=credentials.email,
        action=AuditAction.LOGIN_SUCCESS if success else AuditAction.LOGIN_FAILURE,
        resource_type=AuditResourceType.AUTH,
        resource_id=credentials.email,
    )
