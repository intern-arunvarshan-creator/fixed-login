# Stateless refresh tokens (v1)

Access and refresh tokens are both stateless JWTs. Refresh-token rotation (server-side storage + revocation) is deliberately deferred: it needs a `refresh_tokens` table and more code. Recorded here so this is a known trade-off, not an omission — a stolen refresh token is valid until expiry in v1.
