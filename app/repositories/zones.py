"""Location data access (all SQL)."""

from sqlalchemy import exists, select

from app.database.session import get_session
from app.models.zones import Zone


async def is_zone_table_empty() -> bool:
    """Return True when the zone table contains no rows."""

    db = get_session()
    query = select(exists().where(Zone.id.isnot(None)))
    result = await db.execute(query)
    return not result.scalar_one()