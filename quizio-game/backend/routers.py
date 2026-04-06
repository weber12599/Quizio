import os

import httpx
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from utils import check_student_credentials

DATA_SERVICE_BASE_URL = os.getenv('DATA_SERVICE_BASE_URL')
DATA_SERVICE_TEACHER_AUTH_URL = f'{DATA_SERVICE_BASE_URL}/api/auth/login'

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')


class StudentLoginParams(BaseModel):
    student_id: str
    password: str
    token: str


@router.post('/api/auth/login')
async def proxy_auth_teacher(form_data: OAuth2PasswordRequestForm = Depends()):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                DATA_SERVICE_TEACHER_AUTH_URL,
                data={'username': form_data.username, 'password': form_data.password},
                timeout=5.0,
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Incorrect username or password',
                )
            return response.json()
        except httpx.RequestError as e:
            print(f'Login proxy error: {e}')
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail='Data service is unavailable',
            )


@router.post('/api/auth/student')
async def proxy_auth_student(params: StudentLoginParams):
    student_info = await check_student_credentials(
        params.student_id, params.password, params.token
    )
    if not student_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Student verification failed',
        )
    return student_info


@router.get('/api/exams/')
async def proxy_get_my_exams(token: str = Depends(oauth2_scheme)):
    auth_header = f'Bearer {token}'
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'{DATA_SERVICE_BASE_URL}/api/exams/',
            headers={'Authorization': auth_header},
            timeout=5.0,
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


@router.get('/api/exams/{exam_id}')
async def proxy_get_exam_details(exam_id: int, token: str = Depends(oauth2_scheme)):
    auth_header = f'Bearer {token}'
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'{DATA_SERVICE_BASE_URL}/api/exams/{exam_id}',
            headers={'Authorization': auth_header},
            timeout=5.0,
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


@router.post('/api/media/upload')
async def proxy_upload_media(
    file: UploadFile = File(...),
    authorization: str = Header(None),
):
    """
    Proxy media upload to the Data Backend.
    Both Host (Teacher) and Client (Student) will upload through this game-backend endpoint.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing authorization header',
        )

    headers = {'Authorization': authorization}

    async with httpx.AsyncClient() as client:
        try:
            file_content = await file.read()
            files = {'file': (file.filename, file_content, file.content_type)}

            response = await client.post(
                f'{DATA_SERVICE_BASE_URL}/api/media/upload',
                headers=headers,
                files=files,
                timeout=30.0,
            )

            if response.status_code not in (200, 201):
                raise HTTPException(
                    status_code=response.status_code, detail=response.text
                )

            return response.json()

        except httpx.RequestError as e:
            print(f'Upload proxy error: {e}')
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail='Data service is unavailable for upload',
            )
