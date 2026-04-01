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
