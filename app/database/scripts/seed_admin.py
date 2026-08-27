"""Create or reset Platform Admins (dev: admin1..admin5@example.com, all super_admin)."""

import argparse
import asyncio
import os

from sqlalchemy import select
from sqlmodel import col

from app.core.security import hash_password
from app.database.database import async_session_factory
from app.database.scripts.seed_rbac import assign_super_admin, ensure_catalog
from app.models.platform_admin import PlatformAdmin

DEFAULT_DEV_EMAILS = [f"admin{i}@example.com" for i in range(1, 6)]
DEFAULT_DEV_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "Admin@1234")  # noqa: S105


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


async def seed_dev_team() -> None:
    for i, email in enumerate(DEFAULT_DEV_EMAILS, start=1):
        await seed(username=f"admin{i}", email=email, password=DEFAULT_DEV_PASSWORD)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--email",
        default=None,
        help="Seed a single admin (production provisioning); default seeds the 5 dev admins",
    )
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default=DEFAULT_DEV_PASSWORD)
    args = parser.parse_args()
    if args.email:
        asyncio.run(seed(args.username, args.email, args.password))
    else:
        asyncio.run(seed_dev_team())


if __name__ == "__main__":
    main()
