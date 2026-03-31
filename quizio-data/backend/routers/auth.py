import os

import crud
import schemas
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/api/auth', tags=['auth'])

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# Define the OAuth2 scheme and point it to the login endpoint
# This is the magic line that enables the "Authorize" button in Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')


@router.post('/login')
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # OAuth2PasswordRequestForm automatically handles the form data from Swagger UI
    if form_data.username == ADMIN_USERNAME and form_data.password == ADMIN_PASSWORD:
        return {'access_token': 'fake_jwt_token', 'token_type': 'bearer'}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Incorrect username or password',
        headers={'WWW-Authenticate': 'Bearer'},
    )


@router.post('/student')
async def verify_student(
    student_data: schemas.StudentLogin, db: AsyncSession = Depends(get_db)
):
    student = await crud.get_student_by_student_id(db, student_data.student_id)
    if not student or student.password != student_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid student ID or password',
        )
    return {
        'name': student.name,
        'student_id': student.student_id,
        'class_name': student.class_name,
    }
