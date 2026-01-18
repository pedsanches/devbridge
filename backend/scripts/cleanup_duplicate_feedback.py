#!/usr/bin/env python3
"""
Cleanup Duplicate Feedback Records.

This script cleans up duplicate feedback records that may exist from before
the idempotency key change. It keeps only the most recent feedback per
user+message combination.

Usage:
    # Dry run (default)
    uv run python scripts/cleanup_duplicate_feedback.py

    # Actually delete duplicates
    uv run python scripts/cleanup_duplicate_feedback.py --commit
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.models.feedback import Feedback

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def find_duplicates(session: AsyncSession) -> list[tuple[str, str, int]]:
    """Find user+message combinations with multiple feedback records."""
    result = await session.execute(
        select(
            Feedback.user_id,
            Feedback.message_id,
            func.count(Feedback.id).label("count"),
        )
        .group_by(Feedback.user_id, Feedback.message_id)
        .having(func.count(Feedback.id) > 1)
    )
    return list(result.all())


async def cleanup_duplicates(session: AsyncSession, commit: bool = False) -> int:
    """Remove duplicate feedback records, keeping only the most recent per user+message."""
    duplicates = await find_duplicates(session)

    if not duplicates:
        logger.info("No duplicate feedback records found.")
        return 0

    logger.info(f"Found {len(duplicates)} user+message combinations with duplicates")

    total_deleted = 0

    for user_id, message_id, _count in duplicates:
        # Get all feedback for this user+message, ordered by created_at desc
        result = await session.execute(
            select(Feedback)
            .where(
                Feedback.user_id == user_id,
                Feedback.message_id == message_id,
            )
            .order_by(Feedback.created_at.desc())
        )
        all_feedback = list(result.scalars().all())

        # Keep the first (most recent), delete the rest
        to_delete = all_feedback[1:]
        for fb in to_delete:
            logger.info(
                f"{'Deleting' if commit else 'Would delete'} feedback: "
                f"id={fb.id}, type={fb.feedback_type.value}, "
                f"created_at={fb.created_at}"
            )
            if commit:
                await session.delete(fb)
            total_deleted += 1

    if commit:
        await session.commit()
        logger.info(f"Deleted {total_deleted} duplicate feedback records")
    else:
        logger.info(f"Would delete {total_deleted} feedback records (dry run)")

    return total_deleted


async def main():
    parser = argparse.ArgumentParser(description="Cleanup duplicate feedback records")
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually delete duplicates (default is dry run)",
    )
    args = parser.parse_args()

    async with async_session_factory() as session:
        deleted = await cleanup_duplicates(session, commit=args.commit)

    if not args.commit and deleted > 0:
        logger.info("Run with --commit to actually delete the duplicates")


if __name__ == "__main__":
    asyncio.run(main())
