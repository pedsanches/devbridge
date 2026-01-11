"""
Team Sync Service.

Synchronizes GitHub Teams with DevBridge Teams.
"""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Repository, Team
from app.models.team import team_repositories
from app.services.github_service import GitHubService
from app.services.team_service import slugify


class TeamSyncService:
    """Service for synchronizing GitHub Teams with DevBridge."""

    async def sync_github_teams(
        self,
        db: AsyncSession,
        org_id: str,
        github_token: str,
    ) -> dict:
        """
        Sync GitHub Teams to DevBridge Teams.

        Logic:
        1. Get all GitHub orgs we have repositories from.
        2. Fetch user's GitHub teams.
        3. Filter teams belonging to relevant orgs.
        4. Create/update DevBridge teams with github_team_slug.
        5. Associate repositories.

        Args:
            db: Database session.
            org_id: DevBridge organization ID.
            github_token: User's GitHub token for API access.

        Returns:
            Dict with sync statistics.
        """
        gh_service = GitHubService(token=github_token)

        # Step 1: Get unique GitHub org names from our repositories
        result = await db.execute(
            select(Repository.owner).where(Repository.organization_id == org_id).distinct()
        )
        local_gh_orgs = {row[0] for row in result.all()}

        if not local_gh_orgs:
            return {
                "synced_teams": 0,
                "created_teams": 0,
                "updated_teams": 0,
                "total_repos_linked": 0,
                "message": "Nenhum repositório encontrado para sincronização",
            }

        # Step 2: Fetch user's GitHub teams
        gh_teams = await gh_service.list_user_teams()

        # Step 3: Filter teams belonging to orgs we care about
        relevant_teams = [
            t for t in gh_teams if t.get("organization", {}).get("login") in local_gh_orgs
        ]

        if not relevant_teams:
            return {
                "synced_teams": 0,
                "created_teams": 0,
                "updated_teams": 0,
                "total_repos_linked": 0,
                "message": f"Nenhum time encontrado nas organizações: {', '.join(local_gh_orgs)}",
            }

        created_count = 0
        updated_count = 0
        total_repos_linked = 0

        for gh_team in relevant_teams:
            gh_org_login = gh_team.get("organization", {}).get("login")
            gh_team_slug = gh_team.get("slug")
            gh_team_name = gh_team.get("name")
            gh_team_description = gh_team.get("description")

            if not gh_team_slug or not gh_org_login or not gh_team_name:
                continue

            # Check if team already exists (by github_team_slug)
            existing = await db.execute(
                select(Team).where(
                    Team.organization_id == org_id,
                    Team.github_team_slug == gh_team_slug,
                )
            )
            team = existing.scalar_one_or_none()

            if team:
                # Update existing team
                team.name = gh_team_name
                team.description = gh_team_description or team.description
                updated_count += 1
            else:
                # Create new team
                team = Team(
                    id=str(uuid4()),
                    organization_id=org_id,
                    name=gh_team_name,
                    slug=slugify(gh_team_name),
                    description=gh_team_description,
                    color=self._generate_color_from_name(gh_team_name),
                    github_team_slug=gh_team_slug,
                    is_default=False,
                )
                db.add(team)
                await db.flush()
                created_count += 1

            # Step 4: Fetch team's repositories from GitHub
            gh_repos = await gh_service.list_team_repositories(gh_org_login, gh_team_slug)

            # Step 5: Link local repositories
            repos_linked = await self._link_repositories(db, team.id, org_id, gh_repos)
            total_repos_linked += repos_linked

        await db.flush()

        return {
            "synced_teams": len(relevant_teams),
            "created_teams": created_count,
            "updated_teams": updated_count,
            "total_repos_linked": total_repos_linked,
            "message": f"Sincronização concluída: {created_count} times criados, {updated_count} atualizados",
        }

    async def _link_repositories(
        self,
        db: AsyncSession,
        team_id: str,
        org_id: str,
        gh_repos: list[dict],
    ) -> int:
        """Link GitHub team repositories to DevBridge team."""
        if not gh_repos:
            return 0

        # Extract full_name from GitHub repos (owner/repo format)
        gh_repo_names = {r.get("full_name") for r in gh_repos if r.get("full_name")}

        if not gh_repo_names:
            return 0

        # Find matching local repositories
        result = await db.execute(
            select(Repository.id).where(
                Repository.organization_id == org_id,
                Repository.name.in_(gh_repo_names),
            )
        )
        local_repo_ids = [str(row[0]) for row in result.all()]

        if not local_repo_ids:
            return 0

        # Get existing associations to avoid duplicates
        existing = await db.execute(
            select(team_repositories.c.repository_id).where(team_repositories.c.team_id == team_id)
        )
        existing_repo_ids = {str(row[0]) for row in existing.all()}

        # Insert new associations
        linked = 0
        for repo_id in local_repo_ids:
            if repo_id not in existing_repo_ids:
                await db.execute(
                    team_repositories.insert().values(
                        team_id=team_id,
                        repository_id=repo_id,
                    )
                )
                linked += 1

        return linked

    def _generate_color_from_name(self, name: str) -> str:
        """Generate a consistent color based on team name."""
        colors = [
            "#6366F1",  # Indigo
            "#8B5CF6",  # Violet
            "#EC4899",  # Pink
            "#EF4444",  # Red
            "#F97316",  # Orange
            "#EAB308",  # Yellow
            "#22C55E",  # Green
            "#14B8A6",  # Teal
            "#06B6D4",  # Cyan
            "#3B82F6",  # Blue
        ]
        # Simple hash based on name
        hash_val = sum(ord(c) for c in name)
        return colors[hash_val % len(colors)]


# Singleton instance
team_sync_service = TeamSyncService()
