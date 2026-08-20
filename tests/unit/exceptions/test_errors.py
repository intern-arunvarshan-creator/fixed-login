"""Error factory tests."""

from app.exceptions.errors import (
    ApiError,
    email_already_registered,
    field_errors,
    invalid_credentials,
    not_authenticated,
    user_not_found,
    validation_failed,
)


def test_api_error_carries_fields() -> None:
    err = ApiError(404, "E_404", "Not found", {"x": 1})
    assert (err.status_code, err.code, err.message, err.data) == (
        404,
        "E_404",
        "Not found",
        {"x": 1},
    )


def test_field_errors_shape() -> None:
    assert field_errors([("email", "bad")]) == {"errors": [{"field": "email", "issue": "bad"}]}


def test_error_factories() -> None:
    assert user_not_found().status_code == 404
    assert email_already_registered().status_code == 409
    assert invalid_credentials().status_code == 401
    assert not_authenticated().status_code == 401
    assert validation_failed([("name", "short")]).status_code == 422
