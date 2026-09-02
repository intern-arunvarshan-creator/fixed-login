from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


# Query Category response codes
CODE_CREATED = "CAT_001"
CODE_UPDATED = "CAT_002"
CODE_DELETED = "CAT_003"
CODE_FETCHED = "CAT_004"
CODE_LISTED = "CAT_005"


# Query Category response messages
MSG_CREATED = "Query category created successfully"
MSG_UPDATED = "Query category updated successfully"
MSG_DELETED = "Query category deleted successfully"
MSG_FETCHED = "Query category fetched successfully"
MSG_LISTED = "Query categories listed successfully"


class QueryCategoryBase(BaseModel):
    module: str = Field(..., max_length=100)
    type: str = Field(..., max_length=50)
    description: str | None = None
    key: str = Field(..., max_length=100)
    label: str = Field(..., max_length=255)
    status: Literal["active", "inactive"] = "active"


class QueryCategoryCreate(QueryCategoryBase):
    pass


class QueryCategoryUpdate(BaseModel):
    module: str | None = Field(default=None, max_length=100)
    type: str | None = Field(default=None, max_length=50)
    description: str | None = None
    key: str | None = Field(default=None, max_length=100)
    label: str | None = Field(default=None, max_length=255)
    status: Literal["active", "inactive"] | None = None


class QueryCategoryResponse(QueryCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)