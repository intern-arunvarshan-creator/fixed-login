from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import ApiResponse

router = APIRouter(tags=["Health"])

CODE_OK = "S_200_HEALTH_OK"
MSG_OK = "Service is healthy"
CODE_DOWN = "E_503_HEALTH_DOWN"
MSG_DOWN = "Service is unhealthy"


@router.get(
    "/health",
    response_model=ApiResponse[dict[str, str]],
    summary="Check service and database health",
)
async def health_check(db: AsyncSession = Depends(get_db)) -> ApiResponse[dict[str, str]]:
    try:
        await db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return ApiResponse(
            code=CODE_DOWN,
            message=MSG_DOWN,
            data={"status": "down", "database": "down"},
        )
    return ApiResponse(
        code=CODE_OK,
        message=MSG_OK,
        data={"status": "up", "database": "up"},
    )
