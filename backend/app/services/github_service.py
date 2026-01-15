"""
GitHub Service.

Integration with GitHub API for fetching additional data.
"""

from typing import Any

import httpx

from app.core.config import settings


class GitHubService:
    """Service for interacting with GitHub API."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str | None = None):
        """
        Initialize GitHub service.

        Args:
            token: GitHub API token (uses settings if not provided).
        """
        self.token = token or settings.GITHUB_TOKEN
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DevBridge/0.1.0",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def get_commit_diff(self, owner: str, repo: str, sha: str) -> str | None:
        """
        Get the diff for a specific commit.

        Args:
            owner: Repository owner.
            repo: Repository name.
            sha: Commit SHA.

        Returns:
            Diff content as string, or None if failed.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/commits/{sha}"
        headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.text
            return None

    async def get_commit_files(self, owner: str, repo: str, sha: str) -> list[str]:
        """
        Get the list of files changed in a specific commit.

        Args:
            owner: Repository owner.
            repo: Repository name.
            sha: Commit SHA.

        Returns:
            List of filenames changed in the commit.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/commits/{sha}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                files = data.get("files", [])
                return [f.get("filename", "") for f in files if f.get("filename")]
            return []

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str | None:
        """
        Get the diff for a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            Diff content as string, or None if failed.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.text
            return None

    async def get_repository_info(self, owner: str, repo: str) -> dict[str, Any] | None:
        """
        Get repository information.

        Args:
            owner: Repository owner.
            repo: Repository name.

        Returns:
            Repository info dict, or None if failed.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                return dict(response.json())
            return None

    async def list_user_repositories(
        self, per_page: int = 100, max_pages: int = 5
    ) -> list[dict[str, Any]]:
        """
        List all repositories accessible to the user.

        Fetches multiple pages to get all repositories the user has access to,
        including owned repos, organization repos, and collaborator repos.

        Args:
           per_page: Number of items per page (max 100).
           max_pages: Maximum number of pages to fetch.

        Returns:
            List of repository dicts.
        """
        all_repos: list[dict[str, Any]] = []

        async with httpx.AsyncClient() as client:
            for page in range(1, max_pages + 1):
                url = f"{self.BASE_URL}/user/repos"
                params: dict[str, str | int] = {
                    "per_page": per_page,
                    "sort": "updated",
                    "type": "all",  # owner, collaborator, organization_member
                    "page": page,
                }

                response = await client.get(url, headers=self.headers, params=params, timeout=30)

                if response.status_code != 200:
                    break

                repos = response.json()
                if not repos:
                    break  # No more repos

                all_repos.extend(repos)

                # If we got fewer than per_page, we've reached the end
                if len(repos) < per_page:
                    break

        return all_repos

    async def fetch_issues(
        self, owner: str, repo: str, state: str = "all", per_page: int = 100
    ) -> list[dict[str, Any]]:
        """
        Fetch repository issues.

        Args:
            owner: Repository owner.
            repo: Repository name.
            state: Issue state filter (open, closed, all).
            per_page: Number of issues per page.

        Returns:
            List of issue dicts with number, title, body, state, etc.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues"
        params: dict[str, str | int] = {"state": state, "per_page": per_page, "filter": "all"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code == 200:
                issues = response.json()
                # Filter out pull requests (GitHub API returns PRs in issues endpoint)
                return [
                    {
                        "number": i.get("number"),
                        "title": i.get("title"),
                        "body": i.get("body"),
                        "state": i.get("state"),
                        "author": i.get("user", {}).get("login"),
                        "assignees": [a.get("login") for a in i.get("assignees", [])],
                        "labels": [label.get("name") for label in i.get("labels", [])],
                        "milestone": i.get("milestone", {}).get("title")
                        if i.get("milestone")
                        else None,
                        "created_at": i.get("created_at"),
                        "closed_at": i.get("closed_at"),
                        "closed_by": i.get("closed_by", {}).get("login")
                        if i.get("closed_by")
                        else None,
                    }
                    for i in issues
                    if not i.get("pull_request")  # Filter out PRs
                ]
            return []

    async def get_pr_details(self, owner: str, repo: str, pr_number: int) -> dict[str, Any] | None:
        """
        Get detailed PR information including file stats and merge info.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            Dict with PR details including additions, deletions, changed_files, merged_at.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return {
                    "additions": data.get("additions", 0),
                    "deletions": data.get("deletions", 0),
                    "changed_files": data.get("changed_files", 0),
                    "merged_at": data.get("merged_at"),
                    "merged": data.get("merged", False),
                    "state": data.get("state"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                }
            return None

    async def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        """
        Get all reviews for a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            List of review dicts with state, user, submitted_at.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                reviews = response.json()
                return [
                    {
                        "id": r.get("id"),
                        "user": r.get("user", {}).get("login"),
                        "state": r.get(
                            "state"
                        ),  # APPROVED, CHANGES_REQUESTED, COMMENTED, PENDING, DISMISSED
                        "body": r.get("body"),
                        "submitted_at": r.get("submitted_at"),
                    }
                    for r in reviews
                ]
            return []

    async def get_pr_review_comments(
        self, owner: str, repo: str, pr_number: int
    ) -> list[dict[str, Any]]:
        """
        Get inline review comments for a PR.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pr_number: Pull request number.

        Returns:
            List of review comment dicts.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/comments"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                comments = response.json()
                return [
                    {
                        "id": c.get("id"),
                        "user": c.get("user", {}).get("login"),
                        "body": c.get("body"),
                        "path": c.get("path"),
                        "created_at": c.get("created_at"),
                    }
                    for c in comments
                ]
            return []

    async def get_commit_stats(self, owner: str, repo: str, sha: str) -> dict[str, Any] | None:
        """
        Get commit statistics including additions and deletions.

        Args:
            owner: Repository owner.
            repo: Repository name.
            sha: Commit SHA.

        Returns:
            Dict with additions, deletions, and files_changed.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/commits/{sha}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                stats = data.get("stats", {})
                files = data.get("files", [])
                return {
                    "additions": stats.get("additions", 0),
                    "deletions": stats.get("deletions", 0),
                    "files_changed": len(files),
                }
            return None

    async def list_user_teams(self) -> list[dict[str, Any]]:
        """
        List all teams the authenticated user belongs to.

        Returns:
            List of team dicts.
        """
        url = f"{self.BASE_URL}/user/teams"
        all_teams: list[dict[str, Any]] = []

        async with httpx.AsyncClient() as client:
            page = 1
            while True:
                params = {"page": page, "per_page": 100}
                response = await client.get(url, headers=self.headers, params=params, timeout=30)

                if response.status_code != 200:
                    break

                teams = response.json()
                if not teams:
                    break

                all_teams.extend(teams)

                if len(teams) < 100:
                    break
                page += 1

        return all_teams

    async def list_team_repositories(self, org: str, team_slug: str) -> list[dict[str, Any]]:
        """
        List repositories belonging to a specific team.

        Args:
            org: Organization login (e.g. 'devbridge-ai').
            team_slug: Team slug (e.g. 'frontend').

        Returns:
            List of repository dicts.
        """
        url = f"{self.BASE_URL}/orgs/{org}/teams/{team_slug}/repos"
        all_repos: list[dict[str, Any]] = []

        async with httpx.AsyncClient() as client:
            page = 1
            while True:
                params = {"page": page, "per_page": 100}
                response = await client.get(url, headers=self.headers, params=params, timeout=30)

                if response.status_code != 200:
                    break

                repos = response.json()
                if not repos:
                    break

                all_repos.extend(repos)

                if len(repos) < 100:
                    break
                page += 1

        return all_repos


# Singleton instance
github_service = GitHubService()
