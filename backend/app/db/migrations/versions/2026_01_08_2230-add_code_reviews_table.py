"""Add code_reviews table.

Revision ID: a4c5d6e7f8g9
Revises: 9b3d0e4f5a6c
Create Date: 2026-01-08 22:30:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "a4c5d6e7f8g9"
down_revision = "9b3d0e4f5a6c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "code_reviews",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "activity_id",
            UUID(as_uuid=False),
            sa.ForeignKey("activities.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("review_id", sa.Integer(), nullable=False, index=True),
        sa.Column("reviewer", sa.String(255), nullable=False),
        sa.Column(
            "state",
            sa.Enum(
                "APPROVED",
                "CHANGES_REQUESTED",
                "COMMENTED",
                "PENDING",
                "DISMISSED",
                name="reviewstate",
            ),
            nullable=False,
        ),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("comments_count", sa.Integer(), server_default="0", nullable=False),
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

    # Create unique constraint for activity + review_id
    op.create_unique_constraint(
        "uq_review_activity_review_id",
        "code_reviews",
        ["activity_id", "review_id"],
    )


def downgrade() -> None:
    op.drop_table("code_reviews")
    op.execute("DROP TYPE IF EXISTS reviewstate")
