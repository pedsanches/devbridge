"""
Report Model.

Persists generated reports for history and retrieval.
Implements the storage layer for BR-030 persona-based reports.
"""

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ReportType(str, enum.Enum):
    """Type of report, aligned with personas (BR-030)."""

    WEEKLY_SUMMARY = "weekly_summary"  # PM: Focus on deliverables, progress
    TECHNICAL_REPORT = "technical_report"  # CTO: Metrics, decisions, tech debt
    EXECUTIVE_SUMMARY = "executive_summary"  # CEO: Max 5 bullets, zero jargon
    CUSTOM = "custom"


class Report(Base, UUIDMixin, TimestampMixin):
    """Stored report for history and retrieval.

    Multi-tenant: isolated by organization_id.
    """

    __tablename__ = "reports"

    # Multi-tenancy
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    team_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Report metadata
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(500), nullable=False)

    # Period information
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_description: Mapped[str] = mapped_column(String(100), nullable=False)

    # Report content (stored as JSON for flexibility)
    sections_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    summary_metrics_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Analytics
    sources_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # When the report was generated (may differ from created_at if saved later)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="reports")
    user = relationship("User", back_populates="reports")
    team = relationship("Team", foreign_keys=[team_id])
