"""add_custom_value_to_reporttype

Revision ID: ca8e14e85644
Revises: b8cd4e5f6g7h
Create Date: 2026-01-06 21:16:57.308907+00:00

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ca8e14e85644"
down_revision: str | Sequence[str] | None = "b8cd4e5f6g7h"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE reporttype ADD VALUE 'CUSTOM'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
