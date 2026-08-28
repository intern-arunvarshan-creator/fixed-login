# AGENTS.md

Repo guardrails for AI agents. Full rules: `docs/standards.md`.

## Schema changes

Generate every migration with Alembic autogenerate — it writes the version file:

```bash
uv run alembic revision --autogenerate -m "add foo column"
uv run alembic upgrade head
```

Review the generated file in `alembic/versions/`; edit it only if autogenerate missed a change. Do not create or hand-write a version file — the revision id, `down_revision`, and DDL come from Alembic.

Data changes (seeds, backfills) live in idempotent scripts under `app/database/scripts/`, never in a migration.

If `alembic` fails with `Can't locate revision`, the database predates the squashed history — reset it (drop & recreate, then `upgrade head` + seed) rather than editing version files.

## Before committing

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
```
