"""Zone routes."""

from fastapi import APIRouter, Depends

from app.api.deps import require_permission
from app.models.enums import PermissionName
from app.services.zones import is_zone_table_empty

router = APIRouter(
    prefix="/zones",
    tags=["Zones"],
)


@router.get(
    "/empty",
    response_model=bool,
    summary="Check whether zone table is empty",
)
async def check_zone_table_empty(
    _: None = Depends(require_permission(PermissionName.ZONES_READ)),
) -> bool:
    return await is_zone_table_empty()