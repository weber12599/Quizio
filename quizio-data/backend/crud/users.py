import models
import schemas
from core.security import get_password_hash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


# Get user by email (Used internally for login/validation, no auth needed here)
async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(models.User).where(models.User.email == email))
    return result.scalars().first()


# Get user by username (Used internally for login/validation, no auth needed here)
async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(
        select(models.User).where(models.User.username == username)
    )
    return result.scalars().first()


# Get user by id (Used internally for login/validation, no auth needed here)
async def get_user_by_user_id(
    db: AsyncSession, user_id: str, current_user: models.User
):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    return result.scalar_one_or_none()


# Create a new user (Strictly restricted to Superusers)
async def create_user(
    db: AsyncSession, user: schemas.UserCreate, current_user: models.User
):
    # Security check: Only superusers can create new teacher or admin accounts
    if not current_user.is_superuser:
        return None

    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        # Allow superuser to define if the new user is also a superuser
        is_superuser=user.is_superuser,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_users(db: AsyncSession, current_user: models.User):
    if not current_user.is_superuser:
        return None

    result = await db.execute(select(models.User))
    return result.scalars().all()


async def update_user(
    db: AsyncSession,
    db_user: models.User,
    user_update: schemas.UserUpdate,
    current_user: models.User,
):
    # Security check: Only the self or a superuser can modify the user
    if not current_user.is_superuser and db_user.id != current_user.id:
        return None

    # exclude_unset=True automatically filters out fields that were not explicitly provided
    update_data = user_update.model_dump(exclude_unset=True)

    # Apply updates without repetitive if-statements
    for key, value in update_data.items():
        if key == 'password':
            # Prevent empty password updates
            if key == 'password' and not value:
                continue
            db_user.hashed_password = get_password_hash(value)
        else:
            setattr(db_user, key, value)

    await db.commit()
    await db.refresh(db_user)
    return db_user
