import jwt
import models
from core.security import ALGORITHM, SECRET_KEY
from database import get_db
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# This tells FastAPI that the token is obtained from this endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> models.User:
    """
    Validate the standard JWT token and return the current teacher/user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get('sub')
        scope: str = payload.get('scope')

        # Prevent student upload tokens from being used for general API access (e.g., deleting exams)
        if user_id is None or scope == 'student_upload':
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    # Fetch user from database
    result = await db.execute(select(models.User).where(models.User.id == int(user_id)))
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    return user


async def get_uploader_id(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> int:
    """
    Validates token specifically for media uploads.
    Accepts BOTH standard teacher tokens AND temporary student upload tokens.
    Returns the teacher's ID to attribute the storage ownership correctly.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate upload credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get('sub')
        scope: str = payload.get('scope')

        if user_id is None:
            raise credentials_exception

        # If it's a student upload token, trust the signature and return the teacher's ID directly
        if scope == 'student_upload':
            return int(user_id)

    except InvalidTokenError:
        raise credentials_exception

    # If it's a regular token, verify the user actually exists in the DB
    result = await db.execute(select(models.User).where(models.User.id == int(user_id)))
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    return user.id
