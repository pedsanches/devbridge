"""Add team_metrics table.

Revision ID: c6e7f8g9h0i1
Revises: b5d6e7f8g9h0
Create Date: 2026-01-08 22:40:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "c6e7f8g9h0i1"
down_revision = "b5d6e7f8g9h0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "team_metrics",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "organization_id",
            UUID(as_uuid=False),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "team_id",
            UUID(as_uuid=False),
            sa.ForeignKey("teams.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        # Period
        sa.Column("period_start", sa.Date(), nullable=False, index=True),
        sa.Column("period_end", sa.Date(), nullable=False),
        # DORA Metrics
        sa.Column("deployment_frequency", sa.Float(), nullable=True),
        sa.Column("lead_time_hours", sa.Float(), nullable=True),
        sa.Column("change_failure_rate", sa.Float(), nullable=True),
        sa.Column("mttr_hours", sa.Float(), nullable=True),
        sa.Column("dora_level", sa.String(20), nullable=True),
        # Additional metrics
        sa.Column("avg_cycle_time_hours", sa.Float(), nullable=True),
        sa.Column("avg_pickup_time_hours", sa.Float(), nullable=True),
        sa.Column("avg_review_time_hours", sa.Float(), nullable=True),
        sa.Column("total_prs_merged", sa.Float(), nullable=True),
        sa.Column("total_commits", sa.Float(), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_unique_constraint(
        "uq_team_metrics_period",
        "team_metrics",
        ["organization_id", "team_id", "period_start"],
    )


def downgrade() -> None:
    op.drop_table("team_metrics")
