"""Convert raised errors into the API response envelope."""

import logging
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ExceptionHandler

from app.exceptions.exceptions import (
    AppError,
    ConflictError,
    EmailExistsError,
    ValidationError,
    field_errors,
)
from app.schemas.common import ApiResponse

logger = logging.getLogger(__name__)

# Pydantic prefixes messages from AfterValidator (ValueError) with this.
PYDANTIC_VALUE_ERROR_PREFIX = "Value error, "


def _body(code: str, message: str, data: Any = None, status_code: int = 200) -> JSONResponse:
    envelope = ApiResponse[Any](code=code, message=message, data=data)
    return JSONResponse(status_code=status_code, content=envelope.model_dump(mode="json"))


async def api_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return _body(exc.code, exc.message, exc.data, exc.status_code)


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for err in exc.errors():
        loc = [str(part) for part in err.get("loc", []) if part != "body"]
        field = ".".join(loc) or "body"
        issue = err.get("msg", "").removeprefix(PYDANTIC_VALUE_ERROR_PREFIX)
        errors.append((field, issue))
    error = ValidationError(data=field_errors(errors))
    return _body(error.code, error.message, error.data, error.status_code)


async def integrity_error_handler(_: Request, exc: IntegrityError) -> JSONResponse:
    constraint = (getattr(exc.orig, "constraint_name", "") or "").lower()
    error = EmailExistsError() if "email" in constraint else ConflictError()
    return _body(error.code, error.message, error.data, error.status_code)


async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _body(f"E_{exc.status_code}_ERROR", str(exc.detail), None, exc.status_code)


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s", request.url.path)
    return _body(AppError.code, AppError.message, None, AppError.status_code)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach every exception handler to the application."""
    handlers = [
        (AppError, api_error_handler),
        (RequestValidationError, validation_error_handler),
        (IntegrityError, integrity_error_handler),
        (StarletteHTTPException, http_error_handler),
        (Exception, unhandled_error_handler),
    ]
    for exc_class, handler in handlers:
        # Starlette types a handler as `(Request, Exception) -> Response`; it
        # cannot express that each handler only receives its own exc_class.
        app.add_exception_handler(exc_class, cast(ExceptionHandler, handler))
