"""add_ref_code_sequence

Revision ID: 8c904c0f89b1
Revises: 44f0960ef61c
Create Date: 2026-01-29 01:36:02.531670+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8c904c0f89b1"
down_revision: str | Sequence[str] | None = "44f0960ef61c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE SEQUENCE ref_code_seq START 1")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP SEQUENCE ref_code_seq")
