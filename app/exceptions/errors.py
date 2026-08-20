from dataclasses import dataclass
from typing import Any


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


@dataclass(frozen=True)
class ErrorSpec:
    status_code: int
    code: str
    message: str


VALIDATION_FAILED = ErrorSpec(422, "E_422_VALIDATION_FAILED", "Validation failed")
USER_NOT_FOUND = ErrorSpec(404, "E_404_USR_NOT_FOUND", "User not found")
EMAIL_EXISTS = ErrorSpec(409, "E_409_USR_EMAIL_EXISTS", "Email is already registered")
INVALID_CREDENTIALS = ErrorSpec(
    401, "E_401_AUTH_INVALID_CREDENTIALS", "Invalid username or password"
)
NOT_AUTHENTICATED = ErrorSpec(401, "E_401_NOT_AUTHENTICATED", "Not authenticated")
INTERNAL_ERROR = ErrorSpec(
    500, "E_500_INTERNAL_ERROR", "Something went wrong. Please try again later."
)


def _make(spec: ErrorSpec, data: dict[str, Any] | None = None) -> ApiError:
    return ApiError(spec.status_code, spec.code, spec.message, data)


def field_errors(errors: list[tuple[str, str]]) -> dict[str, Any]:
    return {"errors": [{"field": field, "issue": issue} for field, issue in errors]}


def validation_failed(message: str) -> ApiError:
    return ApiError(VALIDATION_FAILED.status_code, VALIDATION_FAILED.code, message)


def validation_failed_with_fields(errors: list[tuple[str, str]]) -> ApiError:
    return _make(VALIDATION_FAILED, field_errors(errors))


def user_not_found() -> ApiError:
    return _make(USER_NOT_FOUND)


def email_already_registered() -> ApiError:
    return _make(EMAIL_EXISTS, field_errors([("email", EMAIL_EXISTS.message)]))


def invalid_credentials() -> ApiError:
    return _make(INVALID_CREDENTIALS)


def not_authenticated() -> ApiError:
    return _make(NOT_AUTHENTICATED)
