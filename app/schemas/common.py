
from pydantic import BaseModel


class ApiResponse[T](BaseModel):
    code: str
    message: str
    data: T | None = None


class Pagination(BaseModel):
    page: int
    limit: int
    total_items: int
    total_pages: int
