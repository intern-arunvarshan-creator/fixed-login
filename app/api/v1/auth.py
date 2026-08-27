"""Auth routes: login, token refresh, forgot password, and logout."""

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.api.audit import record_audit
from app.api.deps import bearer_scheme, get_current_admin
from app.exceptions.exceptions import AppError, AuthenticationError
from app.models.enums import ActorType, AuditAction, AuditResourceType
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
    payload = credentials.model_dump(mode="json", exclude_unset=True)
    try:
        token = await auth_service.login(credentials)
    except AppError as exc:
        await record_audit(
            request=request,
            actor=credentials.email,
            actor_type=ActorType.ADMIN.value,
            action=AuditAction.LOGIN_FAILURE,
            resource_type=AuditResourceType.AUTH,
            resource_id=credentials.email,
            details={"error_code": exc.code},
            payload=payload,
        )
        raise
    response: ApiResponse[TokenResponse] = ApiResponse(
        code=CODE_LOGIN_OK, message=MSG_LOGIN_OK, data=token
    )
    await record_audit(
        request=request,
        actor=credentials.email,
        actor_type=ActorType.ADMIN.value,
        action=AuditAction.LOGIN_SUCCESS,
        resource_type=AuditResourceType.AUTH,
        resource_id=credentials.email,
        payload=payload,
        response=response.model_dump(mode="json"),
    )
    return response


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
    summary="Exchange a refresh token for new tokens",
)
async def refresh(payload: RefreshRequest, request: Request) -> ApiResponse[TokenResponse]:
    """Exchange a valid refresh token for a new access and refresh token pair."""
    body = payload.model_dump(mode="json", exclude_unset=True)
    try:
        token = await auth_service.refresh(payload)
    except AppError as exc:
        await record_audit(
            request=request,
            actor=None,
            action=AuditAction.REFRESH_FAILURE,
            resource_type=AuditResourceType.AUTH,
            details={"error_code": exc.code},
            payload=body,
        )
        raise
    response: ApiResponse[TokenResponse] = ApiResponse(
        code=CODE_REFRESH_OK, message=MSG_REFRESH_OK, data=token
    )
    await record_audit(
        request=request,
        actor=None,
        action=AuditAction.REFRESH_SUCCESS,
        resource_type=AuditResourceType.AUTH,
        payload=body,
        response=response.model_dump(mode="json"),
    )
    return response


@router.post(
    "/generate-otp",
    response_model=ApiResponse[None],
    summary="Request a password reset OTP",
)
async def generate_otp(payload: GenerateOtpRequest, request: Request) -> ApiResponse[None]:
    """Validate that the admin account exists and is active before an OTP is issued."""
    body = payload.model_dump(mode="json", exclude_unset=True)
    await auth_service.generate_otp(payload)
    response: ApiResponse[None] = ApiResponse(code=CODE_OTP_SENT, message=MSG_OTP_SENT, data=None)
    await record_audit(
        request=request,
        actor=payload.email,
        actor_type=ActorType.ADMIN.value,
        action=AuditAction.OTP_REQUESTED,
        resource_type=AuditResourceType.AUTH,
        payload=body,
        response=response.model_dump(mode="json"),
    )
    return response


@router.post(
    "/verify-otp",
    response_model=ApiResponse[None],
    summary="Verify the password reset OTP",
)
async def verify_otp(payload: VerifyOtpRequest, request: Request) -> ApiResponse[None]:
    """Verify the OTP sent for the given email."""
    body = payload.model_dump(mode="json", exclude_unset=True)
    try:
        await auth_service.verify_otp(payload)
    except AppError as exc:
        await record_audit(
            request=request,
            actor=payload.email,
            actor_type=ActorType.ADMIN.value,
            action=AuditAction.OTP_VERIFY_FAILURE,
            resource_type=AuditResourceType.AUTH,
            resource_id=payload.email,
            details={"error_code": exc.code},
            payload=body,
        )
        raise
    response: ApiResponse[None] = ApiResponse(
        code=CODE_OTP_VERIFIED, message=MSG_OTP_VERIFIED, data=None
    )
    await record_audit(
        request=request,
        actor=payload.email,
        actor_type=ActorType.ADMIN.value,
        action=AuditAction.OTP_VERIFY_SUCCESS,
        resource_type=AuditResourceType.AUTH,
        resource_id=payload.email,
        payload=body,
        response=response.model_dump(mode="json"),
    )
    return response


@router.post(
    "/update-password",
    response_model=ApiResponse[None],
    summary="Set a new password",
)
async def update_password(payload: UpdatePasswordRequest, request: Request) -> ApiResponse[None]:
    """Set a new password for the admin identified by email."""
    body = payload.model_dump(mode="json", exclude_unset=True)
    try:
        await auth_service.update_password(payload)
    except AppError as exc:
        await record_audit(
            request=request,
            actor=payload.email,
            actor_type=ActorType.ADMIN.value,
            action=AuditAction.PASSWORD_RESET_FAILURE,
            resource_type=AuditResourceType.AUTH,
            resource_id=payload.email,
            details={"error_code": exc.code},
            payload=body,
        )
        raise
    response: ApiResponse[None] = ApiResponse(
        code=CODE_PASSWORD_UPDATED, message=MSG_PASSWORD_UPDATED, data=None
    )
    await record_audit(
        request=request,
        actor=payload.email,
        actor_type=ActorType.ADMIN.value,
        action=AuditAction.PASSWORD_RESET_SUCCESS,
        resource_type=AuditResourceType.AUTH,
        resource_id=payload.email,
        payload=body,
        response=response.model_dump(mode="json"),
    )
    return response


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
        raise AuthenticationError()
    await auth_service.logout(access_token=credentials.credentials)
    response: ApiResponse[None] = ApiResponse(code=CODE_LOGOUT_OK, message=MSG_LOGOUT_OK, data=None)
    await record_audit(
        request=request,
        actor=admin.email,
        actor_type=ActorType.ADMIN.value,
        action=AuditAction.LOGOUT,
        resource_type=AuditResourceType.AUTH,
        resource_id=admin.email,
        response=response.model_dump(mode="json"),
    )
    return response
