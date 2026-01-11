"""Test Factories.

Factory functions for creating test data.
Makes tests more readable and maintainable.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from app.models.activity import Activity, ActivityType, BusinessUpdate, ImpactLevel
from app.models.organization import Organization, PlanType
from app.models.organization_settings import OrganizationSettings
from app.models.repo import Repository
from app.models.user import User


def generate_uuid() -> str:
    """Generate a random UUID string."""
    return str(uuid.uuid4())


# =============================================================================
# Organization Factories
# =============================================================================


def build_organization(
    *,
    id: str | None = None,
    name: str = "Test Organization",
    slug: str = "test-org",
    plan: PlanType = PlanType.FREE,
    **kwargs: Any,
) -> Organization:
    """Build an Organization instance without saving to DB."""
    return Organization(
        id=id or generate_uuid(),
        name=name,
        slug=slug,
        plan=plan,
        **kwargs,
    )


def build_organization_settings(
    *,
    organization_id: str,
    github_token: str | None = None,
    slack_webhook_url: str | None = None,
    **kwargs: Any,
) -> OrganizationSettings:
    """Build OrganizationSettings instance."""
    return OrganizationSettings(
        id=generate_uuid(),
        organization_id=organization_id,
        github_token=github_token,
        slack_webhook_url=slack_webhook_url,
        **kwargs,
    )


# =============================================================================
# User Factories
# =============================================================================


def build_user(
    *,
    id: str | None = None,
    email: str = "test@example.com",
    name: str = "Test User",
    **kwargs: Any,
) -> User:
    """Build a User instance without saving to DB."""
    return User(
        id=id or generate_uuid(),
        email=email,
        name=name,
        **kwargs,
    )


# =============================================================================
# Repository Factories
# =============================================================================


def build_repository(
    *,
    id: str | None = None,
    organization_id: str,
    name: str = "owner/test-repo",
    owner: str = "owner",
    url: str = "https://github.com/owner/test-repo",
    is_active: bool = True,
    **kwargs: Any,
) -> Repository:
    """Build a Repository instance without saving to DB."""
    return Repository(
        id=id or generate_uuid(),
        organization_id=organization_id,
        name=name,
        owner=owner,
        url=url,
        is_active=is_active,
        **kwargs,
    )


# =============================================================================
# Activity Factories
# =============================================================================


def build_activity(
    *,
    id: str | None = None,
    repository_id: str,
    external_id: str | None = None,
    type: ActivityType = ActivityType.COMMIT,
    title: str = "Test commit message",
    content: str | None = "Detailed commit content",
    author: str = "testuser",
    occurred_at: datetime | None = None,
    files_touched: list[str] | None = None,
    labels: list[str] | None = None,
    linked_issues: list[str] | None = None,
    value_tags: list[str] | None = None,
    lines_added: int = 10,
    lines_deleted: int = 5,
    **kwargs: Any,
) -> Activity:
    """Build an Activity instance without saving to DB."""
    return Activity(
        id=id or generate_uuid(),
        repository_id=repository_id,
        external_id=external_id or f"sha-{generate_uuid()[:8]}",
        type=type,
        title=title,
        content=content,
        author=author,
        occurred_at=occurred_at or datetime.now(UTC),
        files_touched=files_touched or ["src/main.py"],
        labels=labels,
        linked_issues=linked_issues,
        value_tags=value_tags,
        lines_added=lines_added,
        lines_deleted=lines_deleted,
        **kwargs,
    )


def build_pull_request_activity(
    *,
    repository_id: str,
    pr_number: int = 42,
    title: str = "feat: add new feature",
    author: str = "testuser",
    labels: list[str] | None = None,
    merged_at: datetime | None = None,
    **kwargs: Any,
) -> Activity:
    """Build a PR Activity with typical PR fields."""
    now = datetime.now(UTC)
    return build_activity(
        repository_id=repository_id,
        external_id=str(pr_number),
        type=ActivityType.PULL_REQUEST,
        title=title,
        content=f"PR #{pr_number} description",
        author=author,
        labels=labels or ["enhancement"],
        merged_at=merged_at or now,
        first_review_at=now - timedelta(hours=2),
        approved_at=now - timedelta(hours=1),
        pickup_time_hours=2.0,
        review_time_hours=1.0,
        cycle_time_hours=3.0,
        **kwargs,
    )


def build_business_update(
    *,
    id: str | None = None,
    activity_id: str,
    summary: str = "This change improves system performance",
    impact_level: ImpactLevel = ImpactLevel.MEDIUM,
    category: str | None = "Performance",
    **kwargs: Any,
) -> BusinessUpdate:
    """Build a BusinessUpdate instance."""
    return BusinessUpdate(
        id=id or generate_uuid(),
        activity_id=activity_id,
        summary=summary,
        impact_level=impact_level,
        category=category,
        **kwargs,
    )


# =============================================================================
# GitHub API Response Mocks
# =============================================================================


def mock_github_commit(
    sha: str | None = None,
    message: str = "Test commit",
    author: str = "testuser",
    date: str | None = None,
) -> dict[str, Any]:
    """Create a mock GitHub commit API response."""
    return {
        "sha": sha or f"abc{generate_uuid()[:5]}",
        "commit": {
            "message": message,
            "author": {
                "name": author,
                "date": date or datetime.now(UTC).isoformat(),
            },
        },
        "author": {
            "login": author,
        },
        "stats": {
            "additions": 10,
            "deletions": 5,
        },
        "files": [
            {"filename": "src/main.py", "additions": 10, "deletions": 5},
        ],
    }


def mock_github_pull_request(
    number: int = 42,
    title: str = "Test PR",
    body: str = "PR description",
    state: str = "merged",
    user: str = "testuser",
    labels: list[str] | None = None,
    merged_at: str | None = None,
) -> dict[str, Any]:
    """Create a mock GitHub PR API response."""
    now = datetime.now(UTC)
    return {
        "number": number,
        "title": title,
        "body": body,
        "state": state,
        "user": {"login": user},
        "labels": [{"name": label} for label in (labels or [])],
        "created_at": (now - timedelta(days=1)).isoformat(),
        "merged_at": merged_at or now.isoformat() if state == "merged" else None,
        "additions": 50,
        "deletions": 20,
        "changed_files": 3,
    }


def mock_github_repository(
    name: str = "test-repo",
    full_name: str = "owner/test-repo",
    owner: str = "owner",
    private: bool = False,
) -> dict[str, Any]:
    """Create a mock GitHub repository API response."""
    return {
        "id": 123456,
        "name": name,
        "full_name": full_name,
        "owner": {"login": owner},
        "private": private,
        "html_url": f"https://github.com/{full_name}",
        "description": "Test repository",
        "default_branch": "main",
    }


def mock_github_issue(
    number: int = 1,
    title: str = "Test issue",
    body: str = "Issue description",
    state: str = "open",
    user: str = "testuser",
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Create a mock GitHub issue API response."""
    return {
        "number": number,
        "title": title,
        "body": body,
        "state": state,
        "user": {"login": user},
        "labels": [{"name": label} for label in (labels or [])],
        "created_at": datetime.now(UTC).isoformat(),
        "closed_at": None if state == "open" else datetime.now(UTC).isoformat(),
        "pull_request": None,  # Not a PR
    }
