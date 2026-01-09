"""
Sync Service.

Service for synchronizing GitHub repository data to local database.
Fetches commits and PRs from GitHub API and creates Activities.
"""

import logging
import re
from contextlib import suppress
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas import ActivityCreate, ActivityType, BusinessUpdateCreate, ImpactLevel
from app.services import activity_service, repository_service
from app.services.ai_service import ai_service
from app.services.github_service import github_service

logger = logging.getLogger(__name__)


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
        """Fetch commits from GitHub API."""
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
        """Fetch pull requests from GitHub API."""
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
        fetch_diffs: bool = True,
        token: str | None = None,
        organization_id: str | None = None,
    ) -> dict[str, int]:
        """
        Sync a repository's commits and PRs to the database.

        Args:
            db: Database session.
            repo_name: Repository name in "owner/repo" format.
            max_commits: Maximum commits to sync.
            max_prs: Maximum PRs to sync.
            fetch_diffs: Whether to fetch full diff content for each commit/PR.
            token: Optional GitHub token to use for this sync operation.
            organization_id: Optional Organization UUID. Defaults to DEFAULT_ORG_ID.

        Returns:
            Dict with counts of synced items.
        """
        org_id = organization_id or repository_service.DEFAULT_ORG_ID

        # Update token if provided (TEMPORARY: This is not thread-safe for high concurrency but OK for MVP)
        if token:
            self.token = token
            self.headers["Authorization"] = f"Bearer {token}"

        # Get or create repository
        repo = await repository_service.get_repository_by_name(db, org_id, repo_name)
        if not repo:
            from app.schemas import RepositoryCreate

            owner, name = repo_name.split("/")
            repo_create = RepositoryCreate(
                url=f"https://github.com/{repo_name}",
                name=repo_name,
                owner=owner,
            )
            repo = await repository_service.create_repository(db, org_id, repo_create)

        owner, name = repo_name.split("/")
        commits_synced = 0
        prs_synced = 0

        # Sync commits
        commits = await self.fetch_commits(owner, name, per_page=max_commits)
        for commit in commits:
            sha = commit.get("sha", "")
            message = commit.get("commit", {}).get("message", "")
            author = commit.get("commit", {}).get("author", {}).get("name", "unknown")

            # Build content with diff if requested
            content = message
            if fetch_diffs and sha:
                # Add timeout protection
                try:
                    diff = await github_service.get_commit_diff(owner, name, sha)
                    if diff:
                        # Limit diff size to avoid huge content
                        diff_preview = diff[:5000] if len(diff) > 5000 else diff
                        if len(diff) > 5000:
                            diff_preview += "\n... (diff truncated)"
                        content = f"{message}\n\n---\n## Diff:\n```diff\n{diff_preview}\n```"
                except Exception as e:
                    print(f"Failed to fetch diff for {sha}: {e}")
                    # Continue without diff

            commit_date_str = commit.get("commit", {}).get("author", {}).get("date")
            occurred_at = None
            if commit_date_str:
                with suppress(ValueError):
                    occurred_at = datetime.fromisoformat(commit_date_str.replace("Z", "+00:00"))

            # Fetch files changed in this commit (Context Enrichment)
            files_touched: list[str] | None = None
            if sha:
                try:
                    files_touched = await github_service.get_commit_files(owner, name, sha)
                except Exception as e:
                    print(f"Failed to fetch files for {sha}: {e}")

            # Auto-tagging mechanism (Phase 2)
            # We construct a temporary dict to pass to the AI service
            temp_activity_dict = {
                "title": message.split("\n")[0][:100],
                "content": content,
                "labels": [],
                "files_touched": files_touched or [],
            }
            value_tags = await ai_service.classify_activity_tags(temp_activity_dict)

            activity_in = ActivityCreate(
                repository_id=repo.id,
                external_id=sha[:12],
                type=ActivityType.COMMIT,
                title=message.split("\n")[0][:100],
                content=content,
                author=author,
                occurred_at=occurred_at,
                files_touched=files_touched,
                value_tags=value_tags,
            )

            activity, created = await activity_service.get_or_create_activity(db, activity_in)
            if created:
                commits_synced += 1
                # Generate business update for new activity
                try:
                    update_data = await ai_service.generate_business_update(
                        {
                            "type": "COMMIT",
                            "title": activity_in.title,
                            "content": content,
                            "labels": [],
                            "files_touched": files_touched or [],
                        }
                    )
                    update_create = BusinessUpdateCreate(
                        activity_id=activity.id,
                        summary=update_data["summary"],
                        impact_level=ImpactLevel(update_data["impact_level"]),
                        category=update_data.get("category"),
                    )
                    await activity_service.create_business_update(db, update_create)
                except Exception as e:
                    logger.warning(f"Failed to generate business update for commit {sha[:7]}: {e}")

        # Sync PRs
        prs = await self.fetch_pull_requests(owner, name, per_page=max_prs)
        for pr in prs:
            pr_number = pr.get("number", 0)
            title = pr.get("title", "")
            body = pr.get("body", "") or ""
            user = pr.get("user", {}).get("login", "unknown")
            state = pr.get("state", "open")

            # Build content with diff if requested
            content = body
            if fetch_diffs and pr_number:
                try:
                    diff = await github_service.get_pr_diff(owner, name, pr_number)
                    if diff:
                        diff_preview = diff[:5000] if len(diff) > 5000 else diff
                        if len(diff) > 5000:
                            diff_preview += "\n... (diff truncated)"
                        content = f"{body}\n\n---\n## Diff:\n```diff\n{diff_preview}\n```"
                except Exception as e:
                    print(f"Failed to fetch diff for PR #{pr_number}: {e}")
                    # Continue without diff

            created_at_str = pr.get("created_at")
            occurred_at = None
            if created_at_str:
                with suppress(ValueError):
                    occurred_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))

            # Extract PR labels (Context Enrichment)
            pr_labels = pr.get("labels", [])
            labels: list[str] | None = (
                [label.get("name") for label in pr_labels if label.get("name")]
                if pr_labels
                else None
            )

            # Extract linked issues from PR body (Context Enrichment)
            # Matches: #123, closes #123, fixes #123, resolves #123
            linked_issues: list[str] | None = None
            if body:
                issue_pattern = r"(?:closes?|fixes?|resolves?)?[\s#]*#(\d+)"
                matches = re.findall(issue_pattern, body, re.IGNORECASE)
                linked_issues = list(set(matches)) if matches else None

            # Auto-tagging mechanism (Phase 2)
            temp_activity_dict = {
                "title": title,
                "content": content,
                "labels": labels or [],
                "files_touched": [],  # We don't fetch PR files yet (future improvement)
            }
            value_tags = await ai_service.classify_activity_tags(temp_activity_dict)

            activity_in = ActivityCreate(
                repository_id=repo.id,
                external_id=str(pr_number),
                type=ActivityType.PULL_REQUEST,
                title=f"[{state.upper()}] {title}"[:100],
                content=content,
                author=user,
                occurred_at=occurred_at,
                labels=labels,
                linked_issues=linked_issues,
                value_tags=value_tags,
            )

            activity, created = await activity_service.get_or_create_activity(db, activity_in)
            if created:
                prs_synced += 1
                # Generate business update for new activity
                try:
                    update_data = await ai_service.generate_business_update(
                        {
                            "type": "PULL_REQUEST",
                            "title": title,
                            "content": content,
                            "labels": labels or [],
                            "files_touched": [],
                        }
                    )
                    update_create = BusinessUpdateCreate(
                        activity_id=activity.id,
                        summary=update_data["summary"],
                        impact_level=ImpactLevel(update_data["impact_level"]),
                        category=update_data.get("category"),
                    )
                    await activity_service.create_business_update(db, update_create)
                except Exception as e:
                    logger.warning(f"Failed to generate business update for PR #{pr_number}: {e}")

        return {"commits_synced": commits_synced, "prs_synced": prs_synced}

    async def discover_user_repositories(
        self,
        db: AsyncSession,
        organization_id: str,
        token: str | None = None,
    ) -> int:
        """
        Discover and import all user repositories.

        Fetches repositories from GitHub and creates them in the database
        if they don't exist. Does NOT sync content (commits/PRs), just metadata.

        Args:
            db: Database session.
            organization_id: Organization UUID.
            token: Optional GitHub token. If provided, uses this instead of singleton.

        Returns:
            Number of new repositories imported.
        """
        from app.schemas import RepositoryCreate
        from app.services.github_service import GitHubService

        # Use provided token or fall back to singleton
        gh_service = GitHubService(token=token) if token else github_service

        repos = await gh_service.list_user_repositories()
        imported = 0

        for repo_data in repos:
            full_name = repo_data.get("full_name")
            if not full_name:
                continue

            # Check if exists
            existing = await repository_service.get_repository_by_name(
                db, organization_id, full_name
            )
            if existing:
                continue

            # Create
            owner = repo_data.get("owner", {}).get("login", "unknown")
            repo_create = RepositoryCreate(
                url=repo_data.get("html_url", f"https://github.com/{full_name}"),
                name=full_name,
                owner=owner,
            )

            await repository_service.create_repository(db, organization_id, repo_create)
            imported += 1

        return imported


# Singleton instance
sync_service = SyncService()
