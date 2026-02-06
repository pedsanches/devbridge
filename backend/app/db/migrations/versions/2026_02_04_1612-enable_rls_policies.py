"""Enable Row Level Security for multi-tenant isolation

Revision ID: 2026_02_04_1612
Revises: 2026_02_04_1558
Create Date: 2026-02-04 16:12:00.000000

This migration implements defense-in-depth security:
1. Enables RLS on multi-tenant tables
2. Creates policies that filter rows by organization_id
3. Uses session variable 'app.current_org_id' for tenant identification
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026_02_04_1612"
down_revision = "072e2f4beb3e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tables that have organization_id column
    direct_tables = [
        "conversations",
        "repositories",
        "activities",  # Wait, checking logic below
        "memberships",
        "teams",
        "pending_invitations",
    ]
    # Actually activities does NOT have org_id, moving to special handling
    direct_tables = [
        "conversations",
        "repositories",
        "memberships",
        "teams",
        "pending_invitations",
    ]

    # 1. Apply Direct Policies
    for table in direct_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")

        # Policy: Standard check on organization_id
        policy_condition = (
            "organization_id::text = COALESCE(current_setting('app.current_org_id', true), '')"
        )

        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation_select ON {table}
            FOR SELECT USING ({policy_condition});
        """)
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation_insert ON {table}
            FOR INSERT WITH CHECK ({policy_condition});
        """)
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation_update ON {table}
            FOR UPDATE USING ({policy_condition});
        """)
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation_delete ON {table}
            FOR DELETE USING ({policy_condition});
        """)

        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

    # 2. Apply Policy for Chat Messages (via conversations)
    # Note: INSERTs/UPDATEs might need more complex checks, but for now we secure SELECTs strongly.
    # For INSERTs, we assume the application logic enforces the link to a valid conversation.
    table = "chat_messages"
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")

    # Subquery condition
    join_condition = """
        conversation_id IN (
            SELECT id FROM conversations
            WHERE organization_id::text = COALESCE(current_setting('app.current_org_id', true), '')
        )
    """

    op.execute(
        f"CREATE POLICY {table}_tenant_select ON {table} FOR SELECT USING ({join_condition});"
    )
    op.execute(
        f"CREATE POLICY {table}_tenant_update ON {table} FOR UPDATE USING ({join_condition});"
    )
    op.execute(
        f"CREATE POLICY {table}_tenant_delete ON {table} FOR DELETE USING ({join_condition});"
    )
    # Insert check is tricky without denormalization, often skipped or checked via parent
    op.execute(
        f"CREATE POLICY {table}_tenant_insert ON {table} FOR INSERT WITH CHECK ({join_condition});"
    )

    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

    # 3. Apply Policy for Activities (via repositories)
    table = "activities"
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")

    join_condition = """
        repository_id IN (
            SELECT id FROM repositories
            WHERE organization_id::text = COALESCE(current_setting('app.current_org_id', true), '')
        )
    """

    op.execute(
        f"CREATE POLICY {table}_tenant_select ON {table} FOR SELECT USING ({join_condition});"
    )
    op.execute(
        f"CREATE POLICY {table}_tenant_update ON {table} FOR UPDATE USING ({join_condition});"
    )
    op.execute(
        f"CREATE POLICY {table}_tenant_delete ON {table} FOR DELETE USING ({join_condition});"
    )
    op.execute(
        f"CREATE POLICY {table}_tenant_insert ON {table} FOR INSERT WITH CHECK ({join_condition});"
    )

    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")


def downgrade() -> None:
    tables = [
        "conversations",
        "repositories",
        "memberships",
        "teams",
        "pending_invitations",
        "chat_messages",
        "activities",
    ]

    for table in tables:
        # Drop policies (names might vary, so using distinct DROP statements)
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_select ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_insert ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_update ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_delete ON {table};")

        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_select ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_insert ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_update ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_delete ON {table};")

        # Disable RLS
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
