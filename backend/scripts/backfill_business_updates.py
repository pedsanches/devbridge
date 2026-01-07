#!/usr/bin/env python3
"""
Management script to backfill business updates for existing activities.

Usage:
    cd backend
    poetry run python scripts/backfill_business_updates.py

This script processes all activities that don't have a business update
and generates one using the AI service.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models import Activity, BusinessUpdate, Repository
from app.schemas import BusinessUpdateCreate, ImpactLevel
from app.services import activity_service
from app.services.ai_service import ai_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def backfill_business_updates(
    organization_id: str | None = None,
    limit: int = 100,
    dry_run: bool = False,
) -> dict:
    """
    Backfill business updates for activities that don't have one.

    Args:
        organization_id: Optional org ID to filter by. If None, processes all.
        limit: Maximum number of activities to process.
        dry_run: If True, don't actually create updates, just log what would be done.

    Returns:
        Dict with counts of processed, failed, and skipped.
    """
    async with async_session_factory() as db:
        # Build query for activities without business updates
        query = (
            select(Activity)
            .outerjoin(BusinessUpdate, BusinessUpdate.activity_id == Activity.id)
            .where(BusinessUpdate.id.is_(None))
            .limit(limit)
        )

        if organization_id:
            query = query.join(Repository).where(Repository.organization_id == organization_id)

        result = await db.execute(query)
        activities = list(result.scalars().all())

        logger.info(f"Found {len(activities)} activities without business updates")

        if not activities:
            return {"processed": 0, "failed": 0, "skipped": 0, "total": 0}

        processed = 0
        failed = 0

        for i, activity in enumerate(activities, 1):
            logger.info(f"[{i}/{len(activities)}] Processing: {activity.title[:60]}...")

            if dry_run:
                logger.info("  [DRY RUN] Would generate business update")
                processed += 1
                continue

            try:
                # Generate business update
                update_data = await ai_service.generate_business_update(
                    {
                        "type": (
                            activity.type.value
                            if hasattr(activity.type, "value")
                            else str(activity.type)
                        ),
                        "title": activity.title,
                        "content": activity.content or "",
                        "labels": activity.labels or [],
                        "files_touched": activity.files_touched or [],
                    }
                )

                # Create update
                update_create = BusinessUpdateCreate(
                    activity_id=activity.id,
                    summary=update_data["summary"],
                    impact_level=ImpactLevel(update_data["impact_level"]),
                    category=update_data.get("category"),
                )
                await activity_service.create_business_update(db, update_create)
                await db.commit()

                logger.info(
                    f"  ✅ Created: {update_data['summary'][:50]}... "
                    f"[{update_data['impact_level']}]"
                )
                processed += 1

            except Exception as e:
                await db.rollback()
                logger.error(f"  ❌ Failed: {e}")
                failed += 1

        return {
            "processed": processed,
            "failed": failed,
            "skipped": 0,
            "total": len(activities),
        }


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Backfill business updates for activities")
    parser.add_argument(
        "--org-id",
        type=str,
        default=None,
        help="Organization ID to process (default: all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum activities to process (default: 100)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't create updates, just show what would be done",
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("DevBridge Business Update Backfill")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    result = await backfill_business_updates(
        organization_id=args.org_id,
        limit=args.limit,
        dry_run=args.dry_run,
    )

    logger.info("=" * 60)
    logger.info("Results:")
    logger.info(f"  Total found:  {result['total']}")
    logger.info(f"  Processed:    {result['processed']}")
    logger.info(f"  Failed:       {result['failed']}")
    logger.info(f"  Skipped:      {result['skipped']}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
