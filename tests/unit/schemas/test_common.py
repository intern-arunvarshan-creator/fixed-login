"""Common schema (DTO) tests."""

from app.schemas.common import ApiResponse, Pagination


def test_api_response_generic() -> None:
    assert ApiResponse[str](code="S", message="ok", data="x").data == "x"


def test_pagination_model() -> None:
    p = Pagination(page=1, limit=20, total_items=5, total_pages=1)
    assert p.total_items == 5
