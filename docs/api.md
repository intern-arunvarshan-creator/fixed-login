# API Reference

Base URL: `http://127.0.0.1:8000`

## Conventions

- All responses use the envelope `{ "code": string, "message": string, "data": any }`.
- All JSON field names are `snake_case`.
- Protected routes require `Authorization: Bearer <access_token>`.

## Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/login` | no | `{username, password}` → access + refresh tokens |
| POST | `/api/v1/auth/refresh` | no | `{refresh_token}` → fresh token pair |

## Users

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/users` | yes | create a user |
| GET | `/api/v1/users` | yes | list (page, limit, search, status) |
| GET | `/api/v1/users/{user_id}` | yes | get one user |
| PUT | `/api/v1/users/{user_id}` | yes | full replace |
| PATCH | `/api/v1/users/{user_id}` | yes | partial update |
| DELETE | `/api/v1/users/{user_id}` | yes | delete |

## Audit

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/audit-logs` | yes | list (page, limit, actor, action, resource_type) — append-only, no writes |

## Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | no | service + database liveness |

## Walkthrough

See the README for a curl walkthrough; login → use the access token on protected routes.
