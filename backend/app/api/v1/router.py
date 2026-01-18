"""
API v1 Router.

Main router that aggregates all v1 endpoints.
"""

from fastapi import APIRouter

from app.api.v1.activities import router as activities_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.health import router as health_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.report_templates import router as report_templates_router
from app.api.v1.reports import router as reports_router
from app.api.v1.repos import router as repos_router
from app.api.v1.settings import router as settings_router
from app.api.v1.sync import router as sync_router
from app.api.v1.teams import router as teams_router
from app.api.v1.webhooks import router as webhooks_router

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(settings_router, prefix="/settings", tags=["Settings"])
api_router.include_router(repos_router, prefix="/repos", tags=["Repositories"])
api_router.include_router(activities_router, prefix="/activities", tags=["Activities"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_router.include_router(conversations_router, prefix="/conversations", tags=["Conversations"])
api_router.include_router(feedback_router, prefix="/feedback", tags=["Feedback"])
api_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
api_router.include_router(
    report_templates_router, prefix="/report-templates", tags=["Report Templates"]
)
api_router.include_router(metrics_router, tags=["Metrics"])
api_router.include_router(sync_router, prefix="/sync", tags=["Sync"])
api_router.include_router(teams_router, tags=["Teams"])
api_router.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])
