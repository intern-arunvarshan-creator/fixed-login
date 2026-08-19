# Append-only audit log

The audit log is append-only: repositories expose insert and list only — no update or delete. This keeps Platform Admin actions tamper-evident.

## Consequences

- No update/delete endpoints or repository functions exist for audit entries.
- Retention/archival is a future decision, recorded here so it is not forgotten.
