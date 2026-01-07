"""Add report_templates table.

Revision ID: b8cd4e5f6g7h
Revises: a7bc3d4e5f6g
Create Date: 2026-01-06 17:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b8cd4e5f6g7h"
down_revision: str | None = "a7bc3d4e5f6g"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create report_templates table
    op.create_table(
        "report_templates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "data_filters",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Filters: repositories, authors, activity_types, impact_levels, value_tags, labels",
        ),
        sa.Column(
            "sections_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            comment="Section configs: type, title, enabled, order, detail_level, custom_prompt",
        ),
        sa.Column(
            "language_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Language: language, formality, jargon_level, verbosity, tone, format",
        ),
        sa.Column(
            "visual_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Visual: primary_color, secondary_color, font_family, logo_url, show_charts, watermark",
        ),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
    )

    # Create indexes
    op.create_index(
        "ix_report_templates_organization_id",
        "report_templates",
        ["organization_id"],
    )
    op.create_index(
        "ix_report_templates_user_id",
        "report_templates",
        ["user_id"],
    )
    op.create_index(
        "ix_report_templates_is_default",
        "report_templates",
        ["is_default"],
        postgresql_where=sa.text("is_default = true"),
    )


def downgrade() -> None:
    op.drop_index("ix_report_templates_is_default", table_name="report_templates")
    op.drop_index("ix_report_templates_user_id", table_name="report_templates")
    op.drop_index("ix_report_templates_organization_id", table_name="report_templates")
    op.drop_table("report_templates")
