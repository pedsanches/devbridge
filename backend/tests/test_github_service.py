"""Tests for GitHubService.

Tests for the GitHub API integration service.
Uses mocked HTTP responses to avoid hitting the real API.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.github_service import GitHubService

from .factories import (
    mock_github_commit,
    mock_github_issue,
    mock_github_pull_request,
    mock_github_repository,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def github_service() -> GitHubService:
    """Create a GitHubService instance with a test token."""
    return GitHubService(token="test-token-12345")


# =============================================================================
# Initialization Tests
# =============================================================================


class TestGitHubServiceInit:
    """Tests for GitHubService initialization."""

    def test_init_with_token(self):
        """Should initialize with provided token."""
        service = GitHubService(token="my-token")
        assert service.token == "my-token"

    def test_init_without_token_uses_settings(self):
        """Should fall back to settings when no token provided."""
        with patch("app.services.github_service.settings") as mock_settings:
            mock_settings.GITHUB_TOKEN = "settings-token"
            service = GitHubService()
            assert service.token == "settings-token"

    def test_base_url_is_github_api(self):
        """Should use correct GitHub API base URL."""
        service = GitHubService(token="token")
        assert service.BASE_URL == "https://api.github.com"

    def test_headers_include_auth_when_token_provided(self):
        """Should include authorization header when token is provided."""
        service = GitHubService(token="my-token")
        assert "Authorization" in service.headers
        assert service.headers["Authorization"] == "Bearer my-token"


# =============================================================================
# get_commit_diff Tests
# =============================================================================


class TestGetCommitDiff:
    """Tests for get_commit_diff method."""

    @pytest.mark.asyncio
    async def test_get_commit_diff_success(self, github_service: GitHubService):
        """Should return diff content on success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "diff --git a/file.py b/file.py\n+new line"

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await github_service.get_commit_diff("owner", "repo", "abc123")

        assert result is not None
        assert "diff --git" in result

    @pytest.mark.asyncio
    async def test_get_commit_diff_not_found(self, github_service: GitHubService):
        """Should return None when commit not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await github_service.get_commit_diff("owner", "repo", "invalid")

        assert result is None


# =============================================================================
# get_commit_files Tests
# =============================================================================


class TestGetCommitFiles:
    """Tests for get_commit_files method."""

    @pytest.mark.asyncio
    async def test_get_commit_files_success(self, github_service: GitHubService):
        """Should return list of filenames."""
        commit_data = mock_github_commit()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = commit_data

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await github_service.get_commit_files("owner", "repo", "abc123")

        assert isinstance(result, list)
        assert "src/main.py" in result

    @pytest.mark.asyncio
    async def test_get_commit_files_empty(self, github_service: GitHubService):
        """Should return empty list when no files."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"files": []}

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await github_service.get_commit_files("owner", "repo", "abc123")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_commit_files_not_found(self, github_service: GitHubService):
        """Should return empty list on 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await github_service.get_commit_files("owner", "repo", "invalid")

        assert result == []


# =============================================================================
# list_user_repositories Tests
# =============================================================================


class TestListUserRepositories:
    """Tests for list_user_repositories method."""

    @pytest.mark.asyncio
    async def test_list_repositories_success(self, github_service: GitHubService):
        """Should return list of repositories."""
        repos = [
            mock_github_repository(name="repo1", full_name="owner/repo1"),
            mock_github_repository(name="repo2", full_name="owner/repo2"),
        ]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = repos

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            # First call returns repos, second call returns empty (end pagination)
            mock_client.get.side_effect = [
                mock_response,
                MagicMock(status_code=200, json=MagicMock(return_value=[])),
            ]
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await github_service.list_user_repositories()

        assert len(result) == 2
        assert result[0]["name"] == "repo1"

    @pytest.mark.asyncio
    async def test_list_repositories_handles_api_error(self, github_service: GitHubService):
        """Should return empty list on API error."""
        mock_response = MagicMock()
        mock_response.status_code = 401  # Unauthorized

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await github_service.list_user_repositories()

        assert result == []


# =============================================================================
# fetch_issues Tests
# =============================================================================


class TestFetchIssues:
    """Tests for fetch_issues method."""

    @pytest.mark.asyncio
    async def test_fetch_issues_success(self, github_service: GitHubService):
        """Should return list of issues."""
        issues = [
            mock_github_issue(number=1, title="Bug report"),
            mock_github_issue(number=2, title="Feature request"),
        ]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = issues

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await github_service.fetch_issues("owner", "repo")

        assert len(result) == 2
        assert result[0]["title"] == "Bug report"

    @pytest.mark.asyncio
    async def test_fetch_issues_filters_pull_requests(self, github_service: GitHubService):
        """Should not include PRs in issues list."""
        real_issue = mock_github_issue(number=1, title="Real issue")
        pr_as_issue = {**mock_github_issue(number=2), "pull_request": {"url": "..."}}
        issues = [real_issue, pr_as_issue]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = issues

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await github_service.fetch_issues("owner", "repo")

        # Only real issue should be included
        assert len(result) == 1
        assert result[0]["title"] == "Real issue"


# =============================================================================
# get_pr_details Tests
# =============================================================================


class TestGetPRDetails:
    """Tests for get_pr_details method."""

    @pytest.mark.asyncio
    async def test_get_pr_details_success(self, github_service: GitHubService):
        """Should return PR details with stats."""
        pr = mock_github_pull_request(number=42, title="Feature PR")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = pr

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await github_service.get_pr_details("owner", "repo", 42)

        assert result is not None
        assert result["additions"] == 50
        assert result["deletions"] == 20

    @pytest.mark.asyncio
    async def test_get_pr_details_not_found(self, github_service: GitHubService):
        """Should return None when PR not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await github_service.get_pr_details("owner", "repo", 999)

        assert result is None


# =============================================================================
# get_pr_reviews Tests
# =============================================================================


class TestGetPRReviews:
    """Tests for get_pr_reviews method."""

    @pytest.mark.asyncio
    async def test_get_pr_reviews_success(self, github_service: GitHubService):
        """Should return list of reviews."""
        reviews = [
            {
                "id": 1,
                "state": "APPROVED",
                "user": {"login": "reviewer1"},
                "body": "",
                "submitted_at": "2024-01-01",
            },
            {
                "id": 2,
                "state": "CHANGES_REQUESTED",
                "user": {"login": "reviewer2"},
                "body": "changes",
                "submitted_at": "2024-01-02",
            },
        ]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = reviews

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await github_service.get_pr_reviews("owner", "repo", 42)

        assert len(result) == 2
        assert result[0]["state"] == "APPROVED"


# =============================================================================
# get_commit_stats Tests
# =============================================================================


class TestGetCommitStats:
    """Tests for get_commit_stats method."""

    @pytest.mark.asyncio
    async def test_get_commit_stats_success(self, github_service: GitHubService):
        """Should return commit statistics."""
        commit = mock_github_commit()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = commit

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await github_service.get_commit_stats("owner", "repo", "abc123")

        assert result is not None
        assert result["additions"] == 10
        assert result["deletions"] == 5
        assert result["files_changed"] == 1

    @pytest.mark.asyncio
    async def test_get_commit_stats_not_found(self, github_service: GitHubService):
        """Should return None on 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await github_service.get_commit_stats("owner", "repo", "invalid")

        assert result is None
