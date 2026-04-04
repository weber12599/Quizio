import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone

import httpx
import models
from database import AsyncSessionLocal
from sqlalchemy import String, cast, or_, select

# Configure basic logger for the background task
# Ensure the level is set to INFO so we can see the GC logs in the console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEAWEEDFS_MASTER_URL = os.getenv('SEAWEEDFS_MASTER_URL')


async def _delete_seaweedfs_file(client: httpx.AsyncClient, fid: str) -> bool:
    """Helper function to find and physically delete a file from SeaweedFS."""
    try:
        volume_id = fid.split(',')[0]
        lookup_resp = await client.get(
            f'{SEAWEEDFS_MASTER_URL}/dir/lookup?volumeId={volume_id}'
        )

        if lookup_resp.status_code != 200:
            return False

        lookup_data = lookup_resp.json()
        if not lookup_data.get('locations'):
            return False

        volume_url = lookup_data['locations'][0].get('publicUrl') or lookup_data[
            'locations'
        ][0].get('url')
        delete_target = f'http://{volume_url}/{fid}'

        delete_resp = await client.delete(delete_target)
        return delete_resp.status_code in (200, 202, 204)
    except Exception as e:
        logger.error(f'[GC] Failed to delete {fid} from SeaweedFS: {str(e)}')
        return False


async def media_garbage_collection_task():
    """
    Background infinite loop task for garbage collection.
    Scans and deletes media older than 24 hours that are not referenced in any questions.
    """
    logger.info('[GC] Media garbage collection background task initialized.')

    # Run infinitely while the FastAPI application is alive
    while True:
        try:
            logger.info('[GC] Starting daily media garbage collection cycle...')

            # Set the threshold to 24 hours ago
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

            async with AsyncSessionLocal() as db:
                # Fetch candidates for deletion
                result = await db.execute(
                    select(models.Media).where(models.Media.created_at < cutoff)
                )
                candidates = result.scalars().all()

                logger.info(
                    f'[GC] Found {len(candidates)} media items older than 24 hours.'
                )

                if candidates:
                    deleted_count = 0
                    async with httpx.AsyncClient() as client:
                        for media in candidates:
                            # Check if fid is referenced in question content or options
                            # Cast options array to String to perform a LIKE search safely
                            check_query = (
                                select(models.Question.id)
                                .where(
                                    or_(
                                        models.Question.content.like(f'%{media.fid}%'),
                                        cast(models.Question.options, String).like(
                                            f'%{media.fid}%'
                                        ),
                                    )
                                )
                                .limit(1)
                            )

                            is_used = (
                                await db.execute(check_query)
                            ).scalar_one_or_none()

                            if not is_used:
                                logger.info(
                                    f'[GC] Deleting unused orphaned media: {media.fid}'
                                )
                                success = await _delete_seaweedfs_file(
                                    client, media.fid
                                )

                                if success:
                                    # Delete from DB tracking
                                    await db.delete(media)
                                    await db.commit()
                                    deleted_count += 1
                                else:
                                    logger.warning(
                                        f'[GC] Failed to delete {media.fid} from storage, skipping DB removal.'
                                    )

                    logger.info(
                        f'[GC] Cycle completed. Successfully deleted {deleted_count} orphaned files.'
                    )
                else:
                    logger.info('[GC] Cycle completed. No orphaned files to delete.')

        except Exception as e:
            logger.error(f'[GC] Error in background task cycle: {str(e)}')

        # Sleep for 24 hours (86400 seconds) before the next run
        logger.info('[GC] Going to sleep for 24 hours...')
        await asyncio.sleep(86400)
