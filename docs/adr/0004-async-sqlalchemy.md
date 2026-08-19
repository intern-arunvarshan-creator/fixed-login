# Async SQLAlchemy with asyncpg

All database access uses SQLAlchemy 2 async with the asyncpg driver, so the request path stays non-blocking under concurrency and matches FastAPI's async model.

## Consequences

- Every repository function is `async` and takes an `AsyncSession`.
- Async adds complexity vs. sync SQLAlchemy; accepted because FastAPI's dependency injection is async-first.
