from fastapi import HTTPException, status
from app.models.query_category import QueryCategory
from app.schemas.query_category import (
    QueryCategoryCreate,
    QueryCategoryResponse,
    QueryCategoryUpdate,
)
from app.repositories.query_category import QueryCategoryRepository


class QueryCategoryService:
    """Service class for QueryCategory business logic."""

    def __init__(self, db):
        self.repository = QueryCategoryRepository(db)

    def list_categories(
        self,
        page: int,
        limit: int,
        module: str | None = None,
        status: str | None = None,
    ) -> tuple[list[QueryCategoryResponse], int]:
        """List categories with pagination and optional filters."""
        offset = (page - 1) * limit

        categories = self.repository.get_all(
            skip=offset,
            limit=limit,
            module=module,
            status=status,
        )

        total = self.repository.get_count(
            module=module,
            status=status,
        )

        return [self._to_response(category) for category in categories], total

    def get_category_by_id(
        self,
        category_id: int,
    ) -> QueryCategoryResponse:
        """Get category by ID with validation."""
        category = self.repository.get_by_id(category_id)

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        return self._to_response(category)

    def create_category(
        self,
        category_data: QueryCategoryCreate,
    ) -> QueryCategoryResponse:
        """Create category with business validation."""
        existing = self.repository.get_by_key(category_data.key)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with key '{category_data.key}' already exists",
            )

        category = self.repository.create(category_data)

        return self._to_response(category)

    def update_category(
        self,
        category_id: int,
        category_data: QueryCategoryUpdate,
    ) -> QueryCategoryResponse:
        """Update category with business validation."""
        existing = self.repository.get_by_id(category_id)

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        if (
            category_data.key is not None
            and category_data.key != existing.key
        ):
            key_exists = self.repository.get_by_key(category_data.key)

            if key_exists and key_exists.id != category_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category with key '{category_data.key}' already exists",
                )

        category = self.repository.update(
            category_id,
            category_data,
        )

        return self._to_response(category)

    def delete_category(self, category_id: int) -> None:
        """Soft delete a category."""
        category = self.repository.get_by_id(category_id)

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        self.repository.soft_delete(category_id)

    def seed_data(self) -> dict:
        """Seed initial query categories."""
        initial_data = [
            {
                "module": "RTO Booklet",
                "type": "signature",
                "description": "Signature related",
                "key": "signature_missing",
                "label": "Signature Missing",
                "status": "active",
            },
            {
                "module": "KYC",
                "type": "personal",
                "description": "Personal details",
                "key": "name",
                "label": "Name",
                "status": "active",
            },
        ]

        created_count = self.repository.seed_initial_data(initial_data)

        return {
            "message": f"Seeded {created_count} new categories",
            "total_requested": len(initial_data),
            "created_count": created_count,
        }

    def _to_response(
        self,
        category: QueryCategory,
    ) -> QueryCategoryResponse:
        """Convert SQLAlchemy model to Pydantic response schema."""
        return QueryCategoryResponse(
            id=category.id,
            module=category.module,
            type=category.type,
            description=category.description,
            key=category.key,
            label=category.label,
            status=category.status,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )