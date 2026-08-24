"""Health endpoint result codes, messages, and DTO."""

from enum import StrEnum

from pydantic import BaseModel

CODE_OK = "S_200_HEALTH_OK"
MSG_OK = "Service is healthy"


class HealthStatus(StrEnum):
    """Liveness state of a service component."""

    UP = "up"
    DOWN = "down"


class HealthRead(BaseModel):
    """Service and database liveness report."""

    status: HealthStatus
    database: HealthStatus
