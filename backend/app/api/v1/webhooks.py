"""
GitHub Webhook Endpoints.

Handles incoming webhooks from GitHub and queues them for processing.
"""

import hashlib
import hmac
import time
from typing import Any, cast

from fastapi import APIRouter, Header, HTTPException, Request

from app.core.config import settings
from app.core.rate_limit import build_rate_limit_headers, rate_limiter

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
    body = cast(bytes, await request.body())

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


async def enforce_webhook_rate_limit(repository_full_name: str) -> None:
    """
    Enforce per-repository webhook rate limiting.

    Args:
        repository_full_name: GitHub repository full name.
    """
    limit = settings.WEBHOOK_RATE_LIMIT_PER_HOUR
    if limit <= 0:
        return

    key = f"rate_limit:webhook:{repository_full_name}"
    result = await rate_limiter.check(key, limit, 3600)
    if not result.allowed:
        headers = build_rate_limit_headers(result)
        retry_after = max(result.reset_at - int(time.time()), 0)
        headers["Retry-After"] = str(retry_after)
        raise HTTPException(
            status_code=429,
            detail="Webhook rate limit exceeded",
            headers=headers,
        )


def extract_repository_full_name(payload: dict[str, Any]) -> str | None:
    """Extract repository full name from webhook payload."""
    repository = payload.get("repository")
    if isinstance(repository, dict):
        full_name = repository.get("full_name")
        if isinstance(full_name, str):
            return full_name
    return None


@router.post("/github")  # type: ignore[untyped-decorator]
async def github_webhook(
    request: Request,
    x_github_event: str = Header(...),
    x_hub_signature_256: str | None = Header(None),
) -> dict[str, Any]:
    """
    Handle GitHub webhook events.

    Args:
        request: Incoming webhook request.
        x_github_event: GitHub event type header.
        x_hub_signature_256: GitHub signature header.

    Returns:
        Queue status.
    """
    _ = await verify_github_signature(request, x_hub_signature_256)
    payload = await request.json()

    repository_full_name = extract_repository_full_name(payload)
    if repository_full_name:
        await enforce_webhook_rate_limit(repository_full_name)

    # Route based on event type
    match x_github_event:
        case "push" | "pull_request":
            from app.worker import process_webhook

            task = cast(Any, process_webhook).delay(x_github_event, payload)
            return {
                "status": "queued",
                "event": x_github_event,
                "task_id": task.id,
                "repository": repository_full_name,
            }

        case "ping":
            return {"status": "ok", "event": "ping", "zen": payload.get("zen", "")}

        case _:
            return {"status": "ignored", "event": x_github_event}
