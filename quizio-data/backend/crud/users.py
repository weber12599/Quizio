import models
import schemas
from core.security import get_password_hash
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


# Get a single user by ID (primary key)
async def get_user(db: AsyncSession, user_db_id: int):
    result = await db.execute(select(models.User).where(models.User.id == user_db_id))
    return result.scalar_one_or_none()


# Check if email exists in the database (including soft-deleted records)
async def check_email_exists(db: AsyncSession, email: str) -> bool:
    query = select(models.User).where(models.User.email == email)
    result = await db.execute(query)
    return result.scalars().first() is not None


# Check if username exists in the database (including soft-deleted records)
async def check_username_exists(db: AsyncSession, username: str) -> bool:
    query = select(models.User).where(models.User.username == username)
    result = await db.execute(query)
    return result.scalars().first() is not None


# Get a single user by username (Used internally for login/validation, no auth needed here)
async def get_user_by_username(db: AsyncSession, username: str):
    # Prevent soft-deleted users from logging in or being looked up
    query = select(models.User).where(
        models.User.username == username, models.User.deleted_at.is_(None)
    )

    result = await db.execute(query)
    return result.scalars().first()


async def get_users(db: AsyncSession, current_user: models.User):
    if not current_user.is_superuser:
        raise ValueError('Not authorized as a super user')

    result = await db.execute(select(models.User))
    return result.scalars().all()


# Create a new user (Strictly restricted to Superusers)
async def create_user(
    db: AsyncSession, user: schemas.UserCreate, current_user: models.User
):
    # Security check: Only superusers can create new teacher or admin accounts
    if not current_user.is_superuser:
        raise ValueError('Only administrators can create new accounts')

    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_superuser=user.is_superuser,
    )
    db.add(db_user)
    await db.flush()  # Flush to get the generated user ID

    await db.commit()
    return await get_user(db, db_user.id)


# Update an existing user (Strictly restricted to Superusers)
async def update_user(
    db: AsyncSession,
    db_user: models.User,
    user_update: schemas.UserUpdate,
    current_user: models.User,
):
    # Core defense: Once deleted, a user cannot be modified
    if db_user.deleted_at is not None:
        raise ValueError('Cannot modify a protected user.')

    # Security check: Only the self or a superuser can modify the user
    if not current_user.is_superuser and db_user.id != current_user.id:
        raise ValueError('Not authorized to update this user')

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
    return await get_user(db, db_user.id)


# Soft delete a user
async def toggle_delete_user(db: AsyncSession, db_user: models.User, is_deleted: bool):
    current_is_deleted = db_user.deleted_at is not None
    if not (current_is_deleted ^ is_deleted):
        return db_user

    db_user.deleted_at = func.now() if is_deleted else None
    await db.commit()
    return db_user
