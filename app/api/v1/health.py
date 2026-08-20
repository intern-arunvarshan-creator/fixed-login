from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.health import CODE_DOWN, CODE_OK, MSG_DOWN, MSG_OK

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=ApiResponse[dict[str, str]],
    summary="Check service and database health",
)
async def health_check(db: AsyncSession = Depends(get_db)) -> ApiResponse[dict[str, str]]:
    """Report whether the service and its database connection are up."""
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
