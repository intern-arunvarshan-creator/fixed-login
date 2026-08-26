from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import Settings, settings
from app.core.logging import configure_logging
from app.core.tracing import instrument_app
from app.database.database import get_db
from app.exceptions.exception_handlers import register_exception_handlers
from app.middleware.logging import AccessLogMiddleware
from app.middleware.request_context import RequestContextMiddleware

configure_logging()


def create_app(app_settings: Settings = settings) -> FastAPI:
    """Build and configure the FastAPI application."""
    # ``get_db`` runs for every route, so a request-scoped session is available to
    # the repository layer before any endpoint or dependency executes.
    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        dependencies=[Depends(get_db)],
    )

    register_exception_handlers(app)

    # Starlette runs the *last* added middleware first (outermost). Add the access
    # log first so RequestContextMiddleware runs before it and sets request_id.
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=app_settings.api_v1_prefix)

    instrument_app(app)
    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("app.main:app", reload=True, app_dir=".", log_config=None, access_log=False)


if __name__ == "__main__":
    main()
