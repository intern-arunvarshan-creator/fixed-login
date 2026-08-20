import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.common import Pagination

CODE_LISTED = "S_200_AUDIT_LIST_OK"
MSG_LISTED = "Audit logs fetched successfully"


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    details: dict[str, Any] | None
    request_id: str | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime


class AuditLogListData(BaseModel):
    data: list[AuditLogRead]
    pagination: Pagination
