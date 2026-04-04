import os

import httpx
import models
from core.deps import get_current_user
from database import get_db
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/api/media', tags=['media'])

# Fetch the internal storage URL from environment variables
SEAWEEDFS_MASTER_URL = os.getenv('SEAWEEDFS_MASTER_URL')

# Fail fast to prevent silent connection errors
if not SEAWEEDFS_MASTER_URL:
    raise ValueError(
        'Critical Error: SEAWEEDFS_MASTER_URL environment variable is not set!'
    )


@router.post('/upload', status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Only authenticated users can reach this point
    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Request an FID and volume location from the Master server
            assign_resp = await client.get(f'{SEAWEEDFS_MASTER_URL}/dir/assign')
            assign_resp.raise_for_status()
            assign_data = assign_resp.json()

            fid = assign_data.get('fid')
            volume_url = assign_data.get('url')

            # Step 2: Forward the uploaded file to the assigned Volume server
            upload_target = f'http://{volume_url}/{fid}'

            file_content = await file.read()
            files = {'file': (file.filename, file_content, file.content_type)}

            upload_resp = await client.post(upload_target, files=files)
            upload_resp.raise_for_status()
            upload_data = upload_resp.json()

            # Step 3: Record the uploaded media in the database for GC tracking
            new_media = models.Media(fid=fid, uploader_id=current_user.id)
            db.add(new_media)
            await db.commit()

            # Step 4: Return metadata
            return {
                'fid': fid,
                'filename': file.filename,
                'content_type': file.content_type,
                'size': upload_data.get('size'),
                'url': f'/{fid}',
            }

        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f'Storage error: {str(e)}')
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=500,
                detail=f'Storage returned error: {e.response.status_code}',
            )


@router.delete('/{fid}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    fid: str,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Step 1: Verify the media exists in the database
    result = await db.execute(select(models.Media).where(models.Media.fid == fid))
    media_record = result.scalar_one_or_none()

    if not media_record:
        raise HTTPException(status_code=404, detail='Media not found in database')

    # Step 2: Check authorization (only the uploader can delete their media manually)
    if media_record.uploader_id != current_user.id:
        raise HTTPException(
            status_code=403, detail='Not authorized to delete this media'
        )

    async with httpx.AsyncClient() as client:
        try:
            # Step 3: Query SeaweedFS Master to find the exact volume for this FID
            volume_id = fid.split(',')[0]
            lookup_resp = await client.get(
                f'{SEAWEEDFS_MASTER_URL}/dir/lookup?volumeId={volume_id}'
            )
            lookup_resp.raise_for_status()
            lookup_data = lookup_resp.json()

            if not lookup_data.get('locations'):
                raise HTTPException(
                    status_code=404, detail='Volume location not found in SeaweedFS'
                )

            # Use the first available volume URL
            volume_url = lookup_data['locations'][0].get('publicUrl') or lookup_data[
                'locations'
            ][0].get('url')

            # Step 4: Send DELETE request to the Volume server
            delete_target = f'http://{volume_url}/{fid}'
            delete_resp = await client.delete(delete_target)
            delete_resp.raise_for_status()

            # Step 5: Remove the tracking record from the database
            await db.delete(media_record)
            await db.commit()

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500, detail=f'Storage connection error: {str(e)}'
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=500,
                detail=f'Storage returned error: {e.response.status_code}',
            )
