"""Pagination helper tests."""

from app.utils.pagination import total_pages


def test_total_pages_exact_division() -> None:
    assert total_pages(20, 20) == 1


def test_total_pages_rounds_up() -> None:
    assert total_pages(21, 20) == 2


def test_total_pages_zero_items() -> None:
    assert total_pages(0, 20) == 0
