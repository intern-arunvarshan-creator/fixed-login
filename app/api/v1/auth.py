from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.common import ApiResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])

CODE_LOGIN_OK = "S_200_AUTH_LOGIN_OK"
MSG_LOGIN_OK = "Login successful"
CODE_REFRESH_OK = "S_200_AUTH_REFRESH_OK"
MSG_REFRESH_OK = "Token refreshed"


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    summary="Log in and obtain tokens",
)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    token = await auth_service.login(db, credentials)
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
