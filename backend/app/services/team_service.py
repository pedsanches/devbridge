"""
Team Service.

Business logic for team management and data sources organization.
Implements patterns inspired by Waydev/Swarmia.
"""

import contextlib
import re
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Activity, Repository, Team
from app.models.team import team_repositories
from app.schemas.team import (
    RepositorySummary,
    TeamCreate,
    TeamDetailResponse,
    TeamListResponse,
    TeamResponse,
    TeamUpdate,
)


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:100]


class TeamService:
    """Service for managing teams and repository groupings."""

    async def create_team(
        self,
        db: AsyncSession,
        org_id: str,
        data: TeamCreate,
    ) -> TeamResponse:
        """
        Create a new team.

        Args:
            db: Database session.
            org_id: Organization ID.
            data: Team creation data.

        Returns:
            Created team response.
        """
        team = Team(
            id=str(uuid4()),
            organization_id=org_id,
            name=data.name,
            slug=slugify(data.name),
            description=data.description,
            color=data.color,
            github_team_slug=data.github_team_slug,
            is_default=False,
        )
        db.add(team)
        await db.flush()

        # Add repositories if provided
        if data.repository_ids:
            await self._add_repositories_to_team(db, team.id, org_id, data.repository_ids)

        await db.refresh(team)

        # Count repositories
        repos_count = await self._count_team_repositories(db, team.id)

        return TeamResponse(
            id=team.id,
            name=team.name,
            slug=team.slug,
            description=team.description,
            color=team.color,
            is_default=team.is_default,
            github_team_slug=team.github_team_slug,
            repositories_count=repos_count,
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

    async def get_team(
        self,
        db: AsyncSession,
        team_id: str,
        org_id: str,
    ) -> TeamDetailResponse | None:
        """
        Get a team by ID with full details.

        Args:
            db: Database session.
            team_id: Team ID.
            org_id: Organization ID for access control.

        Returns:
            Team details or None if not found.
        """
        result = await db.execute(
            select(Team)
            .where(Team.id == team_id, Team.organization_id == org_id)
            .options(selectinload(Team.grouped_repositories))
        )
        team = result.scalar_one_or_none()

        if not team:
            return None

        # Get repositories with activity counts
        repos_with_counts = await self._get_repositories_with_counts(db, team.id)

        return TeamDetailResponse(
            id=team.id,
            name=team.name,
            slug=team.slug,
            description=team.description,
            color=team.color,
            is_default=team.is_default,
            github_team_slug=team.github_team_slug,
            repositories_count=len(repos_with_counts),
            created_at=team.created_at,
            updated_at=team.updated_at,
            repositories=repos_with_counts,
        )

    async def list_teams(
        self,
        db: AsyncSession,
        org_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> TeamListResponse:
        """
        List teams for an organization.

        Args:
            db: Database session.
            org_id: Organization ID.
            page: Page number (1-indexed).
            page_size: Items per page.

        Returns:
            Paginated team list.
        """
        # Count total
        count_result = await db.execute(
            select(func.count(Team.id)).where(Team.organization_id == org_id)
        )
        total = count_result.scalar() or 0

        # Get teams
        offset = (page - 1) * page_size
        result = await db.execute(
            select(Team)
            .where(Team.organization_id == org_id)
            .order_by(Team.is_default.desc(), Team.name)
            .offset(offset)
            .limit(page_size)
        )
        teams = list(result.scalars().all())

        # Get repository counts for each team
        items = []
        for team in teams:
            repos_count = await self._count_team_repositories(db, team.id)
            items.append(
                TeamResponse(
                    id=team.id,
                    name=team.name,
                    slug=team.slug,
                    description=team.description,
                    color=team.color,
                    is_default=team.is_default,
                    github_team_slug=team.github_team_slug,
                    repositories_count=repos_count,
                    created_at=team.created_at,
                    updated_at=team.updated_at,
                )
            )

        return TeamListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(offset + len(items)) < total,
        )

    async def update_team(
        self,
        db: AsyncSession,
        team_id: str,
        org_id: str,
        data: TeamUpdate,
    ) -> TeamResponse | None:
        """
        Update a team.

        Args:
            db: Database session.
            team_id: Team ID.
            org_id: Organization ID for access control.
            data: Update data.

        Returns:
            Updated team or None if not found.
        """
        result = await db.execute(
            select(Team).where(Team.id == team_id, Team.organization_id == org_id)
        )
        team = result.scalar_one_or_none()

        if not team:
            return None

        # Update fields
        if data.name is not None:
            team.name = data.name
            team.slug = slugify(data.name)
        if data.description is not None:
            team.description = data.description
        if data.color is not None:
            team.color = data.color
        if data.github_team_slug is not None:
            team.github_team_slug = data.github_team_slug
        if data.is_default is not None:
            # If setting as default, unset other defaults
            if data.is_default:
                await db.execute(
                    Team.__table__.update()
                    .where(Team.organization_id == org_id, Team.id != team_id)
                    .values(is_default=False)
                )
            team.is_default = data.is_default

        await db.flush()
        await db.refresh(team)

        repos_count = await self._count_team_repositories(db, team.id)

        return TeamResponse(
            id=team.id,
            name=team.name,
            slug=team.slug,
            description=team.description,
            color=team.color,
            is_default=team.is_default,
            github_team_slug=team.github_team_slug,
            repositories_count=repos_count,
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

    async def delete_team(
        self,
        db: AsyncSession,
        team_id: str,
        org_id: str,
    ) -> bool:
        """
        Delete a team.

        Args:
            db: Database session.
            team_id: Team ID.
            org_id: Organization ID for access control.

        Returns:
            True if deleted, False if not found.
        """
        result = await db.execute(
            select(Team).where(Team.id == team_id, Team.organization_id == org_id)
        )
        team = result.scalar_one_or_none()

        if not team:
            return False

        await db.delete(team)
        return True

    async def add_repositories(
        self,
        db: AsyncSession,
        team_id: str,
        org_id: str,
        repository_ids: list[str],
    ) -> int:
        """
        Add repositories to a team.

        Args:
            db: Database session.
            team_id: Team ID.
            org_id: Organization ID for access control.
            repository_ids: List of repository IDs to add.

        Returns:
            Number of repositories added.
        """
        # Verify team exists
        result = await db.execute(
            select(Team).where(Team.id == team_id, Team.organization_id == org_id)
        )
        team = result.scalar_one_or_none()
        if not team:
            return 0

        return await self._add_repositories_to_team(db, team_id, org_id, repository_ids)

    async def remove_repositories(
        self,
        db: AsyncSession,
        team_id: str,
        org_id: str,
        repository_ids: list[str],
    ) -> int:
        """
        Remove repositories from a team.

        Args:
            db: Database session.
            team_id: Team ID.
            org_id: Organization ID for access control.
            repository_ids: List of repository IDs to remove.

        Returns:
            Number of repositories removed.
        """
        # Verify team exists
        result = await db.execute(
            select(Team).where(Team.id == team_id, Team.organization_id == org_id)
        )
        team = result.scalar_one_or_none()
        if not team:
            return 0

        # Delete associations
        delete_stmt = team_repositories.delete().where(
            team_repositories.c.team_id == team_id,
            team_repositories.c.repository_id.in_(repository_ids),
        )
        result = await db.execute(delete_stmt)
        return result.rowcount

    async def get_default_team(
        self,
        db: AsyncSession,
        org_id: str,
    ) -> TeamResponse | None:
        """
        Get the default team for an organization.

        Args:
            db: Database session.
            org_id: Organization ID.

        Returns:
            Default team or None.
        """
        result = await db.execute(
            select(Team).where(Team.organization_id == org_id, Team.is_default.is_(True))
        )
        team = result.scalar_one_or_none()

        if not team:
            return None

        repos_count = await self._count_team_repositories(db, team.id)

        return TeamResponse(
            id=team.id,
            name=team.name,
            slug=team.slug,
            description=team.description,
            color=team.color,
            is_default=team.is_default,
            github_team_slug=team.github_team_slug,
            repositories_count=repos_count,
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

    async def create_default_team_if_needed(
        self,
        db: AsyncSession,
        org_id: str,
    ) -> TeamResponse:
        """
        Create a default team if none exists.
        This is called during onboarding.

        Args:
            db: Database session.
            org_id: Organization ID.

        Returns:
            The default team.
        """
        existing = await self.get_default_team(db, org_id)
        if existing:
            return existing

        # Create default team with all active repositories
        team = Team(
            id=str(uuid4()),
            organization_id=org_id,
            name="Meus Repositórios",
            slug="meus-repositorios",
            description="Time padrão com todos os repositórios ativos",
            color="#6366F1",  # Indigo
            is_default=True,
        )
        db.add(team)
        await db.flush()

        # Add all active repositories
        repos_result = await db.execute(
            select(Repository.id).where(
                Repository.organization_id == org_id,
                Repository.is_active.is_(True),
            )
        )
        repo_ids = [str(r[0]) for r in repos_result.all()]

        if repo_ids:
            await self._add_repositories_to_team(db, team.id, org_id, repo_ids)

        await db.refresh(team)

        return TeamResponse(
            id=team.id,
            name=team.name,
            slug=team.slug,
            description=team.description,
            color=team.color,
            is_default=team.is_default,
            github_team_slug=team.github_team_slug,
            repositories_count=len(repo_ids),
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

    # Helper methods

    async def _add_repositories_to_team(
        self,
        db: AsyncSession,
        team_id: str,
        org_id: str,
        repository_ids: list[str],
    ) -> int:
        """Add repositories to a team (many-to-many)."""
        # Verify repositories belong to the same org
        result = await db.execute(
            select(Repository.id).where(
                Repository.id.in_(repository_ids),
                Repository.organization_id == org_id,
            )
        )
        valid_repo_ids = [str(r[0]) for r in result.all()]

        if not valid_repo_ids:
            return 0

        # Insert associations (ignore duplicates)
        # Insert associations (ignore duplicates)
        for repo_id in valid_repo_ids:
            with contextlib.suppress(Exception):
                await db.execute(
                    team_repositories.insert().values(
                        team_id=team_id,
                        repository_id=repo_id,
                    )
                )

        return len(valid_repo_ids)

    async def _count_team_repositories(self, db: AsyncSession, team_id: str) -> int:
        """Count repositories in a team."""
        result = await db.execute(
            select(func.count(team_repositories.c.repository_id)).where(
                team_repositories.c.team_id == team_id
            )
        )
        return result.scalar() or 0

    async def _get_repositories_with_counts(
        self, db: AsyncSession, team_id: str
    ) -> list[RepositorySummary]:
        """Get repositories in a team with activity counts."""
        result = await db.execute(
            select(Repository)
            .join(team_repositories, Repository.id == team_repositories.c.repository_id)
            .where(team_repositories.c.team_id == team_id)
            .order_by(Repository.name)
        )
        repositories = list(result.scalars().all())

        summaries = []
        for repo in repositories:
            # Count activities
            count_result = await db.execute(
                select(func.count(Activity.id)).where(Activity.repository_id == repo.id)
            )
            activities_count = count_result.scalar() or 0

            summaries.append(
                RepositorySummary(
                    id=repo.id,
                    name=repo.name,
                    url=repo.url,
                    is_active=repo.is_active,
                    activities_count=activities_count,
                )
            )

        return summaries


# Singleton instance
team_service = TeamService()
