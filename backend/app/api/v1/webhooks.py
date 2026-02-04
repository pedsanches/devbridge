"""
GitHub Webhook Endpoints.

Handles incoming webhooks from GitHub and queues them for processing.
"""

import hashlib
import hmac
import time
from typing import Any, cast

from fastapi import APIRouter, Header, HTTPException, Request

from app.api.deps import DbSession
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
    db: "DbSession",
    x_github_event: str = Header(...),
    x_github_delivery: str = Header(...),
    x_hub_signature_256: str | None = Header(None),
) -> dict[str, Any]:
    """
    Handle GitHub webhook events with idempotency (ADR-012).

    Args:
        request: Incoming webhook request.
        db: Database session.
        x_github_event: GitHub event type.
        x_github_delivery: GitHub delivery ID (UUID).
        x_hub_signature_256: GitHub signature header.

    Returns:
        Queue status.
    """
    from sqlalchemy import text

    from app.worker import process_webhook

    body_bytes = await verify_github_signature(request, x_hub_signature_256)
    payload = await request.json()

    repository_full_name = extract_repository_full_name(payload)
    if not repository_full_name:
        return {"status": "ignored", "reason": "no_repository"}

    await enforce_webhook_rate_limit(repository_full_name)

    # Calculate payload hash for debugging
    import hashlib

    payload_hash = hashlib.sha256(body_bytes).hexdigest()
    installation_id = payload.get("installation", {}).get("id")

    # === Idempotency Check (Level 1) ===
    # Atomic insert-or-update
    # We use raw SQL for efficiency and ON CONFLICT support
    stmt = text("""
        INSERT INTO ingest_event_ledger (
            delivery_id, source, event_type, repo_full_name,
            installation_id, payload_hash, status
        )
        VALUES (
            :delivery_id, 'github', :event_type, :repo_full_name,
            :installation_id, :payload_hash, 'received'
        )
        ON CONFLICT (delivery_id) DO UPDATE SET
            last_seen_at = NOW(),
            attempt_count = ingest_event_ledger.attempt_count + 1
        RETURNING id, attempt_count, status
    """)

    result = await db.execute(
        stmt,
        {
            "delivery_id": x_github_delivery,
            "event_type": x_github_event,
            "repo_full_name": repository_full_name,
            "installation_id": installation_id,
            "payload_hash": payload_hash,
        },
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=500, detail="Failed to ledger event")

    ledger_id, attempt_count, status = row

    # If it's a retry of a completed event, ignore
    if attempt_count > 1 and status == "completed":
        return {
            "status": "already_processed",
            "delivery_id": x_github_delivery,
            "attempt": attempt_count,
        }

    # If currently processing (and recent), maybe ignore?
    # For now, we allow requeueing via Celery if it crashed,
    # but the worker should handle the "processing" state update.

    # Route based on event type
    match x_github_event:
        case "push" | "pull_request":
            # Mark simple processing status before queuing
            await db.execute(
                text(
                    "UPDATE ingest_event_ledger SET status = 'processing', processing_started_at = NOW() WHERE id = :id"
                ),
                {"id": ledger_id},
            )
            await db.commit()

            task = cast(Any, process_webhook).delay(
                event=x_github_event,
                payload=payload,
                ledger_id=str(ledger_id),  # Pass ledger ID to worker
            )
            return {
                "status": "queued",
                "event": x_github_event,
                "task_id": task.id,
                "delivery_id": x_github_delivery,
                "ledger_id": str(ledger_id),
            }

        case "ping":
            return {"status": "ok", "event": "ping", "zen": payload.get("zen", "")}

        case _:
            return {"status": "ignored", "event": x_github_event}
