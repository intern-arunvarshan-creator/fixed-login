"""Location business rules."""

from app.repositories.zones import (
    is_zone_table_empty as repository_is_zone_table_empty,
)


async def is_zone_table_empty() -> bool:
    return await repository_is_zone_table_empty()