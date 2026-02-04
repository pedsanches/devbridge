from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.public_reference import PublicReference


class ReferenceService:
    """Service for managing public references (Smart References)."""

    async def get_or_create_references(
        self,
        db: AsyncSession,
        team_id: UUID,
        team_slug: str,
        activities: list[dict[str, Any]],
    ) -> dict[UUID, str]:
        """
        Get or create persistent R# codes for a list of activities.

        Args:
            db: Database session.
            team_id: Team ID context.
            team_slug: Team slug for code generation (e.g. BACKEND).
            activities: List of activity dicts.

        Returns:
            Dictionary mapping activity_id -> ref_code (e.g. R-BACKEND-00123).
        """
        if not activities:
            return {}

        activity_ids = [act["id"] for act in activities]

        # 1. Fetch existing references
        query = select(PublicReference).where(
            PublicReference.team_id == str(team_id),
            PublicReference.entity_type == "activity",
            PublicReference.entity_id.in_(activity_ids),
        )
        result = await db.execute(query)
        existing_refs = result.scalars().all()

        ref_map = {UUID(ref.entity_id): ref.code for ref in existing_refs}

        # 2. Identify missing
        missing_ids = [aid for aid in activity_ids if aid not in ref_map]

        if not missing_ids:
            return ref_map

        # 3. Create missing references
        # We process sequentially to ensure order, or batch insert?
        # Batch insert is tricky with "nextval" in Python, but we can do it in SQL.
        # We'll stick to a loop for clarity and sequence safety, or a complex INSERT/RETURNING.
        # Given "anti-race" requirement, let's use the sequence inside the INSERT.

        # We need to map back which ID got which Code.
        # We need to map back which ID got which Code.

        # Optimize: Get a batch of sequence numbers?
        # Or just loop. For context window (20-50 items), looping is acceptable overhead
        # compared to LLM latency.

        slug_prefix = team_slug.upper()

        for aid in missing_ids:
            # Generate code using sequence
            # Safe way: INSERT ... RETURNING code
            # We construct the code in SQL: 'R-' || :slug || '-' || to_char(nextval('ref_code_seq'), 'FM000000')

            external_url = None  # Could construct from repo url + external_id if available

            stmt = text("""
                INSERT INTO public_references (
                    code, team_id, entity_type, entity_id, external_url
                )
                VALUES (
                    'R-' || :slug || '-' || to_char(nextval('ref_code_seq'), 'FM000000'),
                    :team_id, 'activity', :entity_id, :external_url
                )
                ON CONFLICT (team_id, entity_type, entity_id) DO UPDATE SET
                    updated_at = NOW()
                RETURNING code
            """)

            res = await db.execute(
                stmt,
                {
                    "slug": slug_prefix,
                    "team_id": str(team_id),
                    "entity_id": str(aid),
                    "external_url": external_url,
                },
            )
            code = res.scalar()
            if code:
                ref_map[aid] = code

        await db.flush()
        return ref_map


reference_service = ReferenceService()
