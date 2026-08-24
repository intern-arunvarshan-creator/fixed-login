from pydantic import BaseModel

from app.utils.pagination import total_pages


class ApiResponse[T](BaseModel):
    code: str
    message: str
    data: T | None = None


class Pagination(BaseModel):
    page: int
    limit: int
    total_items: int
    total_pages: int

    @classmethod
    def from_total(cls, page: int, limit: int, total_items: int) -> "Pagination":
        """Build a ``Pagination``, computing ``total_pages`` from the totals."""
        return cls(
            page=page,
            limit=limit,
            total_items=total_items,
            total_pages=total_pages(total_items=total_items, limit=limit),
        )


class ListData[T](BaseModel):
    data: list[T]
    pagination: Pagination
