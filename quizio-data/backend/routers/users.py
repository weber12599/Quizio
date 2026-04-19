from typing import List

import models
import schemas
from core.deps import get_current_user
from crud import users as crud_users
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/api/users', tags=['users'])


# ==========================================
# Dependencies
# ==========================================


async def get_user_r(
    user_db_id: int,
    db: AsyncSession = Depends(get_db),
) -> models.User:
    db_user = await crud_users.get_user(db, user_db_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Teacher not found'
        )
    return db_user


async def get_user_rwd(
    db_user: models.User = Depends(get_user_r),
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    # Business rule: Users can only modify their own account, unless they are a superuser
    if not current_user.is_superuser and db_user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Not authorized to update this teacher',
        )
    return db_user


@router.get('/', response_model=List[schemas.UserResponse])
async def read_users(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        return await crud_users.get_users(db, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get('/me', response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    # Return the currently logged-in user profile
    return current_user


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

    try:
        return await crud_users.create_user(db=db, user=user, current_user=current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except IntegrityError:
        await db.rollback()
        msg_slices = []
        if await crud_users.check_email_exists(db, user.email):
            msg_slices.append(f'Email {user.email} exists')
        if await crud_users.check_username_exists(db, user.username):
            msg_slices.append(f'Username {user.username} exists')
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=' & '.join(msg_slices),
        )


@router.put('/{user_db_id}', response_model=schemas.UserResponse)
async def update_existing_user(
    user_in: schemas.UserUpdate,
    db_user: models.User = Depends(get_user_rwd),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        updated_user = await crud_users.update_user(db, db_user, user_in, current_user)
        return updated_user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==========================================
# Lifecycle Management Endpoints
# ==========================================


@router.post('/{user_db_id}/restore', response_model=schemas.UserResponse)
async def restore_deleted_user(
    db_user: models.User = Depends(get_user_rwd),
    db: AsyncSession = Depends(get_db),
):
    return await crud_users.toggle_delete_user(db, db_user, False)


@router.delete('/{user_db_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_user(
    db_user: models.User = Depends(get_user_rwd),
    db: AsyncSession = Depends(get_db),
):
    await crud_users.toggle_delete_user(db, db_user, True)
