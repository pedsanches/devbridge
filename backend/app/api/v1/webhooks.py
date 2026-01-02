"""
GitHub Webhook Endpoints.

Handles incoming webhooks from GitHub for real-time event processing.
"""

import hashlib
import hmac
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from app.api.deps import DbSession
from app.core.config import settings
from app.schemas.webhook import GitHubPRPayload, GitHubPushPayload
from app.services import webhook_service

router = APIRouter()


async def verify_github_signature(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
) -> bytes:
    """
    Verify GitHub webhook signature.

    Args:
        request: Incoming request.
        x_hub_signature_256: GitHub signature header.

    Returns:
        Request body bytes.

    Raises:
        HTTPException: If signature is invalid.
    """
    body = await request.body()

    if not settings.GITHUB_WEBHOOK_SECRET:
        # Skip verification in development if no secret configured
        return body

    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="Missing signature header")

    expected_signature = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(f"sha256={expected_signature}", x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    return body


@router.post("/github")
async def github_webhook(
    request: Request,
    db: DbSession,
    x_github_event: str = Header(...),
    x_hub_signature_256: str | None = Header(None),
) -> dict[str, Any]:
    """
    Handle GitHub webhook events.

    Args:
        request: Incoming webhook request.
        db: Database session.
        x_github_event: GitHub event type header.
        x_hub_signature_256: GitHub signature header.

    Returns:
        Processing status.
    """
    _ = await verify_github_signature(request, x_hub_signature_256)
    payload = await request.json()

    # Route based on event type
    match x_github_event:
        case "push":
            push_payload = GitHubPushPayload.model_validate(payload)
            activities = await webhook_service.process_push_event(db, push_payload)
            return {
                "status": "processed",
                "event": "push",
                "activities_created": len(activities),
                "repository": push_payload.repository.full_name,
                "branch": push_payload.branch,
            }

        case "pull_request":
            pr_payload = GitHubPRPayload.model_validate(payload)
            activity = await webhook_service.process_pr_event(db, pr_payload)
            return {
                "status": "processed" if activity else "skipped",
                "event": "pull_request",
                "action": pr_payload.action,
                "activity_created": activity is not None,
                "repository": pr_payload.repository.full_name,
            }

        case "ping":
            return {"status": "ok", "event": "ping", "zen": payload.get("zen", "")}

        case _:
            return {"status": "ignored", "event": x_github_event}
