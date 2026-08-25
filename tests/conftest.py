"""Pytest configuration and shared fixtures (env vars set before any app import)."""

import os

# ``setdefault`` avoids clobbering values already present in the environment.
# The URL value is irrelevant to the unit tests (all DB access is mocked), but
# it must exist for ``Settings()`` to build.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
