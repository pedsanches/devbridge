"""add_reports_table

Revision ID: a7bc3d4e5f6g
Revises: 8d53d621a973
Create Date: 2026-01-06 19:43:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a7bc3d4e5f6g"
down_revision: str | Sequence[str] | None = "874d6f5559b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create reports table
    op.create_table(
        "reports",
        sa.Column("organization_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "report_type",
            sa.Enum("WEEKLY_SUMMARY", "TECHNICAL_REPORT", "EXECUTIVE_SUMMARY", name="reporttype"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("subtitle", sa.String(length=500), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_description", sa.String(length=100), nullable=False),
        sa.Column("sections_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("summary_metrics_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("sources_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Create indexes for efficient querying
    op.create_index(
        op.f("ix_reports_organization_id"), "reports", ["organization_id"], unique=False
    )
    op.create_index(op.f("ix_reports_user_id"), "reports", ["user_id"], unique=False)
    op.create_index(op.f("ix_reports_report_type"), "reports", ["report_type"], unique=False)
    op.create_index(op.f("ix_reports_generated_at"), "reports", ["generated_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_reports_generated_at"), table_name="reports")
    op.drop_index(op.f("ix_reports_report_type"), table_name="reports")
    op.drop_index(op.f("ix_reports_user_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_organization_id"), table_name="reports")
    op.drop_table("reports")
    # Drop the enum type
    sa.Enum(name="reporttype").drop(op.get_bind(), checkfirst=True)
