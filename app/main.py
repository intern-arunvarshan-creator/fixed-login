from fastapi import FastAPI

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.users import router as users_router
from app.core.config import settings
from app.exceptions.handlers import register_exception_handlers

app = FastAPI(title=settings.app_name, version="0.1.0")

register_exception_handlers(app)

app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1/users")


def main() -> None:
    import uvicorn

    uvicorn.run("app.main:app", reload=True, app_dir=".", log_config=None, access_log=False)


if __name__ == "__main__":
    main()
