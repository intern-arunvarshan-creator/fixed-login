# platform-admin-v2

FastAPI backend where **Platform Admins** log in and manage platform **Users**, with an append-only audit log.

## Stack

Python 3.12 · FastAPI · SQLModel (tables) + Pydantic v2 (DTOs) · SQLAlchemy 2 async · asyncpg · PostgreSQL · Alembic · python-jose · bcrypt · OpenTelemetry · stdlib JSON logging.

## Structure

Every file and folder has a single responsibility. Keep this map updated (rule 18).

platform-admin-v2/
├── .github/workflows/ci.yml    # CI: lint, types, security scan, tests
├── .pre-commit-config.yaml     # git hooks (whitespace, ruff)
├── .python-version             # pinned Python 3.12
├── .gitignore                  # files git must not track
├── .env.example                # env var template (committed)
├── alembic.ini                 # Alembic config
├── alembic/
│   ├── env.py                  # async migration runner (reads model metadata)
│   └── versions/               # migration scripts (0001_initial_schema, ...)
├── app/
│   ├── main.py                 # FastAPI entrypoint; wires routers + middleware + tracing
│   ├── database.py             # async engine, session factory, get_db dependency
│   ├── api/
│   │   ├── deps.py             # get_current_admin auth dependency
│   │   ├── audit.py            # request → audit-context helper
│   │   └── v1/
│   │       ├── health.py       # GET /health
│   │       ├── auth.py         # POST /api/v1/auth/login + /refresh
│   │       ├── users.py        # user CRUD routes
│   │       └── audit_logs.py   # GET /api/v1/audit-logs
│   ├── core/
│   │   ├── config.py           # Settings (from env)
│   │   ├── constants.py        # pagination + header constants
│   │   ├── security.py         # bcrypt hashing + JWT
│   │   ├── logging.py          # structured JSON logging + request_id
│   │   └── tracing.py          # OpenTelemetry setup
│   ├── exceptions/
│   │   ├── errors.py           # ApiError + error catalog
│   │   └── handlers.py         # exception → envelope handlers
│   ├── middleware/
│   │   ├── request_context.py  # sets request_id per request
│   │   └── logging.py          # one access-log line per request
│   ├── models/
│   │   ├── __init__.py         # re-exports models (registers tables for Alembic)
│   │   ├── enums.py            # UserStatus enum
│   │   ├── user.py             # users table
│   │   ├── platform_admin.py   # platform_admins table
│   │   └── audit_log.py        # audit_logs table
│   ├── repositories/
│   │   ├── auth_repository.py  # admin lookup
│   │   ├── user_repository.py  # all user SQL
│   │   └── audit_repository.py # audit SQL (insert + list only — append-only)
│   ├── schemas/
│   │   ├── common.py           # ApiResponse envelope + Pagination
│   │   ├── auth.py             # auth DTOs
│   │   ├── user.py             # user DTOs + password policy
│   │   ├── audit.py            # audit DTOs
│   │   └── health.py           # health result codes/messages
│   ├── services/
│   │   ├── auth_service.py     # login business logic
│   │   ├── user_service.py     # user business rules
│   │   └── audit_service.py    # audit recording (best-effort)
│   └── utils/
│       └── pagination.py       # total_pages helper
├── docs/
│   ├── standards.md            # the coding rules
│   ├── api.md                  # API reference
│   └── adr/                    # architecture decision records
├── scripts/
│   └── seed_admin.py           # create/reset a Platform Admin manually
├── tests/
│   ├── conftest.py             # env setup + TestClient fixture
│   └── unit/                   # unit tests (one file per module)
├── CONTEXT.md                  # domain glossary
├── README.md                   # this file
└── pyproject.toml              # project + tooling config

## Run

See `docs/api.md` for the full walkthrough. Quick start:

uv sync
uv run python -m alembic upgrade head
uv run app

## Checks before committing

Run all of these from `platform-admin-v2/` before you commit. CI runs the same checks on every push/PR.

```bash
# 1. Format (rewrites files to match the style)
uv run ruff format .

# 2. Lint (--fix repairs what it can)
uv run ruff check --fix .

# 3. Type check
uv run mypy app

# 4. Security scan
uv run bandit -c pyproject.toml -r app

# 5. Tests
uv run pytest
```

All five must pass before you commit. To verify *without* rewriting files, CI uses the check-only forms:

```bash
uv run ruff format --check .
uv run ruff check .
```

Your git hooks already run ruff on `git commit`. If you haven't installed them yet, do it once:

```bash
uv run pre-commit install
```
