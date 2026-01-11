"""enhance_teams_for_data_sources

Add description, color, is_default, github_team_slug to teams.
Create team_repositories many-to-many association table.

Revision ID: a1b2c3d4e5f6
Revises: 0ae9c2d22f7c
Create Date: 2026-01-11 17:24:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "c6e7f8g9h0i1"  # add_team_metrics_table
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add new columns to teams table
    op.add_column("teams", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("teams", sa.Column("color", sa.String(length=7), nullable=True))
    op.add_column(
        "teams",
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column("teams", sa.Column("github_team_slug", sa.String(length=100), nullable=True))

    # 2. Create team_repositories many-to-many association table
    op.create_table(
        "team_repositories",
        sa.Column("team_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("repository_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("team_id", "repository_id"),
    )
    op.create_index("ix_team_repositories_team_id", "team_repositories", ["team_id"], unique=False)
    op.create_index(
        "ix_team_repositories_repository_id", "team_repositories", ["repository_id"], unique=False
    )

    # 3. Migrate existing team_id relationships to the many-to-many table
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO team_repositories (team_id, repository_id, added_at)
            SELECT team_id, id, NOW()
            FROM repositories
            WHERE team_id IS NOT NULL
            ON CONFLICT DO NOTHING
            """
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Drop team_repositories table
    op.drop_index("ix_team_repositories_repository_id", table_name="team_repositories")
    op.drop_index("ix_team_repositories_team_id", table_name="team_repositories")
    op.drop_table("team_repositories")

    # 2. Remove new columns from teams
    op.drop_column("teams", "github_team_slug")
    op.drop_column("teams", "is_default")
    op.drop_column("teams", "color")
    op.drop_column("teams", "description")
