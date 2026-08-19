# snake_case for all JSON field names

All API JSON uses `snake_case` field names — `created_at`, `total_items`, `total_pages` — rather than `camelCase`. Pydantic fields serialize as-is, so the wire format matches the Python/SQLAlchemy attribute names and there is one convention for clients and code alike.

## Considered Options

- **`camelCase`** — rejected: it required `serialization_alias` on every multi-word field, drifted from the Python/SQLAlchemy names, and offered no benefit (no JS/TS client contract exists to justify it).
