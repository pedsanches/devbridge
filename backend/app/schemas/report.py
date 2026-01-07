"""
Report Schemas.

Pydantic schemas for structured report generation.
Implements BR-030 (persona-based reports) and BR-011 (structured output).
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ReportType(str, Enum):
    """Type of report to generate, aligned with personas (BR-030)."""

    WEEKLY_SUMMARY = "weekly_summary"  # PM: Focus on deliverables, progress
    TECHNICAL_REPORT = "technical_report"  # CTO: Metrics, decisions, tech debt
    EXECUTIVE_SUMMARY = "executive_summary"  # CEO: Max 5 bullets, zero jargon
    CUSTOM = "custom"


class ReportPeriod(BaseModel):
    """Time period for report generation."""

    start: datetime = Field(..., description="Start of the period (inclusive)")
    end: datetime = Field(..., description="End of the period (inclusive)")


class ReportRequest(BaseModel):
    """Schema for report generation request."""

    report_type: ReportType = Field(..., description="Type of report to generate")
    period: ReportPeriod = Field(..., description="Time period for the report")
    repositories: list[str] | None = Field(
        None, description="Filter by repository names (None = all accessible)"
    )

    model_config = {"populate_by_name": True}


class ReportMetric(BaseModel):
    """A metric to include in the report."""

    name: str = Field(..., description="Metric name (e.g., 'Commits', 'PRs Merged')")
    value: str | int | float = Field(..., description="Metric value")
    change: str | None = Field(None, description="Change vs previous period (e.g., '+15%')")
    trend: Literal["up", "down", "stable"] | None = Field(None, description="Trend direction")


class ReportSection(BaseModel):
    """A section within the report."""

    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content in markdown")
    metrics: list[ReportMetric] | None = Field(None, description="Associated metrics")


class ReportSource(BaseModel):
    """A source activity used to generate the report."""

    title: str = Field(..., description="Activity title")
    repository: str = Field(..., description="Repository name")
    type: str = Field(..., description="Activity type (commit, pr, issue)")
    url: str | None = Field(None, description="Link to the activity")


class ReportResponse(BaseModel):
    """Schema for generated report response."""

    title: str = Field(..., description="Report title")
    subtitle: str = Field(..., description="Brief description or period summary")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the report was generated"
    )
    period_description: str = Field(
        ..., description="Human-readable period (e.g., '01 Jan - 07 Jan 2026')"
    )
    report_type: ReportType = Field(..., description="Type of report generated")
    sections: list[ReportSection] = Field(..., description="Report sections")
    summary_metrics: list[ReportMetric] | None = Field(
        None, description="Key metrics summary at the top"
    )
    confidence_score: float = Field(ge=0.0, le=1.0, description="AI confidence in report accuracy")
    sources_count: int = Field(..., description="Number of activities used as source")
    sources: list[ReportSource] = Field(
        default_factory=list, description="Top sources used (max 10)"
    )
    format: Literal["markdown", "html"] = Field("markdown", description="Output format")


class ReportExportRequest(BaseModel):
    """Schema for exporting a report to different formats."""

    report: ReportResponse = Field(..., description="The report to export")
    format: Literal["markdown", "pdf", "html"] = Field("markdown", description="Export format")


# ============================================================
# History/Persistence Schemas
# ============================================================


class SaveReportRequest(BaseModel):
    """Request to save a generated report to history."""

    title: str = Field(..., description="Report title")
    subtitle: str = Field(..., description="Brief description")
    report_type: ReportType = Field(..., description="Type of report")
    period_start: datetime = Field(..., description="Period start date")
    period_end: datetime = Field(..., description="Period end date")
    period_description: str = Field(..., description="Human-readable period")
    sections: list[ReportSection] = Field(..., description="Report sections")
    summary_metrics: list[ReportMetric] | None = Field(None, description="Summary metrics")
    sources_count: int = Field(..., description="Number of sources")
    confidence_score: float = Field(ge=0.0, le=1.0, description="AI confidence")
    generated_at: datetime = Field(..., description="When report was generated")


class ReportListItem(BaseModel):
    """Compact report item for list display."""

    id: str = Field(..., description="Report UUID")
    report_type: ReportType = Field(..., description="Type of report")
    title: str = Field(..., description="Report title")
    period_description: str = Field(..., description="Human-readable period")
    generated_at: datetime = Field(..., description="When report was generated")
    sources_count: int = Field(..., description="Number of sources used")
    confidence_score: float = Field(..., description="AI confidence score")


class ReportListResponse(BaseModel):
    """Paginated list of saved reports."""

    items: list[ReportListItem] = Field(..., description="List of reports")
    total: int = Field(..., description="Total number of reports")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(10, description="Items per page")
    has_more: bool = Field(..., description="Whether more pages exist")


class SavedReportResponse(BaseModel):
    """Full saved report with all details."""

    id: str = Field(..., description="Report UUID")
    title: str = Field(..., description="Report title")
    subtitle: str = Field(..., description="Brief description")
    report_type: ReportType = Field(..., description="Type of report")
    period_start: datetime = Field(..., description="Period start")
    period_end: datetime = Field(..., description="Period end")
    period_description: str = Field(..., description="Human-readable period")
    sections: list[ReportSection] = Field(..., description="Report sections")
    summary_metrics: list[ReportMetric] | None = Field(None, description="Summary metrics")
    sources_count: int = Field(..., description="Number of sources")
    confidence_score: float = Field(..., description="AI confidence")
    generated_at: datetime = Field(..., description="When report was generated")
    created_at: datetime = Field(..., description="When saved to database")
