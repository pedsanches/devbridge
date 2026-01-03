"""
Sync Service.

Service for synchronizing GitHub repository data to local database.
Fetches commits and PRs from GitHub API and creates Activities.
"""

from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas import ActivityCreate, ActivityType
from app.services import activity_service, repository_service


class SyncService:
    """Service for syncing GitHub data to local database."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str | None = None):
        """Initialize sync service with GitHub token."""
        self.token = token or settings.GITHUB_TOKEN
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DevBridge/0.1.0",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def fetch_commits(
        self,
        owner: str,
        repo: str,
        since: datetime | None = None,
        per_page: int = 30,
    ) -> list[dict[str, Any]]:
        """
        Fetch commits from GitHub API.

        Args:
            owner: Repository owner.
            repo: Repository name.
            since: Only commits after this date.
            per_page: Number of commits to fetch.

        Returns:
            List of commit data dictionaries.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/commits"
        params: dict[str, Any] = {"per_page": per_page}
        if since:
            params["since"] = since.isoformat()

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            return []

    async def fetch_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "all",
        per_page: int = 30,
    ) -> list[dict[str, Any]]:
        """
        Fetch pull requests from GitHub API.

        Args:
            owner: Repository owner.
            repo: Repository name.
            state: Filter by state (open, closed, all).
            per_page: Number of PRs to fetch.

        Returns:
            List of PR data dictionaries.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls"
        params = {"state": state, "per_page": per_page}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            return []

    async def sync_repository(
        self,
        db: AsyncSession,
        repo_name: str,
        max_commits: int = 50,
        max_prs: int = 20,
    ) -> dict[str, int]:
        """
        Sync a repository's commits and PRs to the database.

        Args:
            db: Database session.
            repo_name: Repository name in "owner/repo" format.
            max_commits: Maximum commits to sync.
            max_prs: Maximum PRs to sync.

        Returns:
            Dict with counts of synced items.
        """
        # Get or create repository
        repo = await repository_service.get_repository_by_name(db, repo_name)
        if not repo:
            from pydantic import HttpUrl

            from app.schemas import RepositoryCreate

            owner, name = repo_name.split("/")
            repo_create = RepositoryCreate(
                url=HttpUrl(f"https://github.com/{repo_name}"),
                name=repo_name,
                owner=owner,
            )
            repo = await repository_service.create_repository(db, repo_create)

        owner, name = repo_name.split("/")
        commits_synced = 0
        prs_synced = 0

        # Sync commits
        commits = await self.fetch_commits(owner, name, per_page=max_commits)
        for commit in commits:
            sha = commit.get("sha", "")
            message = commit.get("commit", {}).get("message", "")
            author = commit.get("commit", {}).get("author", {}).get("name", "unknown")

            activity_in = ActivityCreate(
                repository_id=repo.id,
                external_id=sha[:12],
                type=ActivityType.COMMIT,
                title=message.split("\n")[0][:100],
                content=message,
                author=author,
            )

            _, created = await activity_service.get_or_create_activity(db, activity_in)
            if created:
                commits_synced += 1

        # Sync PRs
        prs = await self.fetch_pull_requests(owner, name, per_page=max_prs)
        for pr in prs:
            pr_number = pr.get("number", 0)
            title = pr.get("title", "")
            body = pr.get("body", "") or ""
            user = pr.get("user", {}).get("login", "unknown")
            state = pr.get("state", "open")

            activity_in = ActivityCreate(
                repository_id=repo.id,
                external_id=str(pr_number),
                type=ActivityType.PULL_REQUEST,
                title=f"[{state.upper()}] {title}"[:100],
                content=body,
                author=user,
            )

            _, created = await activity_service.get_or_create_activity(db, activity_in)
            if created:
                prs_synced += 1

        return {"commits_synced": commits_synced, "prs_synced": prs_synced}


# Singleton instance
sync_service = SyncService()
