"""Aggregate router that mounts every v1 route (prefix set at include time)."""

from fastapi import APIRouter

from app.api.v1 import audit_logs, auth, health, roles, screens, users, query_category,zones

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router, prefix="/users")
api_router.include_router(roles.router, prefix="/roles")
api_router.include_router(query_category.router, prefix="/query-category")
api_router.include_router(zones.router, prefix="/zones") 
api_router.include_router(screens.router, prefix="/screens")
api_router.include_router(audit_logs.router)
