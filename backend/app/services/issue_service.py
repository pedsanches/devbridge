"""
Issue Service.

Service layer for Issue model operations.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.issue import Issue
from app.schemas.issue import IssueCreate


async def get_or_create_issue(db: AsyncSession, issue_in: IssueCreate) -> tuple[Issue, bool]:
    """
    Get existing issue by repository_id and issue_number, or create new.

    Args:
        db: Database session.
        issue_in: Issue data to create.

    Returns:
        Tuple of (Issue, created_flag).
    """
    query = select(Issue).where(
        Issue.repository_id == str(issue_in.repository_id),
        Issue.issue_number == issue_in.issue_number,
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        return existing, False

    issue = Issue(
        repository_id=str(issue_in.repository_id),
        issue_number=issue_in.issue_number,
        title=issue_in.title,
        body=issue_in.body,
        state=issue_in.state,
        author=issue_in.author,
        assignees=issue_in.assignees,
        labels=issue_in.labels,
        milestone=issue_in.milestone,
        opened_at=issue_in.opened_at,
        closed_at=issue_in.closed_at,
        closed_by=issue_in.closed_by,
        time_to_close_hours=issue_in.time_to_close_hours,
        linked_pr_numbers=issue_in.linked_pr_numbers,
    )
    db.add(issue)
    await db.commit()
    await db.refresh(issue)
    return issue, True


async def get_issues_by_repository(
    db: AsyncSession, repository_id: UUID, limit: int = 100
) -> list[Issue]:
    """
    Get issues for a repository.

    Args:
        db: Database session.
        repository_id: Repository UUID.
        limit: Maximum issues to return.

    Returns:
        List of Issue objects.
    """
    query = (
        select(Issue)
        .where(Issue.repository_id == str(repository_id))
        .order_by(Issue.opened_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_open_issues_count(db: AsyncSession, repository_id: UUID) -> int:
    """Get count of open issues for a repository."""
    from app.models.issue import IssueState

    query = select(Issue).where(
        Issue.repository_id == str(repository_id),
        Issue.state == IssueState.OPEN,
    )
    result = await db.execute(query)
    return len(list(result.scalars().all()))
