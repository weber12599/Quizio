import uuid

import models
import schemas
from core.deps import get_current_user
from core.security import (
    create_access_token,
    create_guest_upload_token,
    create_student_upload_token,
    verify_password,
)
from crud import students as crud_students
from crud import users as crud_users
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/api/auth', tags=['auth'])


@router.post('/login')
async def login_teacher(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    # Fetch user from the database
    user = await crud_users.get_user_by_username(db, username=form_data.username)

    # Check if user exists and verify password
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    # Generate a JWT token containing the user ID
    access_token = create_access_token(data={'sub': str(user.id)})

    return {'access_token': access_token, 'token_type': 'bearer'}


@router.post('/student')
async def verify_student(
    student_data: schemas.StudentLogin,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Leverage the CRUD function we already built!
    # This automatically ensures the student belongs to the current_user (the teacher hosting the game)
    student = await crud_students.get_student_by_student_id(
        db=db, student_id=student_data.student_id, current_user=current_user
    )

    # Check if student exists (and belongs to the teacher) and passwords match
    if not student or student.password != student_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid student ID or password',
        )

    # Retrieve upload token
    upload_token = create_student_upload_token(
        teacher_id=current_user.id, student_id=student.student_id
    )

    return {
        'id': student.id,
        'name': student.name,
        'student_id': student.student_id,
        'class_name': student.class_name,
        'upload_token': upload_token,
    }


@router.post('/guest')
async def verify_guest(
    guest_data: schemas.GuestLogin,
    current_user: models.User = Depends(get_current_user),
):
    # Generate random guest id
    guest_id = str(uuid.uuid4())

    # Retrieve upload token
    upload_token = create_guest_upload_token(
        teacher_id=current_user.id, guest_id=guest_id, guest_name=guest_data.guest_name
    )

    return {
        'guest_name': guest_data.guest_name,
        'guest_id': guest_id,
        'upload_token': upload_token,
    }
