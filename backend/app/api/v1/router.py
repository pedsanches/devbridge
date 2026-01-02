"""
API v1 Router.

Main router that aggregates all v1 endpoints.
"""

from fastapi import APIRouter

from app.api.v1.activities import router as activities_router
from app.api.v1.health import router as health_router
from app.api.v1.repos import router as repos_router
from app.api.v1.webhooks import router as webhooks_router

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(repos_router, prefix="/repos", tags=["Repositories"])
api_router.include_router(activities_router, prefix="/activities", tags=["Activities"])
api_router.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])
