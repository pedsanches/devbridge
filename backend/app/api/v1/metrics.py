"""
Metrics API endpoints.

Endpoints for retrieving DORA metrics, developer profiles, and team statistics.
"""

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentOrgId, get_current_user, get_db
from app.models.user import User
from app.services import metrics_service

router = APIRouter(prefix="/metrics", tags=["Metrics"])


# Response schemas
class DoraMetricResponse(BaseModel):
    """Single DORA metric with trend data."""

    value: float | str
    formatted: str
    change: float | None = None
    trend: str | None = None  # "up", "down", "stable"
    status: str  # "elite", "high", "medium", "low"


class DoraMetricsResponse(BaseModel):
    """Complete DORA metrics response."""

    deployment_frequency: DoraMetricResponse
    lead_time: DoraMetricResponse
    change_failure_rate: DoraMetricResponse
    mttr: DoraMetricResponse
    overall_level: str
    period_start: date
    period_end: date


class DeveloperProfileResponse(BaseModel):
    """Developer profile summary."""

    github_username: str
    total_commits: int
    total_prs: int
    avg_pr_cycle_time_hours: float | None
    strength_tags: list[str]
    collaboration_score: float


class DeveloperLeaderboardResponse(BaseModel):
    """Leaderboard response."""

    developers: list[DeveloperProfileResponse]
    period_start: date
    period_end: date


def classify_metric_status(value: float, thresholds: dict) -> str:
    """Classify metric into status levels based on thresholds."""
    if value <= thresholds.get("elite", 0):
        return "elite"
    if value <= thresholds.get("high", 0):
        return "high"
    if value <= thresholds.get("medium", 0):
        return "medium"
    return "low"


def format_duration(hours: float | None) -> str:
    """Format duration in hours to human readable string."""
    if hours is None or hours == 0:
        return "—"
    if hours < 1:
        return f"{int(hours * 60)} min"
    if hours < 24:
        return f"{hours:.1f}h"
    days = hours / 24
    return f"{days:.1f} dias"


def format_frequency(per_day: float | None) -> str:
    """Format deployment frequency to human readable string."""
    if per_day is None or per_day == 0:
        return "—"
    if per_day >= 1:
        return f"{per_day:.1f}/dia"
    per_week = per_day * 7
    if per_week >= 1:
        return f"{per_week:.1f}/sem"
    return f"{per_day * 30:.1f}/mês"


def format_percentage(value: float | None) -> str:
    """Format percentage value."""
    if value is None:
        return "—"
    return f"{value * 100:.1f}%"


