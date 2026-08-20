"""Create (or reset) a Platform Admin directly in the database.

Usage:
    uv run python scripts/seed_admin.py --username admin --password 'S3cureP@ss'
"""

import argparse
import asyncio

from sqlalchemy import select
from sqlmodel import col

from app.core.security import hash_password
from app.database.database import async_session_factory
from app.models.platform_admin import PlatformAdmin


async def seed(username: str, password: str) -> None:
    async with async_session_factory() as db:
        result = await db.execute(
            select(PlatformAdmin).where(col(PlatformAdmin.username) == username)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.hashed_password = hash_password(password)
        else:
            db.add(PlatformAdmin(username=username, hashed_password=hash_password(password)))
        await db.commit()
    print(f"PlatformAdmin '{username}' is ready.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    asyncio.run(seed(args.username, args.password))


if __name__ == "__main__":
    main()
