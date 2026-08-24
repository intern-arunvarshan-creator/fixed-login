"""Create (or reset) a Platform Admin — defaults to admin@gmail.com / Admin@1234.

Usage (dev defaults):
    uv run python app/database/scripts/seed_admin.py

Override:
    uv run python app/database/scripts/seed_admin.py \\
        --username admin --email admin@gmail.com --password 'Admin@1234'
"""

import argparse
import asyncio

from sqlalchemy import select
from sqlmodel import col

from app.core.security import hash_password
from app.database.database import async_session_factory
from app.database.scripts.seed_rbac import assign_super_admin, ensure_catalog
from app.models.platform_admin import PlatformAdmin


async def seed(username: str, email: str, password: str) -> None:
    async with async_session_factory() as db:
        result = await db.execute(select(PlatformAdmin).where(col(PlatformAdmin.email) == email))
        admin = result.scalar_one_or_none()
        if admin is not None:
            admin.username = username
            admin.hashed_password = hash_password(password)
        else:
            admin = PlatformAdmin(
                username=username, email=email, hashed_password=hash_password(password)
            )
            db.add(admin)
        await ensure_catalog(db)
        await assign_super_admin(db, admin.id)
        await db.commit()
    print(f"PlatformAdmin '{email}' is ready.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="admin")
    parser.add_argument("--email", default="admin@gmail.com")
    parser.add_argument(
        "--password",
        default="Admin@1234",  # noqa: S105  # nosec B105  (dev-only default; override in real envs)
    )
    args = parser.parse_args()
    asyncio.run(seed(args.username, args.email, args.password))


if __name__ == "__main__":
    main()
