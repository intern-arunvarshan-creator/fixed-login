"""Service health business logic."""

import logging

from app.exceptions.exceptions import ServiceUnavailableError
from app.repositories import health_repository

logger = logging.getLogger("app.services.health")


async def check() -> None:
    """Verify the database is reachable; raise a typed error when it is not."""
    try:
        await health_repository.ping()
    except Exception:
        logger.exception("database health check failed")
        raise ServiceUnavailableError() from None
