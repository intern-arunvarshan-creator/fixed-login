"""Health endpoint."""

from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.schemas.health import CODE_OK, MSG_OK, HealthRead, HealthStatus
from app.services import health_service

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=ApiResponse[HealthRead],
    summary="Check service and database health",
)
async def health_check() -> ApiResponse[HealthRead]:
    """Report whether the service and its database connection are up."""
    await health_service.check()
    return ApiResponse(
        code=CODE_OK,
        message=MSG_OK,
        data=HealthRead(status=HealthStatus.UP, database=HealthStatus.UP),
    )
