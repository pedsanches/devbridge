"""
Metrics Service.

Service for calculating and aggregating developer metrics.
"""

import logging
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity, ActivityType
from app.models.code_review import CodeReview
from app.models.contributor_stats import ContributorStats
from app.models.developer_profile import DeveloperProfile
from app.models.issue import Issue, IssueState

logger = logging.getLogger(__name__)


async def get_or_create_developer_profile(
    db: AsyncSession, organization_id: str, github_username: str
) -> DeveloperProfile:
    """Get or create a developer profile."""
    query = select(DeveloperProfile).where(
        DeveloperProfile.organization_id == organization_id,
        DeveloperProfile.github_username == github_username,
    )
    result = await db.execute(query)
    profile = result.scalar_one_or_none()

    if not profile:
        profile = DeveloperProfile(
            organization_id=organization_id,
            github_username=github_username,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return profile


async def calculate_developer_metrics(
    db: AsyncSession, organization_id: str, github_username: str
) -> DeveloperProfile:
    """
    Calculate aggregated metrics for a developer.

    Args:
        db: Database session.
        organization_id: Organization ID.
        github_username: GitHub username.

    Returns:
        Updated DeveloperProfile.
    """
    profile = await get_or_create_developer_profile(db, organization_id, github_username)

    # Count commits
    commits_query = (
        select(func.count(Activity.id))
        .join(Activity.repository)
        .where(
            Activity.author == github_username,
            Activity.type == ActivityType.COMMIT,
        )
    )
    commits_result = await db.execute(commits_query)
    profile.total_commits = commits_result.scalar() or 0

    # Count PRs created and merged
    prs_query = select(
        func.count(Activity.id).filter(Activity.type == ActivityType.PULL_REQUEST),
        func.count(Activity.id).filter(
            Activity.type == ActivityType.PULL_REQUEST,
            Activity.merged_at.isnot(None),
        ),
    ).where(Activity.author == github_username)
    prs_result = await db.execute(prs_query)
    prs_row = prs_result.one()
    profile.total_prs_created = prs_row[0] or 0
    profile.total_prs_merged = prs_row[1] or 0

    # Count reviews given
    reviews_query = select(func.count(CodeReview.id)).where(CodeReview.reviewer == github_username)
    reviews_result = await db.execute(reviews_query)
    profile.total_reviews_given = reviews_result.scalar() or 0

    # Count issues closed
    issues_query = select(func.count(Issue.id)).where(
        Issue.closed_by == github_username,
        Issue.state == IssueState.CLOSED,
    )
    issues_result = await db.execute(issues_query)
    profile.total_issues_closed = issues_result.scalar() or 0

    # Sum lines added/deleted
    lines_query = select(
        func.coalesce(func.sum(Activity.lines_added), 0),
        func.coalesce(func.sum(Activity.lines_deleted), 0),
    ).where(Activity.author == github_username)
    lines_result = await db.execute(lines_query)
    lines_row = lines_result.one()
    profile.total_lines_added = lines_row[0]
    profile.total_lines_deleted = lines_row[1]

    # Calculate average PR merge time
    merge_time_query = select(func.avg(Activity.cycle_time_hours)).where(
        Activity.author == github_username,
        Activity.type == ActivityType.PULL_REQUEST,
        Activity.cycle_time_hours.isnot(None),
    )
    merge_time_result = await db.execute(merge_time_query)
    profile.avg_pr_merge_time_hours = merge_time_result.scalar()

    await db.commit()
    await db.refresh(profile)
    return profile


async def update_weekly_contributor_stats(
    db: AsyncSession, repository_id: str, week_start: date
) -> list[ContributorStats]:
    """
    Update weekly contributor stats for a repository.

    Args:
        db: Database session.
        repository_id: Repository UUID.
        week_start: Start of the week (usually Monday).

    Returns:
        List of updated ContributorStats.
    """
    week_end = week_start + timedelta(days=7)

    # Get all activities for the week
    activities_query = (
        select(
            Activity.author,
            func.count(Activity.id).filter(Activity.type == ActivityType.COMMIT).label("commits"),
            func.count(Activity.id)
            .filter(Activity.type == ActivityType.PULL_REQUEST)
            .label("prs_created"),
            func.count(Activity.id)
            .filter(
                Activity.type == ActivityType.PULL_REQUEST,
                Activity.merged_at.isnot(None),
            )
            .label("prs_merged"),
            func.coalesce(func.sum(Activity.lines_added), 0).label("additions"),
            func.coalesce(func.sum(Activity.lines_deleted), 0).label("deletions"),
            func.avg(Activity.pickup_time_hours).label("avg_pickup_time"),
            func.avg(Activity.cycle_time_hours).label("avg_cycle_time"),
        )
        .where(
            Activity.repository_id == repository_id,
            Activity.created_at >= week_start,
            Activity.created_at < week_end,
        )
        .group_by(Activity.author)
    )
    result = await db.execute(activities_query)
    rows = result.all()

    stats_list = []
    for row in rows:
        # Check if stats exist
        existing_query = select(ContributorStats).where(
            ContributorStats.repository_id == repository_id,
            ContributorStats.author == row.author,
            ContributorStats.week_start == week_start,
        )
        existing_result = await db.execute(existing_query)
        stats = existing_result.scalar_one_or_none()

        if not stats:
            stats = ContributorStats(
                repository_id=repository_id,
                author=row.author,
                week_start=week_start,
            )
            db.add(stats)

        stats.commits = row.commits
        stats.prs_created = row.prs_created
        stats.prs_merged = row.prs_merged
        stats.additions = row.additions
        stats.deletions = row.deletions
        stats.avg_pickup_time_hours = row.avg_pickup_time
        stats.avg_cycle_time_hours = row.avg_cycle_time

        stats_list.append(stats)

    await db.commit()
    return stats_list


async def get_developer_leaderboard(
    db: AsyncSession, organization_id: str, limit: int = 10
) -> list[DeveloperProfile]:
    """Get top developers by total contributions."""
    query = (
        select(DeveloperProfile)
        .where(DeveloperProfile.organization_id == organization_id)
        .order_by(
            (
                DeveloperProfile.total_commits
                + DeveloperProfile.total_prs_merged
                + DeveloperProfile.total_reviews_given
            ).desc()
        )
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())
