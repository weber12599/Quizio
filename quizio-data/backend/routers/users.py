import models
import schemas
from core.deps import get_current_user
from crud import users as crud_users
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/api/users', tags=['users'])


@router.post(
    '/', response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED
)
async def create_new_user(
    user: schemas.UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Business Rule: Regular teachers MUST provide an email
    if not user.is_superuser and not user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Email is required for regular teachers.',
        )

    # Check if email is already registered
    db_user_email = await crud_users.get_user_by_email(db, email=user.email)
    if db_user_email:
        raise HTTPException(status_code=400, detail='Email already registered')

    # Check if username is already taken
    db_user_username = await crud_users.get_user_by_username(db, username=user.username)
    if db_user_username:
        raise HTTPException(status_code=400, detail='Username already taken')

    # Attempt to create the user
    new_user = await crud_users.create_user(db=db, user=user, current_user=current_user)

    # If CRUD blocked the creation due to lack of superuser privileges
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Only administrators can create new accounts',
        )

    return new_user


@router.get('/me', response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    # Return the currently logged-in user profile
    return current_user
