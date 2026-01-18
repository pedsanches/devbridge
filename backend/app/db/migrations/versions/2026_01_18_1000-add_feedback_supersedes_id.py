"""Add supersedes_id to feedback for append-only history.

Revision ID: f33db4ck0002
Revises: f33db4ck0001
Create Date: 2026-01-18 10:00:00.000000

Changes:
- Add supersedes_id column (FK to feedback.id) for vote change tracking
- Remove unique constraint on idempotency_key (allow multiple feedbacks per user+message)
- Add composite index for user+message queries to find latest feedback

Reference: ADR-011 Feedback Schema Design (updated for append-only model)
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "f33db4ck0002"
down_revision = "f33db4ck0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add supersedes_id column for tracking vote changes
    op.add_column(
        "feedback",
        sa.Column(
            "supersedes_id",
            UUID(as_uuid=False),
            sa.ForeignKey("feedback.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Add index for supersedes_id lookups
    op.create_index(
        "ix_feedback_supersedes_id",
        "feedback",
        ["supersedes_id"],
    )

    # Add composite index for finding latest feedback per user+message
    op.create_index(
        "ix_feedback_user_message_created",
        "feedback",
        ["user_id", "message_id", "created_at"],
    )

    # Drop unique index on idempotency_key to allow append-only model
    # The idempotency_key was created with unique=True in create_table, which creates
    # a unique index named "ix_feedback_idempotency_key", not a constraint.
    # We recreate it as a non-unique index.
    op.drop_index("ix_feedback_idempotency_key", table_name="feedback")
    op.create_index(
        "ix_feedback_idempotency_key",
        "feedback",
        ["idempotency_key"],
    )


def downgrade() -> None:
    # Restore unique constraint on idempotency_key
    op.drop_index("ix_feedback_idempotency_key", table_name="feedback")
    op.create_index(
        "ix_feedback_idempotency_key",
        "feedback",
        ["idempotency_key"],
        unique=True,
    )

    # Drop composite index
    op.drop_index("ix_feedback_user_message_created", table_name="feedback")

    # Drop supersedes_id index and column
    op.drop_index("ix_feedback_supersedes_id", table_name="feedback")
    op.drop_column("feedback", "supersedes_id")
