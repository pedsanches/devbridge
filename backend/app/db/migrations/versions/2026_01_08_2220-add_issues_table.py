"""Add issues table.

Revision ID: 9b3d0e4f5a6c
Revises: 8a2c9d3f4e5b
Create Date: 2026-01-08 22:20:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "9b3d0e4f5a6c"
down_revision = "8a2c9d3f4e5b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "issues",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "repository_id",
            UUID(as_uuid=False),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("issue_number", sa.Integer(), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "state",
            sa.Enum("open", "closed", name="issuestate"),
            nullable=False,
        ),
        sa.Column("author", sa.String(255), nullable=False),
        sa.Column("assignees", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("labels", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("milestone", sa.String(255), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by", sa.String(255), nullable=True),
        sa.Column("time_to_close_hours", sa.Float(), nullable=True),
        sa.Column("linked_pr_numbers", sa.ARRAY(sa.Integer()), nullable=True),
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

    # Create unique constraint for repository + issue number
    op.create_unique_constraint(
        "uq_issue_repo_number",
        "issues",
        ["repository_id", "issue_number"],
    )


def downgrade() -> None:
    op.drop_table("issues")
    op.execute("DROP TYPE IF EXISTS issuestate")
