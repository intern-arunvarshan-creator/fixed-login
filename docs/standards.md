# Coding Standards

Rules for this codebase. Tooling enforces what it can (ruff, mypy, bandit, CI); the rest are review conventions.

## 1. Layering (hard boundary)

Requests flow one way:

`api → services → repositories → models`

- **api** (`app/api/`): routing, request parsing, dependency injection, response shaping. No business logic, no SQL.
- **services** (`app/services/`): business rules. Call repositories. Return model entities.
- **repositories** (`app/repositories/`): the *only* layer that writes SQLAlchemy/SQLModel queries. One repository per model.
- **models** (`app/models/`): table definitions. Import *nothing* from `app` except sibling model modules and pure, dependency-free helpers from `app/utils/` (e.g. `utcnow`).

Hard rules:
- The API layer never calls a repository directly — always through a service.
- Services never return Pydantic DTOs — they return entities; the API layer converts to DTOs.
- Models never import schemas, services, repositories, or config.
- API handlers are thin: parse → call one service function → shape the response (see rule 14).

## 2. Table models and API schemas are separate

Table models (SQLModel) and API schemas (Pydantic) are *different classes*. A table model never crosses the API boundary. Requests/responses are always DTOs.

## 3. Imports

- No single-letter module aliases. `from app.schemas import user as u` is banned.
  Import the module (`from app.schemas import user`) or specific names (`from app.schemas.user import UserCreate`).
- No duplicate imports. ruff enforces ordering and unused imports.

## 4. Naming

- Files/modules: `snake_case`. Repositories: `{thing}_repository.py`. Services: `{thing}_service.py`.
- Functions/variables: `snake_case`. Classes: `PascalCase`. Follow PEP 8.

## 5. Enums over magic strings

Any field with a fixed set of values is a `StrEnum`, stored as a DB enum. No bare `"active"` / `"inactive"` literals scattered in logic.

## 6. Constants live with their domain

Response result codes/messages (`CODE_*`, `MSG_*`) live in the router module that returns them.
Shared infra constants (pagination, header names) live in `app/core/constants.py`.
No business constants inside schema/DTO files.

## 7. Errors

Domain errors raise typed `ApiError`s from `app/exceptions/errors.py`; exception handlers convert them to the response envelope. Services raise errors directly — they never return `None` to mean "not found".

## 8. Types

Everything is type-hinted. `mypy --strict` must pass on `app/`. Avoid `Any`; if you must use it, say why in a comment.

## 9. Async

All I/O is async (`async def` + `await`). No blocking calls in the request path.

## 10. Tests

- Unit tests only (v1). One test file per module.
- 95% coverage gate (CI fails below it).
- Tests are deterministic: no network, no real DB, no sleeps.

## 11. Secrets & config

- `.env` is gitignored; only `.env.example` is committed.
- Secrets are read via `pydantic-settings` into `Settings`; never `os.getenv` scattered in code.
- Passwords are never logged or returned by the API.

## 12. Git

- Trunk-based: short-lived branches off `main`, PR review required before merge.
- Conventional Commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`.

## 13. No unexplained suppressions

No `# noqa` / `type: ignore` unless it is a *deliberate, documented exception with a reason*. The `# noqa: E402` import-order hack is banned — fix the structure instead.

## 14. Thin API layer

API handlers stay tiny — parse input, call **one** service function, return the shaped response. No business logic, no loops, no multi-step orchestration in the router. If a handler grows, the extra work belongs in a service.

_Audit recording and response shaping may add a couple of lines — that's expected. The test is "no business logic here", not a literal line count._

## 15. Small functions

Functions stay short — target **≤15 lines**. When one grows past that, extract the excess into a `_helper()` in the same module (leading underscore = private to that module).

The goal is readability, not the number: if splitting makes the code *harder* to follow, one clear function is better than fragmented helpers. 15 is a target, not a law.

## 16. No hardcoded values

No magic numbers or hardcoded strings in logic. Extract them to a named constant (module-level, or `app/core/constants.py`) or an enum. Obvious literals (`0`, `1`, `""`, `"bearer"`) are fine — anything whose *meaning* isn't obvious from the value itself needs a name.

## 17. DRY — shared code lives in `app/utils/`

A helper used in **two or more** places goes in `app/utils/`. Single-use code stays local (or becomes a `_helper` in its own module). DRY means "don't duplicate the same logic" — not "force every similar-looking two lines into one function."

## 18. Every file/folder explains itself in one line

Each `.py` module starts with a one-line module docstring stating its single responsibility (e.g. `"""User data access (all SQL)."""`). Every file and folder — **at every level, sub-folders and nested files included** — appears in the `README.md` structure map with a one-line description. When you add, move, or remove a file or folder, update that map so it always matches reality. A dev should be able to read the README structure + a file's docstring and know what that file is for without opening it.
