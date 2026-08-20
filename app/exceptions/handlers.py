import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions.errors import (
    INTERNAL_ERROR,
    ApiError,
    email_already_registered,
    validation_failed,
)

logger = logging.getLogger("app.exceptions")

# Pydantic prefixes messages from AfterValidator (ValueError) with this.
PYDANTIC_VALUE_ERROR_PREFIX = "Value error, "


def _envelope(code: str, message: str, data: Any = None, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message, "data": data},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        return _envelope(exc.code, exc.message, exc.data, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for err in exc.errors():
            loc = [str(part) for part in err.get("loc", []) if part != "body"]
            field = ".".join(loc) or "body"
            issue = err.get("msg", "").removeprefix(PYDANTIC_VALUE_ERROR_PREFIX)
            errors.append((field, issue))
        error = validation_failed(errors)
        return _envelope(error.code, error.message, error.data, error.status_code)

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        constraint = (getattr(exc.orig, "constraint_name", "") or "").lower()
        if "email" in constraint:
            error = email_already_registered()
        else:
            error = ApiError(409, "E_409_CONFLICT", "A conflict occurred")
        return _envelope(error.code, error.message, error.data, error.status_code)

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _envelope(f"E_{exc.status_code}_ERROR", str(exc.detail), None, exc.status_code)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s", request.url.path)
        return _envelope(
            INTERNAL_ERROR.code,
            INTERNAL_ERROR.message,
            None,
            INTERNAL_ERROR.status_code,
        )
