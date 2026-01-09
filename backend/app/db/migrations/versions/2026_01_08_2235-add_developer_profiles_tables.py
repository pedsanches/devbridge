"""Add developer_profiles and contributor_stats tables.

Revision ID: b5d6e7f8g9h0
Revises: a4c5d6e7f8g9
Create Date: 2026-01-08 22:35:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "b5d6e7f8g9h0"
down_revision = "a4c5d6e7f8g9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Developer Profiles table
    op.create_table(
        "developer_profiles",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "organization_id",
            UUID(as_uuid=False),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("github_username", sa.String(255), nullable=False, index=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        # Aggregated metrics
        sa.Column("total_commits", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_prs_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_prs_merged", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_reviews_given", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_issues_closed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_lines_added", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("total_lines_deleted", sa.BigInteger(), server_default="0", nullable=False),
        # Time metrics
        sa.Column("avg_review_time_hours", sa.Float(), nullable=True),
        sa.Column("avg_pr_merge_time_hours", sa.Float(), nullable=True),
        # AI insights
        sa.Column("strength_tags", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("collaboration_score", sa.Float(), nullable=True),
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
        "uq_dev_org_username", "developer_profiles", ["organization_id", "github_username"]
    )

    # Contributor Stats table
    op.create_table(
        "contributor_stats",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "repository_id",
            UUID(as_uuid=False),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("author", sa.String(255), nullable=False, index=True),
        sa.Column("week_start", sa.Date(), nullable=False, index=True),
        # SPACE-Activity
        sa.Column("commits", sa.Integer(), server_default="0", nullable=False),
        sa.Column("prs_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("prs_merged", sa.Integer(), server_default="0", nullable=False),
        sa.Column("reviews_given", sa.Integer(), server_default="0", nullable=False),
        sa.Column("issues_closed", sa.Integer(), server_default="0", nullable=False),
        # Code volume
        sa.Column("additions", sa.Integer(), server_default="0", nullable=False),
        sa.Column("deletions", sa.Integer(), server_default="0", nullable=False),
        # SPACE-Efficiency
        sa.Column("avg_pickup_time_hours", sa.Float(), nullable=True),
        sa.Column("avg_cycle_time_hours", sa.Float(), nullable=True),
        # SPACE-Communication
        sa.Column("comments_given", sa.Integer(), server_default="0", nullable=False),
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
        "uq_contrib_repo_author_week",
        "contributor_stats",
        ["repository_id", "author", "week_start"],
    )


def downgrade() -> None:
    op.drop_table("contributor_stats")
    op.drop_table("developer_profiles")
