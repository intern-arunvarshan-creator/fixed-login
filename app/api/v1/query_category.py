from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.deps import get_current_admin, get_db, require_permission
from app.models.enums import PermissionName
from app.models.query_category import QueryCategory
from app.services.query_category import QueryCategoryService

router = APIRouter(prefix="/query-category", tags=["Query Category"])


def get_query_category_service(
    session: Session = Depends(get_db),
) -> QueryCategoryService:
    return QueryCategoryService(session)


@router.get("/", dependencies=[Depends(require_permission(PermissionName.QUERY_CATEGORY_READ))])
def list_query_categories(
    service: QueryCategoryService = Depends(get_query_category_service),
    _: dict = Depends(get_current_admin),
):
    return service.get_all()


@router.get(
    "/{category_id}",
    dependencies=[Depends(require_permission(PermissionName.QUERY_CATEGORY_READ))],
)
def get_query_category(
    category_id: int,
    service: QueryCategoryService = Depends(get_query_category_service),
    _: dict = Depends(get_current_admin),
):
    category = service.get_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query category not found",
        )
    return category


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PermissionName.QUERY_CATEGORY_CREATE))],
)
def create_query_category(
    payload: QueryCategory,
    service: QueryCategoryService = Depends(get_query_category_service),
    _: dict = Depends(get_current_admin),
):
    return service.create(payload)


@router.put(
    "/{category_id}",
    dependencies=[Depends(require_permission(PermissionName.QUERY_CATEGORY_UPDATE))],
)
def update_query_category(
    category_id: int,
    payload: QueryCategory,
    service: QueryCategoryService = Depends(get_query_category_service),
    _: dict = Depends(get_current_admin),
):
    category = service.get_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query category not found",
        )
    return service.update(category, payload)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(PermissionName.QUERY_CATEGORY_DELETE))],
)
def delete_query_category(
    category_id: int,
    service: QueryCategoryService = Depends(get_query_category_service),
    _: dict = Depends(get_current_admin),
):
    category = service.get_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query category not found",
        )
    service.delete(category)