from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.models.query_category import QueryCategory
from app.schemas.query_category import QueryCategoryCreate, QueryCategoryUpdate

class QueryCategoryRepository:
    """Repository class for QueryCategory database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        module: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[QueryCategory]:
        """Fetch all query categories with optional filtering"""
        query = self.db.query(QueryCategory)
        
        if module:
            query = query.filter(QueryCategory.module == module)
        if status:
            query = query.filter(QueryCategory.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    def get_by_id(self, category_id: int) -> Optional[QueryCategory]:
        """Fetch a single query category by ID"""
        return self.db.query(QueryCategory).filter(
            QueryCategory.id == category_id
        ).first()
    
    def get_by_key(self, key: str) -> Optional[QueryCategory]:
        """Fetch a query category by unique key"""
        return self.db.query(QueryCategory).filter(
            QueryCategory.key == key
        ).first()
    
    def create(self, category_data: QueryCategoryCreate) -> QueryCategory:
        """Create a new query category"""
        db_category = QueryCategory(**category_data.dict())
        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)
        return db_category
    
    def update(
        self, 
        category_id: int, 
        category_data: QueryCategoryUpdate
    ) -> Optional[QueryCategory]:
        """Update an existing query category"""
        db_category = self.get_by_id(category_id)
        
        if not db_category:
            return None
        
        update_data = category_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_category, field, value)
        
        self.db.commit()
        self.db.refresh(db_category)
        return db_category
    
    def soft_delete(self, category_id: int) -> Optional[QueryCategory]:
        """Soft delete (mark as inactive) a query category"""
        db_category = self.get_by_id(category_id)
        
        if not db_category:
            return None
        
        db_category.status = "inactive"
        self.db.commit()
        self.db.refresh(db_category)
        return db_category
    
    def seed_initial_data(self, categories: List[dict]) -> int:
        """Seed initial data, skipping existing entries"""
        created_count = 0
        
        for data in categories:
            existing = self.get_by_key(data["key"])
            if not existing:
                self.create(QueryCategoryCreate(**data))
                created_count += 1
        
        return created_count