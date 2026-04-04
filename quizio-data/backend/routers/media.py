import httpx
import models
from core.deps import get_current_user
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

router = APIRouter(prefix='/api/media', tags=['media'])

# Fetch the internal storage URL from environment variables
SEAWEEDFS_MASTER_URL = 'http://seaweedfs-master:9333'

# Fail fast to prevent silent connection errors
if not SEAWEEDFS_MASTER_URL:
    raise ValueError(
        'Critical Error: SEAWEEDFS_MASTER_URL environment variable is not set!'
    )


@router.post('/upload', status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
):
    # Only authenticated users (teachers/admins) can reach this point
    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Request an FID and volume location from the Master server
            assign_resp = await client.get(f'{SEAWEEDFS_MASTER_URL}/dir/assign')
            assign_resp.raise_for_status()
            assign_data = assign_resp.json()

            fid = assign_data.get('fid')
            # SeaweedFS returns the volume URL (e.g., "seaweedfs-volume:8081")
            volume_url = assign_data.get('url')

            # Step 2: Forward the uploaded file to the assigned Volume server
            upload_target = f'http://{volume_url}/{fid}'

            # Read the file content into memory and prepare for upload
            file_content = await file.read()
            files = {'file': (file.filename, file_content, file.content_type)}

            upload_resp = await client.post(upload_target, files=files)
            upload_resp.raise_for_status()
            upload_data = upload_resp.json()

            # Step 3: Return the file metadata and FID back to the frontend
            return {
                'fid': fid,
                'filename': file.filename,
                'content_type': file.content_type,
                'size': upload_data.get('size'),
                # Provide a convenient URL path that points to our Nginx proxy
                'url': f'/{fid}',
            }

        except httpx.RequestError as e:
            # Handle network errors when communicating with SeaweedFS
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Failed to communicate with storage server: {str(e)}',
            )
        except httpx.HTTPStatusError as e:
            # Handle HTTP errors returned by SeaweedFS
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Storage server returned an error: {e.response.status_code}',
            )
