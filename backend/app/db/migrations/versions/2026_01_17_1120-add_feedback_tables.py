"""Add feedback and event_log tables.

Revision ID: f33db4ck0001
Revises: d4c8e5f6a7b9
Create Date: 2026-01-17 11:20:00.000000

Implements Feedback Schema v1.1 with:
- Idempotency via unique constraint on idempotency_key
- Lineage tracking via generation_id and prompt_version_id
- Weighted scoring with score_raw, weight, and score_effective
- EventLog for feedback funnel observability

Reference: docs/architecture/continuous-learning-execution-plan.md
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision = "f33db4ck0001"
down_revision = "196dbefb24e2"  # 2026_01_16_1823-add_context_fields_to_conversations
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create FeedbackType enum (with IF NOT EXISTS for idempotency)
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE feedbacktype AS ENUM (
                'thumbs_up', 'thumbs_down', 'regeneration', 'edit', 'copy', 'abandon'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
    )

    # Create FeedbackSource enum (with IF NOT EXISTS for idempotency)
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE feedbacksource AS ENUM ('explicit', 'implicit');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
    )

    # Create feedback table
    op.create_table(
        "feedback",
        # Primary key
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        # Idempotency
        sa.Column(
            "idempotency_key",
            sa.String(64),
            nullable=False,
            unique=True,
            index=True,
        ),
        # Multi-tenancy
        sa.Column(
            "organization_id",
            UUID(as_uuid=False),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Context
        sa.Column(
            "user_id",
            UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "message_id",
            UUID(as_uuid=False),
            sa.ForeignKey("chat_messages.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "conversation_id",
            UUID(as_uuid=False),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Lineage (required for learning)
        sa.Column("generation_id", sa.String(100), nullable=False, index=True),
        sa.Column("prompt_version_id", sa.String(50), nullable=False, index=True),
        sa.Column("trace_id", sa.String(100), nullable=True),
        # Feedback type - use postgresql.ENUM with create_type=False
        sa.Column(
            "feedback_type",
            sa.dialects.postgresql.ENUM(
                "thumbs_up",
                "thumbs_down",
                "regeneration",
                "edit",
                "copy",
                "abandon",
                name="feedbacktype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.dialects.postgresql.ENUM(
                "explicit",
                "implicit",
                name="feedbacksource",
                create_type=False,
            ),
            nullable=False,
        ),
        # Scoring system
        sa.Column("score_raw", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, default=1.0),
        sa.Column("score_effective", sa.Float(), nullable=False),
        # Metadata
        sa.Column("persona", sa.String(50), nullable=True),
        sa.Column("extra_metadata", JSONB, nullable=True),
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

    # Create composite indexes for common queries
    op.create_index(
        "ix_feedback_org_created",
        "feedback",
        ["organization_id", "created_at"],
    )
    op.create_index(
        "ix_feedback_type_source",
        "feedback",
        ["feedback_type", "source"],
    )

    # Create event_log table for funnel observability
    op.create_table(
        "event_log",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("event_type", sa.String(100), nullable=False, index=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # Correlation IDs
        sa.Column("trace_id", sa.String(100), nullable=True, index=True),
        sa.Column("generation_id", sa.String(100), nullable=True, index=True),
        sa.Column("message_id", sa.String(36), nullable=True),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("organization_id", sa.String(36), nullable=True, index=True),
        # Payload
        sa.Column("payload", JSONB, nullable=True),
    )

    # Create composite index for funnel queries
    op.create_index(
        "ix_event_log_org_type_time",
        "event_log",
        ["organization_id", "event_type", "timestamp"],
    )


def downgrade() -> None:
    # Drop tables
    op.drop_table("event_log")
    op.drop_table("feedback")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS feedbacktype")
    op.execute("DROP TYPE IF EXISTS feedbacksource")
