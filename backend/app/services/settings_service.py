"""
Settings Service.

Business logic for organization settings and integrations.
"""

from uuid import uuid4

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_token, encrypt_token
from app.models import Activity, OrganizationSettings, Repository
from app.schemas.settings import (
    ConnectGitHubResponse,
    DataSourcesResponse,
    DataSourceSummary,
    GitHubIntegration,
    IntegrationsResponse,
    IntegrationStatus,
    SlackIntegration,
)


async def get_or_create_settings(
    db: AsyncSession,
    organization_id: str,
) -> OrganizationSettings:
    """
    Get or create organization settings.

    Args:
        db: Database session.
        organization_id: Organization UUID.

    Returns:
        OrganizationSettings instance.
    """
    result = await db.execute(
        select(OrganizationSettings).where(
            OrganizationSettings.organization_id == organization_id
        )
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = OrganizationSettings(
            id=str(uuid4()),
            organization_id=organization_id,
            is_github_connected=False,
        )
        db.add(settings)
        await db.flush()
        await db.refresh(settings)

    return settings


async def get_integrations_status(
    db: AsyncSession,
    organization_id: str,
) -> IntegrationsResponse:
    """
    Get status of all integrations for an organization.

    Args:
        db: Database session.
        organization_id: Organization UUID.

    Returns:
        IntegrationsResponse with GitHub and Slack status.
    """
    settings = await get_or_create_settings(db, organization_id)

    # Count repositories for this org
    repo_count_result = await db.execute(
        select(func.count(Repository.id)).where(
            Repository.organization_id == organization_id,
            Repository.is_active.is_(True),
        )
    )
    repos_count = repo_count_result.scalar() or 0

    github_status = IntegrationStatus.CONNECTED if settings.is_github_connected else IntegrationStatus.DISCONNECTED

    return IntegrationsResponse(
        github=GitHubIntegration(
            status=github_status,
            connected_at=settings.updated_at if settings.is_github_connected else None,
            repositories_count=repos_count,
            organization_name=None, 
        ),
        slack=SlackIntegration(
            status=IntegrationStatus.CONNECTED if settings.slack_webhook_url else IntegrationStatus.DISCONNECTED,
            connected_at=settings.updated_at if settings.slack_webhook_url else None,
        ),
    )


async def connect_github(
    db: AsyncSession,
    organization_id: str,
    token: str,
) -> ConnectGitHubResponse:
    """
    Connect GitHub integration with a PAT.

    Args:
        db: Database session.
        organization_id: Organization UUID.
        token: GitHub Personal Access Token.

    Returns:
        ConnectGitHubResponse with status.
    """
    # Validate token by calling GitHub API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=10,
            )

            if response.status_code != 200:
                return ConnectGitHubResponse(
                    status=IntegrationStatus.ERROR,
                    message="Invalid token or insufficient permissions",
                )

            user_data = response.json()
            login = user_data.get("login", "unknown")

    except Exception as e:
        return ConnectGitHubResponse(
            status=IntegrationStatus.ERROR,
            message=f"Failed to connect: {e!s}",
        )

    # Encrypt and store token
    settings = await get_or_create_settings(db, organization_id)
    settings.github_token_encrypted = encrypt_token(token)
    settings.is_github_connected = True

    await db.flush()
    await db.refresh(settings)

    # Trigger auto-discovery of repositories
    # We do this inline for MVP simplicity. In production, this should be a background task.
    try:
        from app.services.sync_service import sync_service
        # Re-initialize sync service with the fresh token
        sync_service.token = token
        sync_service.headers["Authorization"] = f"Bearer {token}"
        
        await sync_service.discover_user_repositories(db, organization_id)
    except Exception as e:
        # Don't fail the connection if sync fails, just log it
        print(f"Failed to auto-discover repositories: {e}")

    return ConnectGitHubResponse(
        status=IntegrationStatus.CONNECTED,
        organization_name=login,
        message=f"Successfully connected as {login}",
    )


async def disconnect_github(
    db: AsyncSession,
    organization_id: str,
) -> None:
    """
    Disconnect GitHub integration.

    Args:
        db: Database session.
        organization_id: Organization UUID.
    """
    settings = await get_or_create_settings(db, organization_id)
    settings.github_token_encrypted = None
    settings.is_github_connected = False
    await db.flush()


async def get_github_token(
    db: AsyncSession,
    organization_id: str,
) -> str | None:
    """
    Get decrypted GitHub token for an organization.

    Args:
        db: Database session.
        organization_id: Organization UUID.

    Returns:
        Decrypted token or None if not connected.
    """
    settings = await get_or_create_settings(db, organization_id)

    if not settings.github_token_encrypted:
        return None

    return decrypt_token(settings.github_token_encrypted)


async def get_data_sources(
    db: AsyncSession,
    organization_id: str,
) -> DataSourcesResponse:
    """
    Get all data sources (repositories) for an organization.

    Args:
        db: Database session.
        organization_id: Organization UUID.

    Returns:
        DataSourcesResponse with list of sources.
    """
    settings = await get_or_create_settings(db, organization_id)

    # Get repositories with activity counts
    result = await db.execute(
        select(Repository).where(
            Repository.organization_id == organization_id,
        ).order_by(Repository.created_at.desc())
    )
    repositories = list(result.scalars().all())

    sources = []
    for repo in repositories:
        # Count activities for this repo
        activity_count_result = await db.execute(
            select(func.count(Activity.id)).where(Activity.repository_id == repo.id)
        )
        activity_count = activity_count_result.scalar() or 0

        sources.append(
            DataSourceSummary(
                id=repo.id,
                name=repo.name,
                url=repo.url,
                is_active=repo.is_active,
                activities_count=activity_count,
                last_synced_at=repo.updated_at,
                indexing_status="indexed" if activity_count > 0 else "pending",
                vectors_count=activity_count,  # Simplified: 1 vector per activity
            )
        )

    return DataSourcesResponse(
        sources=sources,
        total=len(sources),
        github_connected=settings.is_github_connected,
    )
