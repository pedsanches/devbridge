"""
Celery worker configuration and tasks.

Provides a minimal worker entrypoint for background processing.
"""

from __future__ import annotations

import asyncio
from typing import Any

from celery import Celery

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import async_session_factory
from app.schemas.webhook import GitHubPRPayload, GitHubPushPayload
from app.services import webhook_service

logger = get_logger(__name__)


def create_celery_app() -> Celery:
    """Create the Celery application using project settings."""
    celery_app = Celery(
        "devbridge",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )
    return celery_app


celery_app = create_celery_app()

# Alias expected by `celery -A app.worker`
app = celery_app


@celery_app.task(name="devbridge.process_webhook")  # type: ignore[untyped-decorator]
def process_webhook(event: str, payload: dict[str, Any]) -> str:
    """
    Process a GitHub webhook payload asynchronously.

    Args:
        event: GitHub event name (e.g., "push", "pull_request").
        payload: Webhook JSON payload.

    Returns:
        Status string for logging/monitoring.
    """

    async def _process() -> str:
        async with async_session_factory() as session:
            try:
                if event == "push":
                    push_payload = GitHubPushPayload.model_validate(payload)
                    activities = await webhook_service.process_push_event(session, push_payload)
                    await session.commit()
                    return f"processed_push:{len(activities)}"

                if event == "pull_request":
                    pr_payload = GitHubPRPayload.model_validate(payload)
                    activity = await webhook_service.process_pr_event(session, pr_payload)
                    await session.commit()
                    return "processed_pull_request" if activity else "skipped_pull_request"

                return f"ignored:{event}"
            except Exception:
                await session.rollback()
                logger.exception("Failed to process webhook", webhook_event=event)
                raise

    return asyncio.run(_process())
