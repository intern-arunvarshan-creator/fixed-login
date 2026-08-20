import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.constants import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MIN_PAGE,
    MIN_PAGE_SIZE,
)
from app.database import get_db
from app.models.enums import UserStatus
from app.models.platform_admin import PlatformAdmin
from app.models.user import User
from app.schemas.common import ApiResponse, Pagination
from app.schemas.user import UserCreate, UserListData, UserRead, UserReplace, UserUpdate
from app.services import user_service
from app.utils.pagination import total_pages

router = APIRouter(tags=["Users"])

CODE_CREATED = "S_201_USR_CREATED"
MSG_CREATED = "User created successfully"
CODE_LISTED = "S_200_USR_LIST_OK"
MSG_LISTED = "Users fetched successfully"
CODE_FETCHED = "S_200_USR_FETCH_OK"
MSG_FETCHED = "User fetched successfully"
CODE_UPDATED = "S_200_USR_UPDATED"
MSG_UPDATED = "User updated successfully"
CODE_DELETED = "S_200_USR_DELETED"
MSG_DELETED = "User deleted successfully"


@router.post("", response_model=ApiResponse[UserRead], status_code=201, summary="Create a user")
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _admin: PlatformAdmin = Depends(get_current_admin),
) -> ApiResponse[UserRead]:
    user = await user_service.create_user(db, data)
    return ApiResponse(code=CODE_CREATED, message=MSG_CREATED, data=user)


@router.get("", response_model=ApiResponse[UserListData], summary="List users")
async def list_users(
    page: int = Query(DEFAULT_PAGE, ge=MIN_PAGE),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE),
    search: str | None = Query(None),
    status: UserStatus | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin: PlatformAdmin = Depends(get_current_admin),
) -> ApiResponse[UserListData]:
    users, total = await user_service.list_users(
        db, page=page, limit=limit, search=search, status=status
    )
    body = _to_user_list_data(users, page, limit, total)
    return ApiResponse(code=CODE_LISTED, message=MSG_LISTED, data=body)


@router.get("/{user_id}", response_model=ApiResponse[UserRead], summary="Get a user")
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: PlatformAdmin = Depends(get_current_admin),
) -> ApiResponse[UserRead]:
    user = await user_service.get_user(db, user_id)
    return ApiResponse(code=CODE_FETCHED, message=MSG_FETCHED, data=user)


@router.put("/{user_id}", response_model=ApiResponse[UserRead], summary="Fully replace a user")
async def replace_user(
    user_id: uuid.UUID,
    data: UserReplace,
    db: AsyncSession = Depends(get_db),
    _admin: PlatformAdmin = Depends(get_current_admin),
) -> ApiResponse[UserRead]:
    user = await user_service.replace_user(db, user_id, data)
    return ApiResponse(code=CODE_UPDATED, message=MSG_UPDATED, data=user)


@router.patch("/{user_id}", response_model=ApiResponse[UserRead], summary="Partially update a user")
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: PlatformAdmin = Depends(get_current_admin),
) -> ApiResponse[UserRead]:
    user = await user_service.update_user(db, user_id, data)
    return ApiResponse(code=CODE_UPDATED, message=MSG_UPDATED, data=user)


@router.delete("/{user_id}", response_model=ApiResponse[None], summary="Delete a user")
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: PlatformAdmin = Depends(get_current_admin),
) -> ApiResponse[None]:
    await user_service.delete_user(db, user_id)
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
