"""Add code metrics and PR lifecycle fields to activities.

Revision ID: 8a2c9d3f4e5b
Revises: ca8e14e85644
Create Date: 2026-01-08 22:10:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8a2c9d3f4e5b"
down_revision = "ca8e14e85644"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === Code Metrics ===
    op.add_column("activities", sa.Column("lines_added", sa.Integer(), nullable=True))
    op.add_column("activities", sa.Column("lines_deleted", sa.Integer(), nullable=True))
    op.add_column("activities", sa.Column("files_changed_count", sa.Integer(), nullable=True))

    # === PR Lifecycle Timestamps ===
    op.add_column(
        "activities", sa.Column("first_review_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("activities", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("activities", sa.Column("merged_at", sa.DateTime(timezone=True), nullable=True))

    # === Calculated Time Metrics (hours) ===
    op.add_column("activities", sa.Column("pickup_time_hours", sa.Float(), nullable=True))
    op.add_column("activities", sa.Column("review_time_hours", sa.Float(), nullable=True))
    op.add_column("activities", sa.Column("merge_time_hours", sa.Float(), nullable=True))
    op.add_column("activities", sa.Column("cycle_time_hours", sa.Float(), nullable=True))

    # === Review Quality Metrics ===
    op.add_column(
        "activities", sa.Column("review_count", sa.Integer(), server_default="0", nullable=False)
    )
    op.add_column(
        "activities",
        sa.Column("rework_iterations", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "activities",
        sa.Column("comments_received", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "activities", sa.Column("is_reverted", sa.Boolean(), server_default="false", nullable=False)
    )
    op.add_column("activities", sa.Column("reverted_by_pr", sa.String(50), nullable=True))


def downgrade() -> None:
    # === Review Quality Metrics ===
    op.drop_column("activities", "reverted_by_pr")
    op.drop_column("activities", "is_reverted")
    op.drop_column("activities", "comments_received")
    op.drop_column("activities", "rework_iterations")
    op.drop_column("activities", "review_count")

    # === Calculated Time Metrics ===
    op.drop_column("activities", "cycle_time_hours")
    op.drop_column("activities", "merge_time_hours")
    op.drop_column("activities", "review_time_hours")
    op.drop_column("activities", "pickup_time_hours")

    # === PR Lifecycle Timestamps ===
    op.drop_column("activities", "merged_at")
    op.drop_column("activities", "approved_at")
    op.drop_column("activities", "first_review_at")

    # === Code Metrics ===
    op.drop_column("activities", "files_changed_count")
    op.drop_column("activities", "lines_deleted")
    op.drop_column("activities", "lines_added")
