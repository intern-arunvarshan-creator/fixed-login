"""QueryCategory CRUD routes."""

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_admin,require_permission
from app.models.platform_admin import PlatformAdmin
from app.core.constants import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MIN_PAGE,
    MIN_PAGE_SIZE,
)
from app.models.enums import PermissionName, Status, StatusFilter, resolve_filter
from app.schemas.common import ApiResponse, ListData, build_list_data
from app.schemas.query_category import (
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
    QueryCategoryCreate,
    QueryCategoryResponse,
    QueryCategoryUpdate,
)
from app.services.query_category import (
    create_category,
    delete_category,
    get_category,
    list_categories,
    update_category,
)

router = APIRouter(
    prefix="/query-categories",
    tags=["QueryCategories"],
)


@router.post(
    "",
    response_model=ApiResponse[QueryCategoryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a query category",
)
async def create_query_category(
    data: QueryCategoryCreate,
    admin: PlatformAdmin = Depends(get_current_admin),
    _: None = Depends(require_permission(PermissionName.QUERY_CATEGORY_WRITE)),
) -> ApiResponse[QueryCategoryResponse]:
    entity = await create_category(data, admin_id=admin.id)
    return ApiResponse(code=CODE_CREATED, message=MSG_CREATED, data=entity)


@router.get(
    "",
    response_model=ApiResponse[ListData[QueryCategoryResponse]],
    summary="List query categories",
)
async def list_query_categories(
    page: int = Query(DEFAULT_PAGE, ge=MIN_PAGE),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=MIN_PAGE_SIZE, le=MAX_PAGE_SIZE),
    status: StatusFilter = Query(StatusFilter.ALL, description="Filter by status"),
    _: None = Depends(require_permission(PermissionName.QUERY_CATEGORY_READ)),
) -> ApiResponse[ListData[QueryCategoryResponse]]:
    entities, total = await list_categories(
        page=page,
        limit=limit,
        status=resolve_filter(status, Status),
    )
    return ApiResponse(
        code=CODE_LISTED,
        message=MSG_LISTED,
        data=build_list_data(
            QueryCategoryResponse,
            entities,
            page=page,
            limit=limit,
            total=total,
        ),
    )


@router.get(
    "/{entity_id}",
    response_model=ApiResponse[QueryCategoryResponse],
    summary="Get a query category",
)
async def get_query_category(
    entity_id: int,
    _: None = Depends(require_permission(PermissionName.QUERY_CATEGORY_READ)),
) -> ApiResponse[QueryCategoryResponse]:
    entity = await get_category(entity_id)
    return ApiResponse(code=CODE_FETCHED, message=MSG_FETCHED, data=entity)


@router.patch(
    "/{entity_id}",
    response_model=ApiResponse[QueryCategoryResponse],
    summary="Update a query category",
)
async def update_query_category(
    entity_id: int,
    data: QueryCategoryUpdate,
    admin: PlatformAdmin = Depends(get_current_admin),
    _: None = Depends(require_permission(PermissionName.QUERY_CATEGORY_WRITE)),
) -> ApiResponse[QueryCategoryResponse]:

    entity = await update_category(entity_id, data, admin_id=admin.id)

    return ApiResponse(
        code=CODE_UPDATED,
        message=MSG_UPDATED,
        data=entity,
    )


@router.delete(
    "/{entity_id}",
    response_model=ApiResponse[None],
    summary="Delete a query category",
)
async def delete_query_category(
    entity_id: int,
    admin: PlatformAdmin = Depends(get_current_admin),
    _: None = Depends(require_permission(PermissionName.QUERY_CATEGORY_WRITE)),
) -> ApiResponse[None]:
    await delete_category(entity_id, admin_id=admin.id)
    return ApiResponse(code=CODE_DELETED, message=MSG_DELETED, data=None)