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
def process_webhook(
    event: str,
    payload: dict[str, Any],
    ledger_id: str | None = None,
) -> str:
    """
    Process a GitHub webhook payload asynchronously.

    Args:
        event: GitHub event name (e.g., "push", "pull_request").
        payload: Webhook JSON payload.
        ledger_id: Optional ID of the ingestion ledger event (ADR-012).

    Returns:
        Status string for logging/monitoring.
    """
    from sqlalchemy import text

    async def _process() -> str:
        async with async_session_factory() as session:
            try:
                result = "ignored"
                if event == "push":
                    push_payload = GitHubPushPayload.model_validate(payload)
                    activities = await webhook_service.process_push_event(session, push_payload)
                    result = f"processed_push:{len(activities)}"

                elif event == "pull_request":
                    pr_payload = GitHubPRPayload.model_validate(payload)
                    activity = await webhook_service.process_pr_event(session, pr_payload)
                    result = "processed_pull_request" if activity else "skipped_pull_request"

                else:
                    result = f"ignored:{event}"

                # Update ledger on success
                if ledger_id:
                    await session.execute(
                        text(
                            "UPDATE ingest_event_ledger SET status = 'completed', processed_at = NOW() WHERE id = :id"
                        ),
                        {"id": ledger_id},
                    )

                await session.commit()
                return result

            except Exception as e:
                await session.rollback()
                logger.exception("Failed to process webhook", webhook_event=event)

                # Update ledger on failure (new session to ensure commit)
                if ledger_id:
                    try:
                        async with async_session_factory() as error_session:
                            await error_session.execute(
                                text(
                                    "UPDATE ingest_event_ledger SET status = 'failed', error_message = :msg WHERE id = :id"
                                ),
                                {"msg": str(e), "id": ledger_id},
                            )
                            await error_session.commit()
                    except Exception:
                        logger.exception("Failed to update ledger status")

                raise

    return asyncio.run(_process())