@router.get("/dora", response_model=DoraMetricsResponse)
async def get_dora_metrics(
    _current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    org_id: CurrentOrgId,
    days: int = Query(default=30, ge=7, le=365, description="Period in days"),
    team_id: str | None = Query(default=None, description="Filter metrics by Team ID"),
):
    """
    Get DORA metrics for the organization.

    Returns deployment frequency, lead time, change failure rate, and MTTR.
    """
    period_end = date.today()
    period_start = period_end - timedelta(days=days)

    # Calculate current period metrics
    metrics = await metrics_service.calculate_dora_metrics(
        db=db,
        organization_id=org_id,
        period_start=period_start,
        period_end=period_end,
        team_id=team_id,
    )

    # Calculate previous period for trend comparison
    prev_period_end = period_start
    prev_period_start = prev_period_end - timedelta(days=days)
    prev_metrics = await metrics_service.calculate_dora_metrics(
        db=db,
        organization_id=org_id,
        period_start=prev_period_start,
        period_end=prev_period_end,
        team_id=team_id,
    )

    # Calculate trends
    def calc_trend(
        current: float | None, previous: float | None, invert: bool = False
    ) -> tuple[float | None, str]:
        if current is None or previous is None or previous == 0:
            return None, "stable"
        change = ((current - previous) / previous) * 100
        if abs(change) < 5:
            return change, "stable"
        trend = "down" if change < 0 else "up"
        if invert:
            trend = "up" if trend == "down" else "down"
        return change, trend

    # Deployment frequency (higher is better)
    df_change, df_trend = calc_trend(
        metrics.deployment_frequency, prev_metrics.deployment_frequency
    )

    # Lead time (lower is better)
    lt_change, lt_trend = calc_trend(
        metrics.lead_time_hours, prev_metrics.lead_time_hours, invert=True
    )

    # Change failure rate (lower is better)
    cfr_change, cfr_trend = calc_trend(
        metrics.change_failure_rate, prev_metrics.change_failure_rate, invert=True
    )

    # MTTR - using avg cycle time as proxy (lower is better)
    mttr_hours = metrics.avg_cycle_time_hours or 0
    prev_mttr = prev_metrics.avg_cycle_time_hours or 0
    mttr_change, mttr_trend = calc_trend(mttr_hours, prev_mttr, invert=True)

    return DoraMetricsResponse(
        deployment_frequency=DoraMetricResponse(
            value=metrics.deployment_frequency or 0,
            formatted=format_frequency(metrics.deployment_frequency),
            change=df_change,
            trend=df_trend,
            status=classify_deployment_frequency(metrics.deployment_frequency or 0),
        ),
        lead_time=DoraMetricResponse(
            value=metrics.lead_time_hours or 0,
            formatted=format_duration(metrics.lead_time_hours),
            change=lt_change,
            trend=lt_trend,
            status=classify_lead_time(metrics.lead_time_hours or 0),
        ),
        change_failure_rate=DoraMetricResponse(
            value=metrics.change_failure_rate or 0,
            formatted=format_percentage(metrics.change_failure_rate),
            change=cfr_change,
            trend=cfr_trend,
            status=classify_change_failure_rate(metrics.change_failure_rate or 0),
        ),
        mttr=DoraMetricResponse(
            value=mttr_hours,
            formatted=format_duration(mttr_hours),
            change=mttr_change,
            trend=mttr_trend,
            status=classify_mttr(mttr_hours),
        ),
        overall_level=metrics.dora_level or "medium",
        period_start=period_start,
        period_end=period_end,
    )


def classify_deployment_frequency(per_day: float) -> str:
    """Classify deployment frequency: elite > 1/day, high > 1/week, medium > 1/month."""
    if per_day >= 1:
        return "elite"
    if per_day >= 1 / 7:
        return "high"
    if per_day >= 1 / 30:
        return "medium"
    return "low"


def classify_lead_time(hours: float) -> str:
    """Classify lead time: elite < 24h, high < 168h (1 week), medium < 720h (1 month)."""
    if hours < 24:
        return "elite"
    if hours < 168:
        return "high"
    if hours < 720:
        return "medium"
    return "low"


def classify_change_failure_rate(rate: float) -> str:
    """Classify CFR: elite < 5%, high < 10%, medium < 15%."""
    if rate < 0.05:
        return "elite"
    if rate < 0.10:
        return "high"
    if rate < 0.15:
        return "medium"
    return "low"


def classify_mttr(hours: float) -> str:
    """Classify MTTR: elite < 1h, high < 24h, medium < 168h (1 week)."""
    if hours < 1:
        return "elite"
    if hours < 24:
        return "high"
    if hours < 168:
        return "medium"
    return "low"


@router.get("/developers", response_model=DeveloperLeaderboardResponse)
async def get_developer_leaderboard(
    _current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    org_id: CurrentOrgId,
    limit: int = Query(default=10, ge=1, le=50, description="Number of developers to return"),
    days: int = Query(default=30, ge=7, le=365, description="Period in days"),
):
    """
    Get developer leaderboard for the organization.

    Returns top developers by contributions with their metrics.
    """
    period_end = date.today()
    period_start = period_end - timedelta(days=days)

    developers = await metrics_service.get_developer_leaderboard(
        db=db,
        organization_id=org_id,
        limit=limit,
    )

    return DeveloperLeaderboardResponse(
        developers=[
            DeveloperProfileResponse(
                github_username=dev.github_username,
                total_commits=dev.total_commits or 0,
                total_prs=dev.total_prs or 0,
                avg_pr_cycle_time_hours=dev.avg_pr_cycle_time_hours,
                strength_tags=dev.strength_tags or [],
                collaboration_score=dev.collaboration_score or 0,
            )
            for dev in developers
        ],
        period_start=period_start,
        period_end=period_end,
    )
