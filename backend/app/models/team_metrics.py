"""
Team Metrics Model.

DORA metrics and team-level performance indicators.
"""

from sqlalchemy import Column, Date, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class TeamMetrics(Base, UUIDMixin, TimestampMixin):
    """Team Metrics model.

    Stores DORA metrics and team performance indicators for a period.
    """

    __tablename__ = "team_metrics"

    # Foreign keys
    organization_id: Mapped[str] = Column(
        UUID(as_uuid=False),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team_id: Mapped[str | None] = Column(
        UUID(as_uuid=False),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,  # NULL = organization-wide metrics
        index=True,
    )

    # Period
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False)

    # === DORA Metrics ===
    deployment_frequency = Column(Float, nullable=True)  # Deploys per day
    lead_time_hours = Column(Float, nullable=True)  # Avg commit→merge time
    change_failure_rate = Column(Float, nullable=True)  # Reverts/deploys %
    mttr_hours = Column(Float, nullable=True)  # Mean time to recovery

    # DORA Performance Level (elite, high, medium, low)
    dora_level = Column(String(20), nullable=True)

    # === Additional Team Metrics ===
    avg_cycle_time_hours = Column(Float, nullable=True)
    avg_pickup_time_hours = Column(Float, nullable=True)
    avg_review_time_hours = Column(Float, nullable=True)
    total_prs_merged = Column(Float, nullable=True)
    total_commits = Column(Float, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="team_metrics")
    team = relationship("Team", back_populates="team_metrics")

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "team_id", "period_start", name="uq_team_metrics_period"
        ),
    )

    def __repr__(self) -> str:
        return f"<TeamMetrics {self.period_start} - {self.dora_level or 'N/A'}>"
