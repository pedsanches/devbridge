"""
Webhook Service.

Business logic for processing GitHub webhook events.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Activity
from app.schemas import ActivityCreate, ActivityType
from app.schemas.webhook import GitHubPRPayload, GitHubPushPayload
from app.services import activity_service, repository_service


async def process_push_event(
    db: AsyncSession,
    payload: GitHubPushPayload,
) -> list[Activity]:
    """
    Process a GitHub push event and create activities for each commit.

    Args:
        db: Database session.
        payload: Parsed push webhook payload.

    Returns:
        List of created activities.
    """
    # Get or create repository
    repo = await repository_service.get_repository_by_name(
        db, repository_service.DEFAULT_ORG_ID, payload.repository.full_name
    )

    if not repo:
        # Auto-register repository from webhook
        from pydantic import HttpUrl

        from app.schemas import RepositoryCreate

        repo_create = RepositoryCreate(
            url=HttpUrl(payload.repository.html_url),
            name=payload.repository.full_name,
            owner=payload.repository.full_name.split("/")[0],
        )
        repo = await repository_service.create_repository(
            db, repository_service.DEFAULT_ORG_ID, repo_create
        )

    # Process each commit
    activities: list[Activity] = []

    for commit in payload.commits:
        # Extract author name
        author = (
            commit.author.login
            if hasattr(commit.author, "login")
            else commit.author.get("name", "unknown")
        )

        activity_in = ActivityCreate(
            repository_id=repo.id,
            external_id=commit.id,
            type=ActivityType.COMMIT,
            title=commit.message.split("\n")[0][:100],  # First line, max 100 chars
            content=commit.message,
            author=author,
        )

        activity, created = await activity_service.get_or_create_activity(db, activity_in)

        if created:
            activities.append(activity)

    return activities


async def process_pr_event(
    db: AsyncSession,
    payload: GitHubPRPayload,
) -> Activity | None:
    """
    Process a GitHub pull_request event and create an activity.

    Args:
        db: Database session.
        payload: Parsed PR webhook payload.

    Returns:
        Created activity or None if skipped.
    """
    # Only process relevant actions
    if payload.action not in ("opened", "closed", "reopened"):
        return None

    # Get or create repository
    repo = await repository_service.get_repository_by_name(
        db, repository_service.DEFAULT_ORG_ID, payload.repository.full_name
    )

    if not repo:
        # Auto-register repository from webhook
        from pydantic import HttpUrl

        from app.schemas import RepositoryCreate

        repo_create = RepositoryCreate(
            url=HttpUrl(payload.repository.html_url),
            name=payload.repository.full_name,
            owner=payload.repository.full_name.split("/")[0],
        )
        repo = await repository_service.create_repository(
            db, repository_service.DEFAULT_ORG_ID, repo_create
        )

    pr = payload.pull_request

    # Calculate State (ADR-012)
    state = "open"
    if pr.merged:
        state = "merged"
    elif pr.state == "closed":
        state = "closed"

    # Build content with PR details
    content = f"{pr.body or ''}\n\n---\nStats: +{pr.additions} -{pr.deletions} in {pr.changed_files} files"

    activity_in = ActivityCreate(
        repository_id=repo.id,
        external_id=str(pr.number),
        type=ActivityType.PULL_REQUEST,
        title=f"[{payload.action.upper()}] {pr.title}"[:100],
        content=content,
        author=pr.user.login,
        # State Machine
        github_node_id=pr.node_id,
        state=state,
        state_updated_at=pr.updated_at,
        last_event_at=pr.updated_at,
    )

    activity, created = await activity_service.get_or_create_activity(db, activity_in)

    return activity if created else None
