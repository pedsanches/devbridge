"""Add team_id to reports table.

Revision ID: d1e2f3g4h5i6
Revises: 2026_01_11_1724
Create Date: 2026-01-11 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d1e2f3g4h5i6"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add team_id column to reports table."""
    conn = op.get_bind()

    # Check if column exists
    result = conn.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'reports' AND column_name = 'team_id'"
        )
    )
    column_exists = result.fetchone() is not None

    if not column_exists:
        op.add_column(
            "reports",
            sa.Column(
                "team_id",
                postgresql.UUID(as_uuid=False),
                nullable=True,
            ),
        )

    # Check if FK exists
    result = conn.execute(
        sa.text(
            "SELECT constraint_name FROM information_schema.table_constraints "
            "WHERE table_name = 'reports' AND constraint_name = 'fk_reports_team_id'"
        )
    )
    fk_exists = result.fetchone() is not None

    if not fk_exists:
        op.create_foreign_key(
            "fk_reports_team_id",
            "reports",
            "teams",
            ["team_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # Check if index exists
    result = conn.execute(
        sa.text(
            "SELECT indexname FROM pg_indexes "
            "WHERE tablename = 'reports' AND indexname = 'ix_reports_team_id'"
        )
    )
    index_exists = result.fetchone() is not None

    if not index_exists:
        op.create_index("ix_reports_team_id", "reports", ["team_id"])


def downgrade() -> None:
    """Remove team_id column from reports table."""
    op.drop_constraint("fk_reports_team_id", "reports", type_="foreignkey")
    op.drop_index("ix_reports_team_id", table_name="reports")
    op.drop_column("reports", "team_id")
