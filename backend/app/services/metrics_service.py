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
from app.models.team_metrics import TeamMetrics

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


def classify_dora_level(
    deployment_frequency: float,
    lead_time_hours: float,
    change_failure_rate: float,
) -> str:
    """
    Classify DORA performance level based on metrics.

    Returns: 'elite', 'high', 'medium', or 'low'
    """
    # Elite: Multiple deploys/day, < 1 hour lead time, < 5% failure rate
    if deployment_frequency >= 1 and lead_time_hours < 1 and change_failure_rate < 0.05:
        return "elite"

    # High: Weekly-Daily deploys, 1 day - 1 week lead time, 5-10% failure rate
    if deployment_frequency >= 0.14 and lead_time_hours < 168 and change_failure_rate < 0.10:
        return "high"

    # Medium: Monthly-Weekly, 1 week - 1 month, 10-15% failure rate
    if deployment_frequency >= 0.03 and lead_time_hours < 720 and change_failure_rate < 0.15:
        return "medium"

    return "low"


async def calculate_dora_metrics(
    db: AsyncSession,
    organization_id: str,
    period_start: date,
    period_end: date,
    team_id: str | None = None,
) -> "TeamMetrics":
    """
    Calculate DORA metrics for a team or organization.

    Args:
        db: Database session.
        organization_id: Organization ID.
        period_start: Start of period.
        period_end: End of period.
        team_id: Optional team ID (None = org-wide).

    Returns:
        TeamMetrics with calculated DORA metrics.
    """
    # Check for existing metrics (order by created_at DESC to get most recent if duplicates exist)
    query = (
        select(TeamMetrics)
        .where(
            TeamMetrics.organization_id == organization_id,
            TeamMetrics.period_start == period_start,
            TeamMetrics.period_end == period_end,
        )
        .order_by(TeamMetrics.created_at.desc())
        .limit(1)
    )
    if team_id:
        query = query.where(TeamMetrics.team_id == team_id)
    else:
        query = query.where(TeamMetrics.team_id.is_(None))

    result = await db.execute(query)
    metrics = result.scalar_one_or_none()

    if not metrics:
        metrics = TeamMetrics(
            organization_id=organization_id,
            team_id=team_id,
            period_start=period_start,
            period_end=period_end,
        )
        db.add(metrics)

    # Calculate days in period
    period_days = (period_end - period_start).days or 1

    # Deployment Frequency: PRs merged to main
    deploy_query = (
        select(func.count(Activity.id))
        .join(Activity.repository)
        .where(
            Activity.type == ActivityType.PULL_REQUEST,
            Activity.merged_at.isnot(None),
            Activity.merged_at >= period_start,
            Activity.merged_at < period_end,
        )
    )
    deploy_result = await db.execute(deploy_query)
    total_deploys = deploy_result.scalar() or 0
    metrics.deployment_frequency = total_deploys / period_days
    metrics.total_prs_merged = total_deploys

    # Lead Time: Average cycle time
    lead_time_query = select(func.avg(Activity.cycle_time_hours)).where(
        Activity.type == ActivityType.PULL_REQUEST,
        Activity.merged_at >= period_start,
        Activity.merged_at < period_end,
        Activity.cycle_time_hours.isnot(None),
    )
    lead_time_result = await db.execute(lead_time_query)
    metrics.lead_time_hours = lead_time_result.scalar() or 0

    # Change Failure Rate: Reverted PRs / Total
    reverted_query = select(func.count(Activity.id)).where(
        Activity.type == ActivityType.PULL_REQUEST,
        Activity.is_reverted.is_(True),
        Activity.merged_at >= period_start,
        Activity.merged_at < period_end,
    )
    reverted_result = await db.execute(reverted_query)
    reverted_count = reverted_result.scalar() or 0
    metrics.change_failure_rate = reverted_count / total_deploys if total_deploys > 0 else 0

    # Average cycle and pickup times
    time_query = select(
        func.avg(Activity.cycle_time_hours),
        func.avg(Activity.pickup_time_hours),
        func.avg(Activity.review_time_hours),
    ).where(
        Activity.type == ActivityType.PULL_REQUEST,
        Activity.merged_at >= period_start,
        Activity.merged_at < period_end,
    )
    time_result = await db.execute(time_query)
    time_row = time_result.one()
    metrics.avg_cycle_time_hours = time_row[0]
    metrics.avg_pickup_time_hours = time_row[1]
    metrics.avg_review_time_hours = time_row[2]

    # Total commits
    commits_query = select(func.count(Activity.id)).where(
        Activity.type == ActivityType.COMMIT,
        Activity.created_at >= period_start,
        Activity.created_at < period_end,
    )
    commits_result = await db.execute(commits_query)
    metrics.total_commits = commits_result.scalar() or 0

    # Classify DORA level
    metrics.dora_level = classify_dora_level(
        metrics.deployment_frequency or 0,
        metrics.lead_time_hours or 0,
        metrics.change_failure_rate or 0,
    )

    await db.commit()
    await db.refresh(metrics)
    return metrics
