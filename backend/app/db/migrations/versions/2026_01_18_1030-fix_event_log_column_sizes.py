"""Fix event_log column sizes for message_id with suffixes.

Revision ID: f33db4ck0003
Revises: f33db4ck0002
Create Date: 2026-01-18 10:30:00.000000

The message_id in event_log was defined as VARCHAR(36) for UUID format,
but the frontend sends message IDs with suffixes like "-assistant"
(e.g., "9d056fe6-bed1-4949-a16f-7d45426eefd3-assistant" = 45 chars).

This migration extends the column to VARCHAR(100) to accommodate these IDs.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f33db4ck0003"
down_revision = "f33db4ck0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend message_id from VARCHAR(36) to VARCHAR(100)
    # to accommodate UUIDs with suffixes like "-assistant"
    op.alter_column(
        "event_log",
        "message_id",
        type_=sa.String(100),
        existing_type=sa.String(36),
        existing_nullable=True,
    )


def downgrade() -> None:
    # Revert to VARCHAR(36) - may cause data truncation if longer values exist
    op.alter_column(
        "event_log",
        "message_id",
        type_=sa.String(36),
        existing_type=sa.String(100),
        existing_nullable=True,
    )
