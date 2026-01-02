"""
GitHub Webhook Endpoints.

Handles incoming webhooks from GitHub for real-time event processing.
"""

import hashlib
import hmac
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from app.core.config import settings

router = APIRouter()


async def verify_github_signature(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
) -> None:
    """
    Verify GitHub webhook signature.

    Args:
        request: Incoming request.
        x_hub_signature_256: GitHub signature header.

    Raises:
        HTTPException: If signature is invalid.
    """
    if not settings.GITHUB_WEBHOOK_SECRET:
        # Skip verification in development if no secret configured
        return

    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="Missing signature header")

    body = await request.body()
    expected_signature = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(f"sha256={expected_signature}", x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(...),
) -> dict[str, Any]:
    """
    Handle GitHub webhook events.

    Args:
        request: Incoming webhook request.
        x_github_event: GitHub event type header.

    Returns:
        Processing status.
    """
    await verify_github_signature(request)

    payload = await request.json()

    # Route based on event type
    match x_github_event:
        case "push":
            # TODO: Queue push event for processing
            return {"status": "accepted", "event": "push", "queued": True}

        case "pull_request":
            # TODO: Queue PR event for processing
            return {"status": "accepted", "event": "pull_request", "queued": True}

        case "ping":
            return {"status": "ok", "event": "ping", "zen": payload.get("zen", "")}

        case _:
            return {"status": "ignored", "event": x_github_event}
