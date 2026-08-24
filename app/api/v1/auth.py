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
    resp = ApiResponse[TokenResponse](code=CODE_LOGIN_OK, message=MSG_LOGIN_OK, data=token)
    await _audit_login(request=request, credentials=credentials, success=True, response=resp)
    return resp


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
async def generate_otp(payload: GenerateOtpRequest, request: Request) -> ApiResponse[None]:
    """Validate that the admin account exists and is active before an OTP is issued."""
    await auth_service.generate_otp(payload)
    resp = ApiResponse[None](code=CODE_OTP_SENT, message=MSG_OTP_SENT, data=None)
    await record_audit(
        request=request,
        actor=payload.email,
        action=AuditAction.OTP_REQUESTED,
        resource_type=AuditResourceType.AUTH,
        resource_id=payload.email,
        payload=payload.model_dump(mode="json"),
        response=resp.model_dump(mode="json"),
    )
    return resp


@router.post(
    "/verify-otp",
    response_model=ApiResponse[None],
    summary="Verify the password reset OTP",
)
async def verify_otp(payload: VerifyOtpRequest, request: Request) -> ApiResponse[None]:
    """Verify the OTP sent for the given email."""
    try:
        await auth_service.verify_otp(payload)
    except ApiError:
        await _audit_verify_otp(request=request, payload=payload, success=False)
        raise
    resp = ApiResponse[None](code=CODE_OTP_VERIFIED, message=MSG_OTP_VERIFIED, data=None)
    await _audit_verify_otp(request=request, payload=payload, success=True, response=resp)
    return resp


@router.post(
    "/update-password",
    response_model=ApiResponse[None],
    summary="Set a new password",
)
async def update_password(payload: UpdatePasswordRequest, request: Request) -> ApiResponse[None]:
    """Set a new password for the admin identified by email."""
    admin = await auth_service.update_password(payload)
    resp = ApiResponse[None](code=CODE_PASSWORD_UPDATED, message=MSG_PASSWORD_UPDATED, data=None)
    await record_audit(
        request=request,
        actor=admin.username,
        action=AuditAction.PASSWORD_RESET_SUCCESS,
        resource_type=AuditResourceType.AUTH,
        resource_id=admin.email,
        payload=payload.model_dump(mode="json"),
        response=resp.model_dump(mode="json"),
    )
    return resp


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
    resp = ApiResponse[None](code=CODE_LOGOUT_OK, message=MSG_LOGOUT_OK, data=None)
    await record_audit(
        request=request,
        actor=admin.username,
        action=AuditAction.LOGOUT,
        resource_type=AuditResourceType.AUTH,
        resource_id=admin.email,
        response=resp.model_dump(mode="json"),
    )
    return resp


async def _audit_login(
    request: Request,
    credentials: LoginRequest,
    success: bool,
    response: ApiResponse[TokenResponse] | None = None,
) -> None:
    await record_audit(
        request=request,
        actor=credentials.email,
        action=AuditAction.LOGIN_SUCCESS if success else AuditAction.LOGIN_FAILURE,
        resource_type=AuditResourceType.AUTH,
        resource_id=credentials.email,
        payload=credentials.model_dump(mode="json"),
        response=response.model_dump(mode="json") if response else None,
    )


async def _audit_verify_otp(
    request: Request,
    payload: VerifyOtpRequest,
    success: bool,
    response: ApiResponse[None] | None = None,
) -> None:
    await record_audit(
        request=request,
        actor=payload.email,
        action=AuditAction.OTP_VERIFY_SUCCESS if success else AuditAction.OTP_VERIFY_FAILURE,
        resource_type=AuditResourceType.AUTH,
        resource_id=payload.email,
        payload=payload.model_dump(mode="json"),
        response=response.model_dump(mode="json") if response else None,
    )
