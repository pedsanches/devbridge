"""Remove message_id foreign key constraint from feedback table.

Revision ID: f33db4ck0004
Revises: f33db4ck0003
Create Date: 2026-01-18 10:36:00.000000

The frontend generates message IDs with suffixes like "-assistant" (e.g.,
"9d056fe6-bed1-4949-a16f-7d45426eefd3-assistant") which don't exist in
the chat_messages table. This migration removes the FK constraint to
allow storing these frontend-generated IDs.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f33db4ck0004"
down_revision = "f33db4ck0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the foreign key constraint on message_id
    op.drop_constraint("feedback_message_id_fkey", "feedback", type_="foreignkey")

    # Alter column to be a regular String(100) without FK
    op.alter_column(
        "feedback",
        "message_id",
        type_=sa.String(100),
        existing_type=sa.dialects.postgresql.UUID(),
        existing_nullable=False,
    )


def downgrade() -> None:
    # Note: This downgrade may fail if there are message_ids with suffixes
    # that don't exist in chat_messages
    op.alter_column(
        "feedback",
        "message_id",
        type_=sa.dialects.postgresql.UUID(as_uuid=False),
        existing_type=sa.String(100),
        existing_nullable=False,
    )

    op.create_foreign_key(
        "feedback_message_id_fkey",
        "feedback",
        "chat_messages",
        ["message_id"],
        ["id"],
        ondelete="CASCADE",
    )
